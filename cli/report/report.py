#
# Copyright (C) 2023 Red Hat, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import fnmatch
import json
import logging
import os
from datetime import datetime
from typing import Any
from typing import Optional

import junitparser
from google.cloud import storage

from cli.objects.configuration import Configuration
from cli.objects.jira_base import Jira


class Report:
    def __init__(
        self,
        job_name: str,
        job_name_safe: str,
        build_id: str,
        gcs_bucket: str,
        firewatch_config: Configuration,
        jira: Jira,
        fail_with_test_failures: bool,
    ) -> None:
        """
        Constructs the Report object, which will analyze failures in a Prow job and report those failures to Jira based
        on a firewatch config.

        :param job_name: The full name of a Prow job. The value of $JOB_NAME
        :param job_name_safe: The safe name of a test in a Prow job. The value of $JOB_NAME_SAFE
        :param build_id: The build ID that needs to be reported. The value of $BUILD_ID
        :param gcs_bucket: The bucket that Prow job logs are stored
        :param firewatch_config: A firewatch Configuration object
        :param jira: A Jira object used to interact with the Jira server
        :param fail_with_test_failures: A boolean value. If a test failure is found, after bugs are filed, firewatch will exit with a non-zero exit code
        """
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(
            __name__,
        )

        # Set variables
        self.job_name = job_name or os.getenv("JOB_NAME")  # type: ignore
        self.job_name_safe = job_name_safe or os.getenv("JOB_NAME_SAFE")
        self.build_id = build_id or os.getenv("BUILD_ID")
        self.gcs_bucket = gcs_bucket
        self.firewatch_config = firewatch_config
        self.jira = jira
        self.fail_with_test_failures = fail_with_test_failures

        # Log job information
        self.logger.info(f"JOB NAME: {self.job_name}")
        self.logger.info(f"BUILD ID: {self.build_id}")

        # Determine if the job is a rehearsal
        if self.is_rehearsal():
            exit(0)

        # Connect to GCS bucket
        self.storage_client = storage.Client.create_anonymous_client()
        self.bucket = self.storage_client.bucket(gcs_bucket)

        # Define the download path
        self.download_path = f"/tmp/{self.build_id}"
        if not os.path.exists(self.download_path):
            os.mkdir(self.download_path)

        # Find failures
        self.steps: list[str] = []
        self.logs_dir = self.download_logs()
        self.junit_dir = self.download_junit()
        self.failures = self.find_failures()

        # If failures exist
        if len(self.failures) > 0:
            self.bugs_filed = self.file_jira_issues()
            if len(self.bugs_filed) > 1:
                self.relate_issues(self.bugs_filed)
            if self.fail_with_test_failures and self.has_test_failures():
                self.logger.info(
                    "Test failures found and --fail_with_test_failures flag is set. Exiting with exit code 1",
                )
                exit(1)
        else:
            self.logger.info(
                f"No failures for {self.job_name} #{self.build_id} were found!",
            )

    def download_logs(self) -> str:
        """
        Used to download the finished.json and build-log.txt files from each step in a Prow job.

        :returns: A string object representing the directory that the downloaded logs are in
        """
        path = f"{self.download_path}/logs"
        if not os.path.exists(path):
            os.mkdir(path)

        blobs = self.storage_client.list_blobs(
            self.gcs_bucket,
            prefix=f"logs/{self.job_name}/{self.build_id}/artifacts/{self.job_name_safe}",
        )

        files_to_download = ["finished.json", "build-log.txt"]

        for blob in blobs:
            blob_name = blob.name.split("/")[-1]
            blob_step = blob.name.split("/")[-2]

            if blob_name in files_to_download:
                # Add step to list if it doesn't already exist
                if blob_step not in self.steps:
                    self.steps.append(blob_step)

                # Create step directory if it does not already exist
                if not os.path.exists(f"{path}/{blob_step}"):
                    os.mkdir(f"{path}/{blob_step}")

                # Download blob
                file = f"{path}/{blob_step}/{blob_name}"
                with open(file, "xb") as target:
                    blob.download_to_file(target)
                    self.logger.info(f"{file} downloaded successfully...")

        return path

    def download_junit(self) -> str:
        """
        Used to download any artifact for steps that include "junit" in the file name.

        :returns: A string object representing the directory that the downloaded junit files are in
        """
        path = f"{self.download_path}/artifacts"
        if not os.path.exists(path):
            os.mkdir(path)

        blobs = self.storage_client.list_blobs(
            self.gcs_bucket,
            prefix=f"logs/{self.job_name}/{self.build_id}/artifacts/{self.job_name_safe}",
        )
        for blob in blobs:
            blob_name = blob.name.split("/")[-1]

            if "junit" in blob_name:
                blob_step = blob.name.split("/")[5]

                # Create a step directory if it does not already exist
                if not os.path.exists(f"{path}/{blob_step}"):
                    os.mkdir(f"{path}/{blob_step}")

                # Download blob
                file = f"{path}/{blob_step}/{blob_name}"
                with open(file, "xb") as target:
                    blob.download_to_file(target)
                    self.logger.info(f"{file} downloaded successfully...")

        return path

    def find_failures(self) -> list[dict[str, str]]:
        """
        Ultimately, this function is used to generate a list of failures for a Prow job. The function works by iterating
        through downloaded log files and checks the finished.json file for the status of a step. If the status is not
        passed, it will mark the step as failed. It then iterates through all the junit files for each step and
        classifies a step as failed if there is a test failure.

        :returns: A list of dictionaries each item in the list will look like {"step": "some-step-name", "failure_type": "pod_failure OR test_failure"}
        """
        # The failures list should be a list of dictionary objects that define a failure.
        # The dictionary objects look like:
        # {"step": "some-step-name", "failure_type": "pod_failure OR test_failure"}
        # You'll notice there are two options for failure_type.
        # pod_failure = some non-zero exit code occurred in a pod - the "passed" value in "finished.json" is false
        # test_failure = one or more tests in the gathered junit files is marked as failed
        failures = []

        # Find failed pods in the logs directory
        for root, dirs, files in os.walk(self.logs_dir):
            for file_name in files:
                if file_name == "finished.json":
                    file_path = os.path.join(root, file_name)
                    with open(file_path) as file:
                        data = json.load(file)
                        if data.get("passed", False) is False:
                            step = os.path.basename(os.path.dirname(file_path))
                            failure = {
                                "step": step,
                                "failure_type": "pod_failure",
                            }
                            failures.append(failure)
                            self.logger.info(f"Found pod failure in step: {step}")

        # Find failures in JUnit results
        for root, dirs, files in os.walk(self.junit_dir):
            for file_name in files:
                if ("junit" in file_name) and ("xml" in file_name):
                    file_path = os.path.join(root, file_name)
                    try:
                        junit_xml = junitparser.JUnitXml.fromfile(file_path)
                    except junitparser.junitparser.JUnitXmlError:
                        self.logger.warning(
                            f"Attempted to parse {file_name}, but it doesn't seem to be a JUnit results file.",
                        )
                        continue
                    step = os.path.basename(os.path.dirname(file_path))

                    for suite in junit_xml:
                        for case in suite:
                            if hasattr(case, "result") and case.result:
                                for result in case.result:
                                    if isinstance(result, junitparser.Failure):
                                        failure = {
                                            "step": step,
                                            "failure_type": "test_failure",
                                        }
                                        # Override any failures that have been found. This is only because some test
                                        # suites return a non-zero exit code if a test fails. We would like to classify
                                        # Those failures as the test_failure type.
                                        existing_failures = [
                                            f for f in failures if f["step"] == step
                                        ]
                                        if existing_failures:
                                            failures = [
                                                f for f in failures if f["step"] != step
                                            ]
                                        failures.append(failure)
                                        self.logger.info(
                                            f"Found test failure in step: {step}",
                                        )
                            elif isinstance(case, junitparser.Failure):
                                failure = {
                                    "step": step,
                                    "failure_type": "test_failure",
                                }
                                # Override any failures that have been found. This is only because some test
                                # suites return a non-zero exit code if a test fails. We would like to classify
                                # Those failures as the test_failure type.
                                existing_failures = [
                                    f for f in failures if f["step"] == step
                                ]
                                if existing_failures:
                                    failures = [
                                        f for f in failures if f["step"] != step
                                    ]
                                failures.append(failure)
                                self.logger.info(
                                    f"Found test failure in step: {step}",
                                )

        return failures

    def file_jira_issues(self) -> list[str]:
        """
        Used to file bugs in Jira based on a list of failures.

        :returns: A list of strings. Each string represents the key of a Jira bug filed
        """
        rule_failure_pairs = []
        bugs_filed = []

        # Find rules that match the failures found.
        for failure in self.failures:
            rule_matches = self.failure_matches_rule(
                failure=failure,
                rules=self.firewatch_config.rules,
                default_jira_project=self.firewatch_config.default_jira_project,
            )
            for rule in rule_matches:
                rule_failure_pairs.append({"rule": rule, "failure": failure})

        for pair in rule_failure_pairs:
            date = datetime.now()
            project = pair["rule"]["jira_project"]
            epic = pair["rule"]["jira_epic"] if "jira_epic" in pair["rule"] else None
            component = (
                pair["rule"]["jira_component"]
                if "jira_component" in pair["rule"]
                else None
            )
            summary = f"Failure in {self.job_name}, {date.strftime('%m-%d-%Y')}"
            description = self.build_issue_description(
                step_name=pair["failure"]["step"],
                classification=pair["rule"]["classification"],
            )
            type = "Bug"
            file_attachments = self.get_file_attachments(
                step_name=pair["failure"]["step"],
            )
            labels = [
                self.job_name,
                pair["failure"]["step"],
                pair["failure"]["failure_type"],
            ]
            affects_version = (
                pair["rule"]["jira_affects_version"]
                if "jira_affects_version" in pair["rule"]
                else None
            )

            # Find duplicate bugs
            duplicate_bugs = self.find_duplicate_bugs(
                project=project,
                job_name=self.job_name,
                failed_step=pair["failure"]["step"],
                failure_type=pair["failure"]["failure_type"],
            )

            # If duplicates are found, comment
            if len(duplicate_bugs) > 0:
                for bug in duplicate_bugs:
                    self.add_duplicate_comment(
                        issue_id=bug,
                        failed_step=pair["failure"]["step"],
                        classification=pair["rule"]["classification"],
                    )

            # If duplicates are not found, file a bug
            else:
                jira_issue = self.jira.create_issue(
                    project=project,
                    summary=summary,
                    description=description,
                    issue_type=type,
                    component=component,
                    epic=epic,
                    file_attachments=file_attachments,
                    labels=labels,
                    affects_version=affects_version,
                )
                bugs_filed.append(jira_issue.key)

        return bugs_filed

    def find_duplicate_bugs(
        self,
        project: str,
        job_name: Optional[str],
        failed_step: str,
        failure_type: str,
    ) -> list[str]:
        """
        Searches Jira for possible duplicate bugs in the given project. If a bug in the same job, with the same failure_type, and the same failed_step, is found a list of duplicate bugs is returned.

        :param project: Jira project to search in
        :param job_name: Job name to search for
        :param failed_step: Failed step name to search for
        :param failure_type: Failure type to match

        :return: A list of duplicate bugs that are still open
        """

        self.logger.info(
            f'Searching for duplicate bugs in project {project} for a "{failure_type}" failure type in the {failed_step} step.',
        )

        # This JQL query will find any bug in the provided project that:
        # Has a label that matches the job name
        # AND has a label that matches the failed step name
        # AND has a label that matches the failure type
        # AND the bugs are not closed
        jql_query = f'project = {project} AND labels="{job_name}" AND labels="{failed_step}" AND labels="{failure_type}" AND status not in (closed)'
        duplicate_bugs = self.jira.search(jql_query=jql_query)

        if len(duplicate_bugs) > 0:
            self.logger.info("Possible duplicate bugs found:")
            for bug in duplicate_bugs:
                self.logger.info(f"https://issues.redhat.com/browse/{bug}")

        return duplicate_bugs

    def add_duplicate_comment(
        self,
        issue_id: str,
        failed_step: str,
        classification: str,
    ) -> None:
        """
        Builds a comment saying there is a duplicate failure and uses the Jira connection to add the comment to the duplicate bug

        :param issue_id: Bug to comment on
        :param failed_step: Failed step to put in comment
        :param classification: Classification to put in comment
        :return: None
        """
        comment = f"""
                A duplicate failure was identified in a recent run of the {self.job_name} job:

                *Link:* https://prow.ci.openshift.org/view/gs/origin-ci-test/logs/{self.job_name}/{self.build_id}
                *Build ID:* {self.build_id}
                *Classification:* {classification}
                *Failed Step:* {failed_step}

                Please see the link provided above to determine if this is the same issue. If it is not, please manually file a new bug for this issue.

                This comment was created using [firewatch in OpenShift CI|https://github.com/CSPI-QE/firewatch]
            """

        self.jira.comment(issue_id=issue_id, comment=comment)

    def failure_matches_rule(
        self,
        failure: dict[str, str],
        rules: Any,
        default_jira_project: str,
    ) -> list[dict[str, str]]:
        """
        Determines if a failure matches a rule in the firewatch config. If there is no matching rule, a default rule
        will be returned.

        :param failure: A dictionary item representing a failure
        :param rules: A list of firewatch rules
        :param default_jira_project: A string value of the Jira project you'd like to use by default

        :returns: A list of rules that the failure may match
        """
        # Check if the step matches a "step" in the firewatch_config
        matching_rules = []
        ignored_rules = []

        default_rule = {
            "step": "!none",
            "failure_type": "!none",
            "classification": "!none",
            "jira_project": default_jira_project,
        }

        for rule in rules:

            # Check if the rule should be ignored
            if "ignore" in rule and (rule["ignore"].lower() == "true"):
                ignore_rule = True
            else:
                ignore_rule = False

            if fnmatch.fnmatch(failure["step"], rule["step"]) and (
                (failure["failure_type"] == rule["failure_type"])
                or rule["failure_type"] == "all"
            ):
                if ignore_rule:
                    ignored_rules.append(rule)
                else:
                    matching_rules.append(rule)

        if (len(matching_rules) < 1) and (len(ignored_rules) < 1):
            if default_rule not in matching_rules:
                matching_rules.append(default_rule)

        return matching_rules

    def get_file_attachments(self, step_name: str) -> list[str]:
        """
        Generates a list of filepaths for logs and junit files associated with the step defined in the step_name
        parameter.

        :param step_name: A string object representing the name of the step to gather files for

        :returns: A list of filepaths for logs and junit files associated with the step
        """
        attachments = []
        if os.path.exists(f"{self.logs_dir}/{step_name}"):
            for root, dirs, files in os.walk(f"{self.logs_dir}/{step_name}"):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    attachments.append(file_path)

        if os.path.exists(f"{self.junit_dir}/{step_name}"):
            for root, dirs, files in os.walk(f"{self.junit_dir}/{step_name}"):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    attachments.append(file_path)

        return attachments

    def build_issue_description(self, step_name: str, classification: str) -> str:
        """
        Generates a description for a Jira bug to be filed for a failure.

        :param step_name: A string object representing the name of a failed step
        :param classification: A string object representing the best-guess classification for a bug

        :returns: A string object that is the description of a Jira bug
        """
        description = f"""
            *Link:* https://prow.ci.openshift.org/view/gs/origin-ci-test/logs/{self.job_name}/{self.build_id}
            *Build ID:* {self.build_id}
            *Classification:* {classification}
            *Failed Step:* {step_name}

            Please see the link provided above along with the logs and junit files attached to the bug.

            This bug was filed using [firewatch in OpenShift CI|https://github.com/CSPI-QE/firewatch)]
        """

        return description

    def relate_issues(self, issues: list[str]) -> None:
        """
        Creates a relation for every issue created for a run.

        :param issues: A list of Jira issue keys to relate to one another.

        :returns: None
        """
        self.logger.info("Relating all Jira issues created for this run")
        for i in range(len(issues)):
            current_issue = issues[i]

            for j in range(i + 1, len(issues)):
                related_issue = issues[j]
                self.jira.relate_issues(
                    inward_issue=current_issue,
                    outward_issue=related_issue,
                )

    def is_rehearsal(self) -> bool:
        """
        Determines if a run is a rehearsal run.

        :returns: A boolean value. If run is a rehearsal, return True. If run is not a rehearsal, return False
        """
        if (
            self.job_name is not None
            and isinstance(self.job_name, str)
            and self.job_name.startswith("rehearse")
        ):
            self.logger.info(f"Run #{self.build_id} is a rehearsal job.")
            return True
        return False

    def has_test_failures(self) -> bool:
        """
        Determines if any of the failures in the failures list has any test_failures

        :returns: A boolean value. Any of the failures are test_failures, return True. If not, return False
        """
        for failure in self.failures:
            if failure["failure_type"] == "test_failure":
                return True
        return False
