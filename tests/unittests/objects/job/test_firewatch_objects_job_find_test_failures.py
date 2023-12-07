import os
import tempfile
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from cli.objects.configuration import Configuration
from cli.objects.job import Job
from tests.unittests import helpers


class TestFindTestFailures(unittest.TestCase):
    @patch("cli.objects.configuration.Jira")
    @patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "TEST"})
    @patch.dict(
        os.environ,
        {
            "FIREWATCH_CONFIG": '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}'
        },
    )
    def setUp(self, mock_jira):
        mock_jira.return_value = MagicMock()
        self.config = Configuration(mock_jira, False, False, False)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.junit_dir = helpers._get_tmp_junit_dir(tmp_path=self.temp_dir.name)
        self.mock_logger = patch("cli.objects.job.get_logger")
        self.mock_logger.start().return_value = MagicMock()
        self.mock_storage_client = patch(
            "cli.objects.job.storage.Client.create_anonymous_client"
        )
        self.mock_storage_client.start().return_value = MagicMock()
        self.mock_get_steps = patch.object(
            Job, "_get_steps", return_value=["step1", "step2"]
        )
        self.mock_get_steps.start()
        self.job = Job("job1", "job1_safe", "123", "bucket1", self.config)

    def tearDown(self):
        patch.stopall()

    def test_find_test_failures_with_failures(self):
        helpers._create_failed_step_junit(junit_dir=self.junit_dir)
        failures = self.job._find_test_failures(junit_dir=self.junit_dir)
        assert len(failures) == 1

    def test_find_test_failures_without_failures(self):
        helpers._create_successful_step_junit(junit_dir=self.junit_dir)
        failures = self.job._find_test_failures(junit_dir=self.junit_dir)
        assert len(failures) == 0
