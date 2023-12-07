import os
import unittest
from unittest.mock import patch, mock_open, MagicMock

from cli.objects.configuration import Configuration
from cli.objects.failure import Failure
from cli.objects.failure_rule import FailureRule
from cli.objects.job import Job
from cli.report import Report
import tempfile

from tests.unittests import helpers


class TestGetFileAttachments(unittest.TestCase):

    @patch('cli.objects.configuration.Jira')
    @patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "TEST"})
    @patch.dict(os.environ, {"FIREWATCH_CONFIG": '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}'})
    def setUp(self, mock_jira):
        mock_jira.return_value = MagicMock()
        self.config = Configuration(mock_jira, False, False, False)
        self.mock_get_steps = patch.object(Job, '_get_steps', return_value=['step1', 'step2'])
        self.mock_get_steps.start()
        self.mock_logger = patch('cli.objects.job.get_logger')
        self.mock_logger.start().return_value = MagicMock()
        self.mock_storage_client = patch('cli.objects.job.storage.Client.create_anonymous_client')
        self.mock_storage_client.start().return_value = MagicMock()
        self.job = Job('job1', 'job1_safe', '123', 'bucket1', self.config)
        self.report = Report(self.config, self.job)

    def tearDown(self):
        patch.stopall()

    def test_get_file_attachments(self):
        with tempfile.TemporaryDirectory() as tmp_path:
            logs_dir = helpers._get_tmp_logs_dir(tmp_path=tmp_path)
            junit_dir = helpers._get_tmp_junit_dir(tmp_path=tmp_path)
            helpers._create_failed_step_junit(junit_dir=junit_dir)
            helpers._create_failed_step_pod(logs_dir=logs_dir)

            file_attachments = self.report._get_file_attachments(
                step_name="failed-step",
                logs_dir=logs_dir,
                junit_dir=junit_dir,
            )
            assert len(file_attachments) > 0
            for file in file_attachments:
                assert os.path.exists(file)
