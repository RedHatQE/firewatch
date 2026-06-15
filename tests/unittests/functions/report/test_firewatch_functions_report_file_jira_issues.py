import json
import os
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from src.objects.configuration import Configuration
from src.objects.failure import Failure
from src.objects.job import Job
from src.report.report import Report
from tests.unittests.functions.report.report_base_test import ReportBaseTest

_BAREBONES_RULE_CONFIG = json.dumps({
    "failure_rules": [
        {
            "step": "barebones-step",
            "failure_type": "pod_failure",
            "classification": "barebones",
            "jira_watchers": ["w@test.com"],
            "jira_additional_assignees": ["aa@test.com"],
            "slack_channel": "#my-channel",
            "slack_user": "user@redhat.com",
        },
    ],
})


class TestFileJiraIssues(ReportBaseTest):
    def test_file_jira_issues_with_no_failures(self):
        report = Report(self.config, self.job)
        result, bugs_updated = report.file_jira_issues([], self.config, self.job)
        self.assertEqual(result, [])
        self.assertEqual(bugs_updated, [])

    def test_file_jira_issues_with_failures(self):
        failures = [Failure(failed_step="step1", failure_type="pod_failure")]

        report = Report(self.config, self.job)
        result, bugs_updated = report.file_jira_issues(failures, self.config, self.job)
        self.assertNotEqual(result, [])
        self.assertEqual(bugs_updated, [])


class TestBarebonesRuleEmitsJiraTicketFields(unittest.TestCase):
    """One failure matching one rule; assert create_issue receives derived Jira fields."""

    @patch("src.objects.configuration.Jira")
    @patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "TEST"})
    @patch.dict(os.environ, {"FIREWATCH_CONFIG": _BAREBONES_RULE_CONFIG})
    def setUp(self, mock_jira):
        mock_jira.return_value = MagicMock()
        self.config = Configuration(
            jira=mock_jira,
            fail_with_test_failures=False,
            fail_with_pod_failures=False,
            keep_job_dir=True,
            verbose_test_failure_reporting=False,
        )
        self.mock_get_steps = patch.object(Job, "_get_steps", return_value=["barebones-step"])
        self.mock_get_steps.start()
        self.mock_logger = patch("src.objects.job.get_logger")
        self.mock_logger.start().return_value = MagicMock()
        self.mock_storage_client = patch("src.objects.job.storage.Client.create_anonymous_client")
        self.mock_storage_client.start().return_value = MagicMock()
        self.job = Job(
            name="barebones-job",
            name_safe="barebones-job_safe",
            build_id="1",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )

    def tearDown(self):
        patch.stopall()

    def test_matching_failure_passes_watchers_assignees_and_slack_labels(self):
        failures = [Failure(failed_step="barebones-step", failure_type="pod_failure")]
        report = Report(self.config, self.job)
        report.file_jira_issues(failures, self.config, self.job)

        self.config.jira.create_issue.assert_called_once()
        _, kwargs = self.config.jira.create_issue.call_args
        self.assertEqual(kwargs.get("watchers"), ["w@test.com"])
        self.assertEqual(kwargs.get("additional_assignees"), ["aa@test.com"])
        labels = kwargs.get("labels", [])
        self.assertIn("slack-channel:my-channel", labels)
        self.assertIn("slack-user:user", labels)
