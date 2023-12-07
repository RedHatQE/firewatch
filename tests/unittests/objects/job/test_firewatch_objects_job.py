import os
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from cli.objects.configuration import Configuration
from cli.objects.job import Job


class TestJob(unittest.TestCase):
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
        self.mock_get_steps = patch.object(
            Job, "_get_steps", return_value=["step1", "step2"]
        )
        self.mock_get_steps.start()
        self.mock_logger = patch("cli.objects.job.get_logger")
        self.mock_logger.start().return_value = MagicMock()
        self.mock_storage_client = patch(
            "cli.objects.job.storage.Client.create_anonymous_client"
        )
        self.mock_storage_client.start().return_value = MagicMock()
        self.job = Job("job1", "job1_safe", "123", "bucket1", self.config)

    def tearDown(self):
        patch.stopall()

    def test_initialization_with_valid_parameters(self):
        self.assertEqual(self.job.name, "job1")
        self.assertEqual(self.job.name_safe, "job1_safe")
        self.assertEqual(self.job.build_id, "123")
        self.assertEqual(self.job.gcs_bucket, "bucket1")
