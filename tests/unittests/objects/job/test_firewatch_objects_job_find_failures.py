import os
import tempfile
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from cli.objects.configuration import Configuration
from cli.objects.job import Job
from tests.unittests import helpers


class TestFindFailures(unittest.TestCase):
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
        self.mock_logger = patch("cli.objects.job.get_logger")
        self.mock_logger.start().return_value = MagicMock()
        self.mock_storage_client = patch(
            "cli.objects.job.storage.Client.create_anonymous_client",
        )
        self.mock_storage_client.start().return_value = MagicMock()
        self.mock_get_steps = patch.object(
            Job,
            "_get_steps",
            return_value=["step1", "step2"],
        )
        self.mock_get_steps.start()
        self.job = Job("job1", "job1_safe", "123", "bucket1", self.config)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.junit_dir = helpers._get_tmp_junit_dir(tmp_path=self.temp_dir.name)
        self.logs_dir = helpers._get_tmp_logs_dir(tmp_path=self.temp_dir.name)

    def tearDown(self):
        patch.stopall()

    def test_find_test_failures_no_pod_failures(self):
        helpers._create_failed_step_junit(junit_dir=self.junit_dir)
        failures = self.job._find_failures(
            junit_dir=self.junit_dir,
            logs_dir=self.logs_dir,
        )
        assert (
            failures[0].failure_type == "test_failure"
            and failures[0].step == "failed-step"
        )

    def test_find_pod_failures_no_test_failures(self):
        helpers._create_failed_step_pod(logs_dir=self.logs_dir)
        failures = self.job._find_failures(
            junit_dir=self.junit_dir,
            logs_dir=self.logs_dir,
        )
        assert (
            failures[0].failure_type == "pod_failure"
            and failures[0].step == "failed-step"
        )

    def test_find_all_failures(self):
        helpers._create_failed_step_pod(logs_dir=self.logs_dir)
        helpers._create_failed_step_junit(junit_dir=self.junit_dir)
        failures = self.job._find_failures(
            junit_dir=self.junit_dir,
            logs_dir=self.logs_dir,
        )
        assert (
            failures[0].failure_type == "test_failure"
            and failures[0].step == "failed-step"
        )

    def test_failures_no_failures(self):
        helpers._create_successful_step_pod(logs_dir=self.logs_dir)
        helpers._create_successful_step_junit(junit_dir=self.junit_dir)
        failures = self.job._find_failures(
            junit_dir=self.junit_dir,
            logs_dir=self.logs_dir,
        )
        assert not failures
