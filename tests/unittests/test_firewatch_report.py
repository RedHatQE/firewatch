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
import json
import logging
import os

from google.cloud import storage

from cli.report.report import Report


class TestFirewatchReport:
    logger = logging.getLogger(__name__)

    def test_is_rehearsal_function(self) -> None:
        self.build_id = "TEST_BUILD_ID"
        self.logger = logging.getLogger(__name__)

        self.job_name = "rehearse-39134-periodic-ci-oadp-qe-oadp-qe-automation-main-oadp1.1-ocp4.13-lp-interop-oadp-interop-aws"
        assert Report.is_rehearsal(self)

        self.job_name = "periodic-ci-oadp-qe-oadp-qe-automation-main-oadp1.1-ocp4.13-lp-interop-oadp-interop-aws"
        assert not Report.is_rehearsal(self)

    def test_has_test_failures(self) -> None:
        self.failures = [
            {"step": "test_step", "failure_type": "test_failure"},
            {"step": "test_step", "failure_type": "pod_failure"},
        ]

        assert Report.has_test_failures(self)

        self.failures = [
            {"step": "test_step", "failure_type": "pod_failure"},
            {"step": "test_step", "failure_type": "pod_failure"},
        ]

        assert not Report.has_test_failures(self)

    def test_download_logs(self, tmp_path) -> None:
        # Set required variables
        self.download_path = tmp_path
        self.gcs_bucket = "origin-ci-test"
        self.storage_client = storage.Client.create_anonymous_client()
        self.bucket = self.storage_client.bucket(self.gcs_bucket)
        self.steps: list[str] = []

        # Some random job to test with
        self.job_name = "periodic-ci-windup-windup-ui-tests-v1.0-mtr-ocp4.13-lp-interop-mtr-interop-aws"
        self.job_name_safe = "mtr-interop-aws"
        self.build_id = "1658302496205967360"

        assert os.listdir(Report.download_logs(self))

    def test_download_junit(self, tmp_path) -> None:
        # Set required variables
        self.download_path = tmp_path
        self.gcs_bucket = "origin-ci-test"
        self.storage_client = storage.Client.create_anonymous_client()
        self.bucket = self.storage_client.bucket(self.gcs_bucket)
        self.steps: list[str] = []

        # Some random job to test with
        self.job_name = "periodic-ci-windup-windup-ui-tests-v1.0-mtr-ocp4.13-lp-interop-mtr-interop-aws"
        self.job_name_safe = "mtr-interop-aws"
        self.build_id = "1658302496205967360"

        assert os.listdir(Report.download_junit(self))

    def test_get_file_attachments(self, tmp_path) -> None:
        # Set required variables
        self.download_path = tmp_path
        self.gcs_bucket = "origin-ci-test"
        self.storage_client = storage.Client.create_anonymous_client()
        self.bucket = self.storage_client.bucket(self.gcs_bucket)
        self.steps: list[str] = []

        # Some random job to test with
        self.job_name = "periodic-ci-windup-windup-ui-tests-v1.0-mtr-ocp4.13-lp-interop-mtr-interop-aws"
        self.job_name_safe = "mtr-interop-aws"
        self.build_id = "1658302496205967360"

        # Download junit files and logs
        self.logs_dir = Report.download_logs(self)
        self.junit_dir = Report.download_junit(self)

        # Step Name
        step_name = "mtr-tests-ui"

        attachments = Report.get_file_attachments(self, step_name)

        assert len(attachments) > 0

        for attachment in attachments:
            assert os.path.exists(attachment)

    def test_find_failures(self, tmp_path) -> None:
        # Set required variables
        self.logger = logging.getLogger(__name__)
        self.download_path = tmp_path
        self.gcs_bucket = "origin-ci-test"
        self.storage_client = storage.Client.create_anonymous_client()
        self.bucket = self.storage_client.bucket(self.gcs_bucket)
        self.steps: list[str] = []

        # Some random job to test with
        self.job_name = "periodic-ci-oadp-qe-oadp-qe-automation-main-oadp1.1-ocp4.13-lp-interop-oadp-interop-aws"
        self.job_name_safe = "oadp-interop-aws"
        self.build_id = "1655452745290747904"

        # Download junit files and logs
        self.logs_dir = Report.download_logs(self)
        self.junit_dir = Report.download_junit(self)

        assert len(Report.find_failures(self)) > 0

    def test_build_issue_description(self) -> None:
        self.job_name = "periodic-ci-oadp-qe-oadp-qe-automation-main-oadp1.1-ocp4.13-lp-interop-oadp-interop-aws"
        self.job_name_safe = "oadp-interop-aws"
        self.build_id = "1655452745290747904"
        classification = "test-classification"
        step_name = "test-step-name"

        assert Report.build_issue_description(self, step_name, classification)

    def test_failure_matches_rule(self) -> None:
        # Test when a match is found
        rules = json.loads(
            '[{"step": "*test*", "failure_type": "test_failure", "classification": "Test failures", "jira_project": "INTEROP"}]',
        )
        failure = {"step": "some-test-step", "failure_type": "test_failure"}
        rule_matches = Report.failure_matches_rule(
            self,
            failure=failure,
            rules=rules,
            default_jira_project="INTEROP",
        )
        assert (
            rule_matches[0]["step"] == "*test*"
            and rule_matches[0]["failure_type"] == "test_failure"
        )

        # Test when a match is not found
        rules = json.loads(
            '[{"step": "*test*", "failure_type": "test_failure", "classification": "Test failures", "jira_project": "INTEROP"}]',
        )
        failure = {"step": "some-infra-step", "failure_type": "pod_failure"}
        rule_matches = Report.failure_matches_rule(
            self,
            failure=failure,
            rules=rules,
            default_jira_project="INTEROP",
        )
        assert (
            rule_matches[0]["step"] == "!none"
            and rule_matches[0]["failure_type"] == "!none"
            and rule_matches[0]["jira_project"] == "INTEROP"
        )

        # Test when the rule's "test_failure" definition is "all"
        rules = json.loads(
            '[{"step": "*test*", "failure_type": "all", "classification": "General failures", "jira_project": "INTEROP"}]',
        )
        failure = {"step": "some-test-step", "failure_type": "test_failure"}
        rule_matches = Report.failure_matches_rule(
            self,
            failure=failure,
            rules=rules,
            default_jira_project="INTEROP",
        )
        assert (
            rule_matches[0]["step"] == "*test*"
            and rule_matches[0]["failure_type"] == "all"
            and rule_matches[0]["jira_project"] == "INTEROP"
        )
