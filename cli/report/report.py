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
import logging
import os
from datetime import datetime
from typing import Optional

from cli.objects.configuration import Configuration
from cli.objects.failure import Failure
from cli.objects.jira_base import Jira
from cli.objects.job import Job
from cli.objects.rule import Rule


class Report:
    def __init__(self, firewatch_config: Configuration, job: Job) -> None:
        """
        Builds the Report object. This class is used to file Jira issues for OpenShift failures.

        :param firewatch_config: A valid firewatch Configuration object.
        :param job: A valid Job object representing the prow job being checked for failures/reported on.
        """
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(
            __name__,
        )

        # If job is a rehearsal, exit 0
        if job.is_rehearsal:
            exit(0)

        # If job has failures, file bugs
        if job.has_failures:
            bugs_filed = self.file_jira_issues(
                failures=job.failures,  # type: ignore
                firewatch_config=firewatch_config,
                job=job,
            )
            if len(bugs_filed) > 1:
                self.relate_issues(issues=bugs_filed, jira=firewatch_config.jira)
            if firewatch_config.fail_with_test_failures and job.has_test_failures:
                self.logger.info(
                    "Test failures found and --fail_with_test_failures flag is set. Exiting with exit code 1",
                )
                exit(1)
        else:
            self.logger.info(f"No failures for {job.name} #{job.build_id} were found!")

            # Look for open bugs and
            open_bugs = self._get_open_bugs(
                job_name=job.name,
                jira=firewatch_config.jira,
            )
            if open_bugs is not None:
                if len(open_bugs) > 0:
                    for bug in open_bugs:
                        self.logger.info(
                            f"Adding passed job notification to issue {bug}",
                        )
                        self.add_passing_job_comment(
                            job=job,
                            jira=firewatch_config.jira,
                            issue_id=bug,
                        )

    def file_jira_issues(
        self,
        failures: list[Failure],
        firewatch_config: Configuration,
        job: Job,
    ) -> list[str]:
        """
        Using a list of failures, the firewatch config, and the Job object, file issues in Jira.

        :param failures: A list of Failure objects representing the failures found in a prow job.
        :param firewatch_config: A valid firewatch Configuration object.
        :param job: A valid Job object representing the prow job to be checked/reported on.
        :return: A list of strings representing the bugs filed in Jira.
        """
        rule_failure_pairs = []
        bugs_filed = []

        # Get rule_failure_pairs
        for failure in failures:
            rule_matches = self.failure_matches_rule(
                failure=failure,
                rules=firewatch_config.rules,  # type: ignore
                default_jira_project=firewatch_config.default_jira_project,
            )
            for rule in rule_matches:
                rule_failure_pairs.append({"rule": rule, "failure": failure})

        for pair in rule_failure_pairs:
            # Gather bug information
            date = datetime.now()
            project = pair["rule"].jira_project  # type: ignore
            epic = pair["rule"].jira_epic  # type: ignore
            component = pair["rule"].jira_component  # type: ignore
            affects_version = pair["rule"].jira_affects_version  # type: ignore
            assignee = pair["rule"].jira_assignee  # type: ignore
            priority = pair["rule"].jira_priority  # type: ignore
            summary = f"Failure in {job.name}, {date.strftime('%m-%d-%Y')}"
            description = self._get_issue_description(
                step_name=pair["failure"].step,  # type: ignore
                classification=pair["rule"].classification,  # type: ignore
                job_name=job.name,
                build_id=job.build_id,
            )
            issue_type = "Bug"
            file_attachments = self._get_file_attachments(
                step_name=pair["failure"].step,  # type: ignore
                logs_dir=job.logs_dir,
                junit_dir=job.junit_dir,
            )
            labels = self._get_issue_labels(
                job_name=job.name,
                step_name=pair["failure"].step,  # type: ignore
                failure_type=pair["failure"].failure_type,  # type: ignore
                jira_additional_labels=pair["rule"].jira_additional_labels,  # type: ignore
            )

            # Find duplicate bugs
            duplicate_bugs = self._get_duplicate_bugs(
                project=project,
                job_name=job.name,
                failed_step=pair["failure"].step,  # type: ignore
                failure_type=pair["failure"].failure_type,  # type: ignore
                jira=firewatch_config.jira,
            )

            # If duplicates are found, comment
            if duplicate_bugs:
                for bug in duplicate_bugs:
                    self.add_duplicate_comment(
                        issue_id=bug,
                        failed_step=pair["failure"].step,  # type: ignore
                        classification=pair["rule"].classification,  # type: ignore
                        job=job,
                        jira=firewatch_config.jira,
                    )
            # If duplicates are not found, file a bug
            else:
                jira_issue = firewatch_config.jira.create_issue(
                    project=project,
                    summary=summary,
                    description=description,
                    issue_type=issue_type,
                    component=component,
                    epic=epic,
                    file_attachments=file_attachments,
                    labels=labels,
                    affects_version=affects_version,
                    assignee=assignee,
                    priority=priority,
                )
                bugs_filed.append(jira_issue.key)

        return bugs_filed

    def failure_matches_rule(
        self,
        failure: Failure,
        rules: list[Rule],
        default_jira_project: str,
    ) -> list[Rule]:
        """
        Used to check if a failure matches any rules in the firewatch config.

        :param failure: A Failure object representing a failure found in a prow job.
        :param rules: A list of Rule objects from the firewatch config.
        :param default_jira_project: A string object representing the default Jira project to report bugs to if there isn't a matching rule.
        :return: A list of Rule objects that represents the list of Rules a failure matches.
        """
        matching_rules = []
        ignored_rules = []

        default_rule_dict = {
            "step": "!none",
            "failure_type": "!none",
            "classification": "!none",
            "jira_project": default_jira_project,
        }
        default_rule = Rule(default_rule_dict)

        for rule in rules:
            if fnmatch.fnmatch(failure.step, rule.step) and (
                (failure.failure_type == rule.failure_type)
                or rule.failure_type == "all"
            ):
                if rule.ignore:
                    ignored_rules.append(rule)
                else:
                    matching_rules.append(rule)

        if (len(matching_rules) < 1) and (len(ignored_rules) < 1):
            if default_rule not in matching_rules:
                matching_rules.append(default_rule)

        return matching_rules

    def add_passing_job_comment(self, job: Job, jira: Jira, issue_id: str) -> None:
        """
        Used to make a comment on a Jira issue that is open but has had a passing job since the issue was filed.

        :param job: Job object of the passing job.
        :param jira: Jira object.
        :param issue_id: Issue ID of the open issue to comment on.
        :return:
        """
        comment = f"""
                                h2. *JOB RECENTLY PASSED*

                                This job has been run successfully since this bug was filed. Please verify that this bug is still relevant and close it if needed.

                                *Passing Run Link:* https://prow.ci.openshift.org/view/gs/origin-ci-test/logs/{job.name}/{job.build_id}
                                *Passing Run Build ID:* {job.build_id}


                                _Please add the "ignore-passing-notification" tag to this bug to avoid future passing job notifications._

                                This comment was created using [firewatch in OpenShift CI|https://github.com/CSPI-QE/firewatch].
                            """
        jira.comment(issue_id=issue_id, comment=comment)

    def add_duplicate_comment(
        self,
        issue_id: str,
        failed_step: str,
        classification: str,
        job: Job,
        jira: Jira,
    ) -> None:
        """
        Used to make a comment on a Jira issue that is a suspected duplicate.

        :param issue_id: Issue ID of the suspected duplicate.
        :param failed_step: Name of the failed step.
        :param classification: Classification of the failure.
        :param job: Job object of the failed job.
        :param jira: Jira object.
        :return: None
        """
        comment = f"""
                        A duplicate failure was identified in a recent run of the {job.name} job:

                        *Link:* https://prow.ci.openshift.org/view/gs/origin-ci-test/logs/{job.name}/{job.build_id}
                        *Build ID:* {job.build_id}
                        *Classification:* {classification}
                        *Failed Step:* {failed_step}

                        Please see the link provided above to determine if this is the same issue. If it is not, please manually file a new bug for this issue.

                        This comment was created using [firewatch in OpenShift CI|https://github.com/CSPI-QE/firewatch]
                    """

        jira.comment(issue_id=issue_id, comment=comment)

    def relate_issues(self, issues: list[str], jira: Jira) -> None:
        """
        Creates a relation for every issue created for a run.

        :param issues: A list of Jira issue keys to relate to one another.

        :returns: None
        """
        self.logger.info("Relating all Jira issues created for this run.")
        relations = {}  # type: ignore

        # Populate the relations dictionary.
        # Should look like {"TEST-1234": [], "TEST-4321": []}
        for issue in issues:
            relations.update({issue: []})

        for key in relations:
            for issue in issues:
                if (key != issue) and (issue not in relations[key]):
                    related_issue = jira.relate_issues(
                        inward_issue=key,
                        outward_issue=issue,
                    )
                    if related_issue:
                        relations[key].append(issue)
                        relations[issue].append(key)

    def _get_file_attachments(
        self,
        step_name: str,
        logs_dir: str,
        junit_dir: str,
    ) -> list[str]:
        """
        Generates a list of filepaths for logs and junit files associated with the step defined in the step_name
        parameter.

        :param step_name: A string object representing the name of the step to gather files for
        :param logs_dir: A string object representing the path to the logs directory
        :param junit_dir: A string object representing the path to the junit archives directory
        :returns: A list of filepaths for logs and junit files associated with the step
        """
        attachments = []

        if os.path.exists(f"{logs_dir}/{step_name}"):
            for root, dirs, files in os.walk(f"{logs_dir}/{step_name}"):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    attachments.append(file_path)

        if os.path.exists(f"{junit_dir}/{step_name}"):
            for root, dirs, files in os.walk(f"{junit_dir}/{step_name}"):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    attachments.append(file_path)
        if len(attachments) < 1:
            self.logger.info(
                f"No file attachments for failed step {step_name} were found.",
            )
        return attachments

    def _get_issue_description(
        self,
        step_name: str,
        classification: str,
        job_name: Optional[str],
        build_id: Optional[str],
    ) -> str:
        """
        Used to generate the description of a bug to be filed in Jira.

        :param step_name: Name of the step that failed.
        :param classification: Classification of the failure.
        :param job_name: Name of job that failed.
        :param build_id: Build ID of failure.
        :return: String object representing the description.
        """
        description = f"""
                    *Link:* https://prow.ci.openshift.org/view/gs/origin-ci-test/logs/{job_name}/{build_id}
                    *Build ID:* {build_id}
                    *Classification:* {classification}
                    *Failed Step:* {step_name}

                    Please see the link provided above along with the logs and junit files attached to the bug.

                    This bug was filed using [firewatch in OpenShift CI|https://github.com/CSPI-QE/firewatch)]
                """

        return description

    def _get_issue_labels(
        self,
        job_name: Optional[str],
        step_name: str,
        failure_type: str,
        jira_additional_labels: Optional[list[str]],
    ) -> list[Optional[str]]:
        """
        Builds a list of labels to be included on the Jira issue.

        :param job_name: Name of failed job.
        :param step_name: Name of failed step in job.
        :param failure_type: Failure type.
        :param jira_additional_labels: An optional list of additional labels to include.
        :return: A list of strings representing the labels the new Jira issue should include.
        """
        labels = [
            job_name,
            step_name,
            failure_type,
            "firewatch",
        ]

        if jira_additional_labels:
            for additional_label in jira_additional_labels:
                labels.append(additional_label)

        return labels

    def _get_duplicate_bugs(
        self,
        project: str,
        job_name: Optional[str],
        failed_step: str,
        failure_type: str,
        jira: Jira,
    ) -> Optional[list[str]]:
        """
        Used to search for possible duplicate bugs before filing a new bug.

        :param project: The project to search for duplicate bugs in.
        :param job_name: Name of the failed job.
        :param failed_step: Name of the failed step.
        :param failure_type: Failure type.
        :param jira: Jira object.
        :return: A list of strings representing duplicate bugs found.
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
        duplicate_bugs = jira.search(jql_query=jql_query)

        if len(duplicate_bugs) > 0:
            self.logger.info("Possible duplicate bugs found:")
            for bug in duplicate_bugs:
                self.logger.info(f"https://issues.redhat.com/browse/{bug}")

            return duplicate_bugs
        else:
            return None

    def _get_open_bugs(
        self,
        job_name: Optional[str],
        jira: Jira,
    ) -> Optional[list[str]]:
        """
        Used to search for open bugs for a specific job.

        :param job_name: A string object representing the job_name to search for.
        :param jira: Jia object.
        :return: A list of string representing open bugs for a job. If none are found, None is returned.
        """
        self.logger.info(f"Searching for open bugs for job {job_name}")

        # This JQL query will find any open issue that:
        # has a label that matches the job name
        # AND a label that == "firewatch"
        # AND does NOT have a label that == "ignore-passing-notification"
        # AND a is not in the "closed" status
        jql_query = f'labels="{job_name}" AND labels="firewatch" AND labels!="ignore-passing-notification" AND status not in (closed)'
        open_bugs = jira.search(jql_query=jql_query)

        if len(open_bugs) > 0:
            self.logger.info(f"Found open bugs for job {job_name}:")
            for bug in open_bugs:
                self.logger.info(f"https://issues.redhat.come/browse/{bug}")

            return open_bugs
        else:
            return None
