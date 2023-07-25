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
import logging
import os

import tests.unittests.helpers as helpers
from cli.objects.failure import Failure
from cli.objects.rule import Rule
from cli.report.report import Report


class TestFirewatchReport:
    def test_get_issue_labels(self) -> None:
        job_name = "test-job-name"
        step_name = "test-step-name"
        failure_type = "test_failure"
        additional_labels = ["additional-label-1", "additional-label-2"]

        # Test no additional labels
        labels = set(
            Report._get_issue_labels(
                self,
                job_name=job_name,
                step_name=step_name,
                failure_type=failure_type,
                jira_additional_labels=[],
            ),
        )
        compare_labels = {job_name, step_name, failure_type, "firewatch"}
        assert labels == compare_labels

        # Test with additional labels
        labels = set(
            Report._get_issue_labels(
                self,
                job_name=job_name,
                step_name=step_name,
                failure_type=failure_type,
                jira_additional_labels=additional_labels,
            ),
        )
        compare_labels = {
            job_name,
            step_name,
            failure_type,
            "firewatch",
            "additional-label-1",
            "additional-label-2",
        }
        assert labels == compare_labels

    def test_failure_matches_rule(self) -> None:
        default_jira_project = "TEST"
        failure = Failure(failed_step="failed-step", failure_type="test_failure")
        ignore_rule = Rule(
            rule_dict={
                "step": "failed-step",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
                "ignore": "true",
            },
        )
        no_match_rule = Rule(
            rule_dict={
                "step": "other-step",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
            },
        )
        match_rule = Rule(
            rule_dict={
                "step": "failed-step",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
            },
        )
        default_rule_dict = {
            "step": "!none",
            "failure_type": "!none",
            "classification": "!none",
            "jira_project": default_jira_project,
        }
        default_rule = Rule(default_rule_dict)

        # Test a failure that does not match any rule
        rules = [no_match_rule]
        matching_rules = Report.failure_matches_rule(
            self,
            failure=failure,
            rules=rules,
            default_jira_project=default_jira_project,
        )
        assert len(matching_rules) == 1
        assert matching_rules[0].step == default_rule.step

        # Test a failure that matches an ignore rule (should not return anything)
        rules = [ignore_rule]
        matching_rules = Report.failure_matches_rule(
            self,
            failure=failure,
            rules=rules,
            default_jira_project=default_jira_project,
        )
        assert len(matching_rules) == 0

        # Test a failure that matches a rule
        rules = [match_rule]
        matching_rules = Report.failure_matches_rule(
            self,
            failure=failure,
            rules=rules,
            default_jira_project=default_jira_project,
        )
        assert len(matching_rules) == 1
        assert (matching_rules[0].step == match_rule.step) and (
            matching_rules[0].failure_type == match_rule.failure_type
        )

    def test_get_file_attachments(self, tmp_path) -> None:
        self.logger = logging.getLogger(
            __name__,
        )

        # Set up paths
        logs_dir = helpers._get_tmp_logs_dir(tmp_path=tmp_path)
        junit_dir = helpers._get_tmp_junit_dir(tmp_path=tmp_path)
        helpers._create_failed_step_junit(junit_dir=junit_dir)
        helpers._create_failed_step_pod(logs_dir=logs_dir)

        file_attachments = Report._get_file_attachments(
            self,
            step_name="failed-step",
            logs_dir=logs_dir,
            junit_dir=junit_dir,
        )
        assert len(file_attachments) > 0
        for file in file_attachments:
            assert os.path.exists(file)

    def test_get_issue_description(self) -> None:
        step_name = "test-step-name"
        classification = "test-classification"
        job_name = "test-job-name"
        build_id = "12345"

        compare_description = f"""
                    *Link:* https://prow.ci.openshift.org/view/gs/origin-ci-test/logs/{job_name}/{build_id}
                    *Build ID:* {build_id}
                    *Classification:* {classification}
                    *Failed Step:* {step_name}

                    Please see the link provided above along with the logs and junit files attached to the bug.

                    This bug was filed using [firewatch in OpenShift CI|https://github.com/CSPI-QE/firewatch)]
                """
        issue_description = Report._get_issue_description(
            self,
            step_name=step_name,
            classification=classification,
            job_name=job_name,
            build_id=build_id,
        )

        assert compare_description == issue_description
