import os
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from cli.objects.configuration import Configuration
from cli.objects.job import Job


class TestGetDownloadPath(unittest.TestCase):
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
        self.mock_exists = patch("os.path.exists")
        self.mock_exists.start()
        self.mock_mkdir = patch("os.mkdir")
        self.mock_mkdir.start()
        self.job = Job("job1", "job1_safe", "123", "bucket1", self.config)

    def tearDown(self):
        patch.stopall()

    def test_get_download_path_not_exists(self):
        self.mock_exists.return_value = False
        path = self.job._get_download_path("123")
        self.assertEqual(path, "/tmp/123")

    def test_get_download_path_exists(self):
        self.mock_exists.return_value = True
        path = self.job._get_download_path("123")
        self.assertEqual(path, "/tmp/123")
