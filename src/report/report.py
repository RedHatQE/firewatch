import os
import shutil
from datetime import datetime
from typing import Any
from typing import Optional
from typing import Tuple

import jira
from simple_logger.logger import get_logger

from src.objects.configuration import Configuration
from src.objects.failure import Failure
from src.objects.failure_rule import FailureRule
from src.objects.jira_base import Jira
from src.objects.job import Job
from src.report.constants import JOB_PASSED_SINCE_TICKET_CREATED_LABEL


class Report:
    def __init__(self, firewatch_config: Configuration, job: Job) -> None:
        """
        Builds the Report object. This class is used to file Jira issues for OpenShift failures.

        Args:
            firewatch_config (Configuration): A valid firewatch Configuration object.
            job (Job): A valid Job object representing the prow job being checked for failures/reported on.
        """
        self.logger = get_logger(__name__)

        # If job is a rehearsal
        if job.is_rehearsal:
            self.logger.info(f"Deleting job directory: {job.download_path}")
            try:
                shutil.rmtree(job.download_path)
            except Exception as error:
                self.logger.error(f"Error deleting job directory: {error}")

            self.exit_on_failures(firewatch_config=firewatch_config, job=job)

            exit(0)

        # If job is retrigger
        if job.is_retriggered:
            self.logger.info(f"Adding retrigger label to issue: {job.name}")
            if job.name:
                self.add_retrigger_job_label(jira=firewatch_config.jira, issue_id=job.name)
            else:
                self.logger.warning("Job name is None. Cannot add retrigger label")

        bugs_filed = None
        bugs_updated = None
        # If job has failures, file bugs
        if job.failures:
            bugs_filed, bugs_updated = self.file_jira_issues(
                failures=job.failures,  # type: ignore
                firewatch_config=firewatch_config,
                job=job,
            )
            if len(bugs_filed) > 1:
                self.relate_issues(issues=bugs_filed, jira=firewatch_config.jira)
        if not bugs_filed and not bugs_updated:
            self.logger.info(f"No failures for {job.name} #{job.build_id} were found!")

            # Report success
            if firewatch_config.success_rules:
                self.report_success(job=job, firewatch_config=firewatch_config)

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
                        self.logger.info(
                            f"Adding passed job label to issue {bug}",
                        )
                        self.add_passing_job_label(
                            jira=firewatch_config.jira,
                            issue_id=bug,
                        )

        # Delete the job directory
        if not firewatch_config.keep_job_dir:
            self.logger.info(f"Deleting job directory: {job.download_path}")
            shutil.rmtree(job.download_path)

        self.exit_on_failures(firewatch_config=firewatch_config, job=job)

    def file_jira_issues(
        self,
        failures: list[Failure],
        firewatch_config: Configuration,
        job: Job,
    ) -> Tuple[list[str], list[str]]:
        """
        Using a list of failures, the firewatch config, and the Job object, file issues in Jira.

        Args:
            failures (list[Failure]): A list of Failure objects representing the failures found in a prow job.
            firewatch_config (Configuration): A valid firewatch Configuration object.
            job (Job): A valid Job object representing the prow job to be checked/reported on.

        Returns:
            list[str]: A list of strings representing the bugs filed in Jira.
            list[str]: A list of strings representing the duplicate bugs updated in Jira.
        """
        rule_failure_pairs = []
        bugs_filed: list[str] = []
        dup_bugs_updated: list[str] = []

        # Get rule_failure_pairs
        for failure in failures:
            rule_matches = self.failure_matches_rule(
                failure=failure,
                rules=firewatch_config.failure_rules,  # type: ignore
                default_jira_project=firewatch_config.default_jira_project,
            )
            for rule in rule_matches:
                rule_failure_pairs.append({"rule": rule, "failure": failure})

        rule_failure_pairs = self.filter_priority_rule_failure_pairs(
            rule_failure_pairs=rule_failure_pairs,
        )

        # File bugs
        for pair in rule_failure_pairs:
            # If verbose_test_failure_reporting is True, check the limit before filing bugs
            if firewatch_config.verbose_test_failure_reporting:
                if firewatch_config.verbose_test_failure_reporting_ticket_limit is not None:
                    if len(bugs_filed) >= firewatch_config.verbose_test_failure_reporting_ticket_limit:
                        self.logger.warning(
                            f'Ticket limit of {firewatch_config.verbose_test_failure_reporting_ticket_limit} reached. No more bugs will be filed. If you would like to increase this limit, specify "--verbose-test-failure-reporting-ticket-limit <limit>" when executing firewatch report.',
                        )
                        break

            # Gather bug information
            date = datetime.now()
            project = pair["rule"].jira_project  # type: ignore
            epic = pair["rule"].jira_epic  # type: ignore
            component = pair["rule"].jira_component  # type: ignore
            affects_version = pair["rule"].jira_affects_version  # type: ignore
            assignee = pair["rule"].jira_assignee  # type: ignore
            priority = pair["rule"].jira_priority  # type: ignore
            security_level = pair["rule"].jira_security_level  # type: ignore
            summary = f"Failure in {job.name}{' -' + pair['failure'].failed_test_name if firewatch_config.verbose_test_failure_reporting else ''} - {date.strftime('%m-%d-%Y')}"  # type: ignore
            self.logger.info(summary)
            description = self._get_issue_description(
                step_name=pair["failure"].step,  # type: ignore
                failure_type=pair["failure"].failure_type,  # type: ignore
                classification=pair["rule"].classification,  # type: ignore
                job=job,  # type: ignore
                failed_test_name=(
                    pair["failure"].failed_test_name  # type: ignore
                    if firewatch_config.verbose_test_failure_reporting
                    else None
                ),  # type: ignore
                jira=firewatch_config.jira,  # type: ignore
            )
            issue_type = "Bug"
            file_attachments = self._get_file_attachments(
                step_name=pair["failure"].step,  # type: ignore
                logs_dir=job.logs_dir,
                junit_dir=job.junit_dir,
                junit_file=(
                    pair["failure"].failed_test_junit_path  # type: ignore
                    if firewatch_config.verbose_test_failure_reporting
                    else None
                ),  # type: ignore
            )
            labels = self._get_issue_labels(
                job_name=job.name,
                step_name=pair["failure"].step,  # type: ignore
                type=pair["failure"].failure_type,  # type: ignore
                jira_additional_labels=pair["rule"].jira_additional_labels,  # type: ignore
                jira_additional_labels_filepath=firewatch_config.additional_labels_file,
                failed_test_name=(
                    pair["failure"].failed_test_name  # type: ignore
                    if firewatch_config.verbose_test_failure_reporting
                    else None
                ),  # type: ignore
            )

            # Find duplicate bugs
            duplicate_bugs = self._get_duplicate_bugs(
                project=project,
                job_name=job.name,
                failed_step=pair["failure"].step,  # type: ignore
                failure_type=pair["failure"].failure_type,  # type: ignore
                failed_test_name=(
                    pair["failure"].failed_test_name  # type: ignore
                    if firewatch_config.verbose_test_failure_reporting
                    else None
                ),  # type: ignore
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
                        failed_test_name=(
                            pair["failure"].failed_test_name  # type: ignore
                            if firewatch_config.verbose_test_failure_reporting
                            else None
                        ),  # type: ignore
                    )
                    dup_bugs_updated.append(bug)
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
                    security_level=security_level,
                )
                bugs_filed.append(jira_issue.key)

        return bugs_filed, dup_bugs_updated

    def report_success(self, job: Job, firewatch_config: Configuration) -> None:
        """
        Reports a success story to Jira in the default Jira project and the default Jira epic.
        Args:
            firewatch_config (Configuration): A valid firewatch Configuration object.
            job (Job): A valid Job object representing the prow job to be reported on.
        Returns:
            None
        """
        self.logger.info(f"Reporting job {job.name} success.")
        date = datetime.now()
        for rule in firewatch_config.success_rules if firewatch_config.success_rules else []:
            labels = self._get_issue_labels(
                job_name=job.name,
                type="success",
                jira_additional_labels=rule.jira_additional_labels,  # type: ignore
                jira_additional_labels_filepath=firewatch_config.additional_labels_file,
            )

            firewatch_config.jira.create_issue(
                project=rule.jira_project,
                summary=f"Job {job.name} passed - {date.strftime('%m-%d-%Y')}",
                description=self._get_issue_description(
                    job=job,  # type: ignore
                    success_issue=True,
                ),
                issue_type="Story",
                epic=rule.jira_epic,
                labels=labels,
                component=rule.jira_component,
                affects_version=rule.jira_affects_version,
                assignee=rule.jira_assignee,
                priority=rule.jira_priority,
                security_level=rule.jira_security_level,
                close_issue=True,
            )

    def filter_priority_rule_failure_pairs(
        self,
        rule_failure_pairs: list[dict[Any, Any]],
    ) -> list[dict[Any, Any]]:
        """
        Filters a list of rule/failure pairs based on user-defined groups/priorities. If there are multiple rule/failure
        pairs with a group defined in the rule, it will determine which rule is the highest priority. After filtering
        out the lower priority rule/failure pairs, it will return the new list of rule/failure pairs.

        Args:
            rule_failure_pairs (list[dict[Any, Any]]): A list of rule/failure pairs.
        Returns:
            list[dict[Any, Any]]: A list of rule/failure pairs that have been filtered for user-defined priorities.
        """

        groups: dict[Any, Any] = {}  # {"some-group-name": [pair1, pair2, pair3]}
        filtered_rule_failure_pairs = []
        none_filtered_failure_pairs = []

        for pair in rule_failure_pairs:
            rule = pair["rule"]
            if rule.group_name and rule.group_priority:  # type: ignore
                groups.setdefault(rule.group_name, []).append(pair)  # type: ignore
            else:
                none_filtered_failure_pairs.append(pair)

        for _, group_pair in groups.items():
            highest_priority = min(_group.get("rule").group_priority for _group in group_pair)
            filtered_rule_failure_pairs.extend(
                [_group_pair for _group_pair in group_pair if _group_pair["rule"].group_priority == highest_priority],
            )

        return filtered_rule_failure_pairs + none_filtered_failure_pairs

    def failure_matches_rule(
        self,
        failure: Failure,
        rules: list[FailureRule],
        default_jira_project: str,
    ) -> list[FailureRule]:
        """
        Used to check if a failure matches any rules in the firewatch config.

        Args:
            failure (Failure): A Failure object representing a failure found in a prow job.
            rules (list[Rule]): A list of Rule objects from the firewatch config.
            default_jira_project (str): A string object representing the default Jira project to report bugs to if there isn't a matching rule.

        Returns:
            list[Rule]: A list of Rule objects that represents the list of Rules a failure matches.
        """
        matching_rules = []
        ignored_rules = []

        default_rule_dict = {
            "step": "!none",
            "failure_type": "!none",
            "classification": "!none",
            "jira_project": default_jira_project,
        }
        default_rule = FailureRule(default_rule_dict)

        for rule in rules:
            if rule.matches_failure(failure):
                if rule.ignore:
                    ignored_rules.append(rule)
                else:
                    matching_rules.append(rule)

        if (len(matching_rules) < 1) and (len(ignored_rules) < 1):
            if default_rule not in matching_rules:
                matching_rules.append(default_rule)

        # Sort matching_rules by the identical rules to failure.step
        if matching_rules:
            matching_rules = sorted(matching_rules, key=lambda x: x.step.__eq__(failure.step), reverse=True)
        return matching_rules

    def add_passing_job_comment(self, job: Job, jira: Jira, issue_id: str) -> None:
        """
        Used to make a comment on a Jira issue that is open but has had a passing job since the issue was filed.

        Args:
            job (Job): Job object of the passing job.
            jira (Jira): Jira object.
            issue_id (str): Issue ID of the open issue to comment on.

        Returns:
            None
        """
        comment = f"""
                                h4. *JOB RECENTLY PASSED*

                                This job has been run successfully since this bug was filed. Please verify that this bug is still relevant and close it if needed.

                                *Passing Run Link:* https://prow.ci.openshift.org/view/gs/test-platform-results/logs/{job.name}/{job.build_id}
                                *Passing Run Build ID:* {job.build_id}


                                _Please add the "ignore-passing-notification" tag to this bug to avoid future passing job notifications._

                                This comment was created using [firewatch in OpenShift CI|https://github.com/CSPI-QE/firewatch].
                            """
        jira.comment(issue_id=issue_id, comment=comment)

    def add_passing_job_label(self, jira: Jira, issue_id: str) -> None:
        """
        Used to add a label on a Jira issue that is open but has had a passing job since the issue was filed.

        Args:
            jira (Jira): Jira object.
            issue_id (str): Issue ID of the open issue to comment on.

        Returns:
            None
        """
        jira.add_labels_to_issue(
            issue_id_or_key=issue_id,
            labels=[JOB_PASSED_SINCE_TICKET_CREATED_LABEL],
        )

    def add_retrigger_job_label(self, jira: Jira, issue_id: str) -> None:
        """
        Used to add a label on a Jira issue that the latest build is retrigger of job.

        Args:
            jira (Jira): Jira object.
            issue_id (str): Issue ID of the open issue to comment on.

        Returns:
            None
        """
        assert issue_id is not None, "issue_id cannot be None"
        jira.add_labels_to_issue(
            issue_id_or_key=issue_id,
            labels=["RETRIGGER_JOB"],
        )

    def add_duplicate_comment(
        self,
        issue_id: str,
        failed_step: str,
        classification: str,
        job: Job,
        jira: Jira,
        failed_test_name: Optional[str] = None,
    ) -> None:
        """
        Used to make a comment on a Jira issue that is a suspected duplicate.

        Args:
            issue_id (str): Issue ID of the suspected duplicate.
            failed_step (str): Name of the failed step.
            classification (str): Classification of the failure.
            job (Job): Job object of the failed job.
            jira (Jira): Jira object.
            failed_test_name (Optional[str]): Name of failed test, else None

        Returns:
            None
        """
        comment = f"""
                        A duplicate failure was identified in a recent run of the {job.name} job:

                        *Link:* https://prow.ci.openshift.org/view/gs/test-platform-results/logs/{job.name}/{job.build_id}
                        *Build ID:* {job.build_id}
                        *Classification:* {classification}
                        *Failed Step:* {failed_step}
                        {"*Failed Test:* " + failed_test_name if failed_test_name else ""}

                        Please see the link provided above to determine if this is the same issue. If it is not, please manually file a new bug for this issue.

                        This comment was created using [firewatch in OpenShift CI|https://github.com/CSPI-QE/firewatch]
                    """

        jira.comment(issue_id=issue_id, comment=comment)

    def relate_issues(self, issues: list[str], jira: Jira) -> None:
        """
        Creates a relation for every issue created for a run.

        Args:
            issues (list[str]): A list of Jira issue keys to relate to one another.
            jira (Jira): Jira object.

        Returns:
            None
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

    def exit_on_failures(self, firewatch_config: Configuration, job: Job) -> None:
        if firewatch_config.fail_with_test_failures and job.has_test_failures:
            self.logger.error("Test failures found and --fail-with-test-failures flag is set. Exiting with exit code 1")
            exit(1)

        if firewatch_config.fail_with_pod_failures and job.has_pod_failures:
            self.logger.error("Pod failures found and --fail-with-pod-failures flag is set. Exiting with exit code 1")
            exit(1)

    def _get_file_attachments(
        self,
        step_name: str,
        logs_dir: str,
        junit_dir: str,
        junit_file: Optional[str] = None,
    ) -> list[str]:
        """
        Generates a list of filepaths for logs and junit files associated with the step defined in the step_name
        parameter.

        Args:
            step_name (str): A string object representing the name of the step to gather files for
            logs_dir (str): A string object representing the path to the logs directory
            junit_dir (str): A string object representing the path to the junit archives directory

        Returns:
            list[str]: A list of filepaths for logs and junit files associated with the step
        """
        attachments = []

        if os.path.exists(f"{logs_dir}/{step_name}"):
            for root, dirs, files in os.walk(f"{logs_dir}/{step_name}"):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    attachments.append(file_path)

        if junit_file:
            if os.path.exists(junit_file):
                attachments.append(junit_file)
                return attachments

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
        job: Job,
        step_name: Optional[str] = None,
        failure_type: Optional[str] = None,
        classification: Optional[str] = None,
        failed_test_name: Optional[str] = None,
        success_issue: Optional[bool] = False,
        jira: Optional[Jira] = None,
    ) -> str:
        """
        Used to generate the description of a bug to be filed in Jira.

        Args:
            job_name (str): Name of job that failed.
            build_id (str): Build ID of failure.
            step_name (Optional[str]): Name of the step that failed.
            classification (Optional[str]): Classification of the failure.
            failure_type (Optional[str]): Failure type.
            failed_test_name (Optional[str]): Name of failed test, else None
            success_issue (Optional [bool]): Description for success issue if True else for failure

        Returns:
            str: String object representing the description.
        """
        link_line_base_url = (
            "https://qe-private-deck-ci.apps.ci.l2s4.p1.openshiftapps.com/view/gs/qe-private-deck/logs/"
            if job.is_private_deck
            else "https://prow.ci.openshift.org/view/gs/test-platform-results/logs/"
        )
        link_line = f"*Prow Job Link:* [{job.name} #{job.build_id}|{link_line_base_url}{job.name}/{job.build_id}]"
        build_id_line = f"*Build ID:* {job.build_id}"
        job_history_link_line = f"*Job History:* [{job.name}|https://prow.ci.openshift.org/job-history/gs/test-platform-results/logs/{job.name}]"
        firewatch_link_line = f"This {'issue' if success_issue else 'bug'} was filed using [firewatch in OpenShift CI|https://github.com/CSPI-QE/firewatch]"

        # If the issue is being created for a failure
        if not success_issue:
            classification_line = f"*Classification:* {classification}"
            failed_step_line = f"*Failed Step:* {step_name}"
            failed_test_line = f"*Failed Test:* {failed_test_name}" if failed_test_name else ""
            past_bugs = self._get_past_bugs(
                failed_step=step_name,  # type: ignore
                failure_type=failure_type,  # type: ignore
                failed_test_name=failed_test_name,  # type: ignore
                jira=jira,  # type: ignore
            )
            description = f"{link_line}\n{build_id_line}\n{classification_line}\n{failed_step_line}\n{failed_test_line}\n{job_history_link_line}\n"
            if past_bugs:
                failed_test_portion = f" and failed test *{failed_test_name}*" if failed_test_name else ""
                description += f"\n----\nHere are up to 10 related bugs produced by the step *{step_name}* and failed with failure type *{failure_type}*{failed_test_portion}:\n{self._get_past_bugs_table(issues=past_bugs, jira=jira)}\n"  # type: ignore

        # If the issue is being created for a success
        else:
            description = f"{link_line}\n{build_id_line}"

        description += f"\n{firewatch_link_line}"

        return description

    def _get_issue_labels(
        self,
        job_name: Optional[str],
        type: str,
        jira_additional_labels: Optional[list[str]],
        jira_additional_labels_filepath: Optional[str],
        failed_test_name: Optional[str] = None,
        step_name: Optional[str] = None,
    ) -> list[Optional[str]]:
        """
        Builds a list of labels to be included on the Jira issue.

        Args:
            job_name (Optional[str]): Name of failed job.
            step_name (str): Name of failed step in job.
            type (str): Failure type.
            jira_additional_labels (Optional[list[str]]): An optional list of additional labels to include.
            failed_test_name (Optional[str]): Name of failed test, else None

        Returns:
            list[Optional[str]]: A list of strings representing the labels the new Jira issue should include.
        """
        labels = [job_name, type, step_name, failed_test_name, "firewatch"]

        # Remove any None values
        labels = [label for label in labels if label]

        # Add any additional labels
        if jira_additional_labels:
            labels.extend(jira_additional_labels)
        if jira_additional_labels_filepath:
            with open(jira_additional_labels_filepath, "r") as file:
                labels.extend(line.strip() for line in file)

        return list(set(labels))

    def _get_duplicate_bugs(
        self,
        project: str,
        job_name: Optional[str],
        failed_step: str,
        failure_type: str,
        failed_test_name: Optional[str],
        jira: Jira,
    ) -> Optional[list[str]]:
        """
        Used to search for possible duplicate bugs before filing a new bug.

        Args:
            project (str): The project to search for duplicate bugs in.
            job_name (Optional[str]): Name of the failed job.
            failed_step (str): Name of the failed step.
            failure_type (str): Failure type.
            failed_test_name (Optional[str]): Name of the failed test.
            jira (Jira): Jira object.

        Returns:
            Optional[list[str]]: A list of strings representing duplicate bugs found.
        """
        self.logger.info(
            f'Searching for duplicate bugs of failure type "{failure_type}" {("and failed test case " + failed_test_name) if failed_test_name else ""} in the {failed_step} step in Jira project {project}',
        )

        # This JQL query will find any bug in the provided project that:
        # Has a label that matches the job name
        # AND has a label that matches the failed step name
        # AND has a label that matches the failure type
        # AND the bugs are not closed
        # AND issue is of type "bug"
        failed_test_filter = f'AND labels="{failed_test_name}"' if failed_test_name else ""
        jql_query = f'project = {project} AND labels="{job_name}" AND labels="{failed_step}" AND labels="{failure_type}" {failed_test_filter} AND resolution = Unresolved AND Issuetype = bug'
        duplicate_bugs = jira.search_issues(jql_query=jql_query)

        if len(duplicate_bugs) > 0:
            self.logger.info("Possible duplicate bugs found:")
            for bug in duplicate_bugs:
                self.logger.info(f"{jira.url}/browse/{bug}")

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

        Args:
            job_name (Optional[str]): A string object representing the job_name to search for.
            jira (Jira): Jia object.

        Returns:
            Optional[list[str]]: A list of string representing open bugs for a job. If none are found, None is returned.
        """
        self.logger.info(f"Searching for open bugs for job {job_name}")

        # This JQL query will find any open issue that:
        # has a label that matches the job name
        # AND a label that == "firewatch"
        # AND does NOT have a label that == "ignore-passing-notification"
        # AND is unresolved
        # AND issue is of type "bug"
        jql_query = f'labels="{job_name}" AND labels="firewatch" AND labels!="ignore-passing-notification" AND resolution = Unresolved AND Issuetype = bug'
        open_bugs = jira.search_issues(jql_query=jql_query)

        if len(open_bugs) > 0:
            self.logger.info(f"Found open bugs for job {job_name}:")
            for bug in open_bugs:
                self.logger.info(f"{jira.url}/browse/{bug}")

            return open_bugs
        else:
            return None

    def _get_past_bugs(
        self,
        failed_step: str,
        failure_type: str,
        jira: Jira,
        failed_test_name: Optional[str] = None,
    ) -> Optional[list[jira.Issue]]:
        """
        Used to search for closed bugs for a specific step and failure type.

        Args:
            failed_step (str): The name of the failed step to search for bugs under.
            failure_type (str): The failure type to search for bugs under
            jira (Jira): Jia object.
            failed_test_name (Optional[str]): Name of failed test, else None

        Returns:
            Optional[list[jira.Issue]]: An optional list of Jira issues from firewatch that are from a specific failed step and failure type.
        """
        failed_test_filter = f'AND labels="{failed_test_name}"' if failed_test_name else ""
        list_of_issues = jira.search(
            jql_query=f'labels="{failed_step}" AND labels="{failure_type}" {failed_test_filter} AND resolution != Unresolved ORDER BY created DESC',
        )

        # Reduce to 10 most recent issues
        return list_of_issues[:10]

    def _get_past_bugs_table(self, issues: list[jira.Issue], jira: Jira) -> str:
        """
        Used to build the table of bugs related to a specific step/failure type that will be put in issue descriptions

        Args:
            issues (list[jira.Issue]): A list of jira issues.
            jira (Jira): Jia object.

        Returns:
            str: A string object representing the table of related Jira issues to be put in a bug description.
        """
        table = "||Bug||Date Created||Assignee||"
        issue_rows = []

        for issue in issues:
            date_created = issue.get_field("created").split("T")[0]
            assignee = issue.get_field("assignee")
            issue_row = f"\n|[{issue.key}|{jira.url}/browse/{issue.key}]|{date_created}|{assignee}|"
            issue_rows.append(issue_row)

        for row in issue_rows:
            table += row

        return table
