import os
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from src.objects.configuration import Configuration
from src.objects.job import Job
from src.report.report import Report


class ReportBaseTest(unittest.TestCase):
    @patch("src.objects.configuration.Jira")
    @patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "TEST"})
    @patch.dict(
        os.environ,
        {
            "FIREWATCH_CONFIG": '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}',
        },
    )
    def setUp(self, mock_jira):
        mock_jira.return_value = MagicMock()
        self.config = Configuration(mock_jira, False, True, False)
        self.mock_get_steps = patch.object(
            Job,
            "_get_steps",
            return_value=["step1", "step2"],
        )
        self.mock_get_steps.start()
        self.mock_logger = patch("src.objects.job.get_logger")
        self.mock_logger.start().return_value = MagicMock()
        self.mock_storage_client = patch(
            "src.objects.job.storage.Client.create_anonymous_client",
        )
        self.mock_storage_client.start().return_value = MagicMock()
        self.job = Job("job1", "job1_safe", "123", "bucket1", self.config)
        self.report = Report(self.config, self.job)

    def tearDown(self):
        patch.stopall()
