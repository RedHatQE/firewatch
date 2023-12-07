import os
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from cli.objects.configuration import Configuration
from cli.objects.job import Job


class JobBaseTest(unittest.TestCase):
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

    def tearDown(self):
        patch.stopall()
