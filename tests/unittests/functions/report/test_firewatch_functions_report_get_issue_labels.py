import os
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from cli.objects.configuration import Configuration
from cli.objects.failure import Failure
from cli.objects.failure_rule import FailureRule
from cli.objects.job import Job
from cli.report import Report
from tests.unittests import helpers


class TestGetIssueLabels(unittest.TestCase):
    @patch("cli.objects.configuration.Jira")
    @patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "TEST"})
    @patch.dict(
        os.environ,
        {
            "FIREWATCH_CONFIG": '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}',
        },
    )
    def setUp(self, mock_jira):
        mock_jira.return_value = MagicMock()
        self.config = Configuration(mock_jira, False, False, False)
        self.mock_get_steps = patch.object(
            Job,
            "_get_steps",
            return_value=["step1", "step2"],
        )
        self.mock_get_steps.start()
        self.mock_logger = patch("cli.objects.job.get_logger")
        self.mock_logger.start().return_value = MagicMock()
        self.mock_storage_client = patch(
            "cli.objects.job.storage.Client.create_anonymous_client",
        )
        self.mock_storage_client.start().return_value = MagicMock()
        self.job = Job("job1", "job1_safe", "123", "bucket1", self.config)
        self.report = Report(self.config, self.job)

    def tearDown(self):
        patch.stopall()

    def test_get_issue_labels_no_additional_labels(self):
        labels = self.report._get_issue_labels(
            job_name=self.job.name,
            step_name="test-step-name",
            type="test_failure",
            jira_additional_labels=[],
        )

        assert len(labels) == 4
        assert self.job.name in labels
        assert "test-step-name" in labels
        assert "test_failure" in labels
        assert "firewatch" in labels

    def test_get_issue_labels_with_additional_labels(self):
        labels = self.report._get_issue_labels(
            job_name=self.job.name,
            step_name="test-step-name",
            type="test_failure",
            jira_additional_labels=["additional-label-1", "additional-label-2"],
        )

        assert len(labels) == 6
        assert self.job.name in labels
        assert "test-step-name" in labels
        assert "test_failure" in labels
        assert "firewatch" in labels
        assert "additional-label-1" and "additional-label-2" in labels

    def test_get_issue_labels_with_failed_test_name(self):
        labels = self.report._get_issue_labels(
            job_name=self.job.name,
            step_name="test-step-name",
            type="test_failure",
            failed_test_name="test-name",
            jira_additional_labels=[],
        )

        assert len(labels) == 5
        assert self.job.name in labels
        assert "test-step-name" in labels
        assert "test_failure" in labels
        assert "firewatch" in labels
        assert "test-name" in labels

    def test_get_issue_labels_with_duplicate_labels(self):
        labels = self.report._get_issue_labels(
            job_name=self.job.name,
            step_name="test-step-name",
            type="test_failure",
            jira_additional_labels=["test-step-name", "test_failure"],
        )

        assert len(labels) == 4
        assert self.job.name in labels
        assert "test-step-name" in labels
        assert "test_failure" in labels
        assert "firewatch" in labels
