import os
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from cli.objects.configuration import Configuration


@patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "TEST"})
@patch.dict(
    os.environ,
    {
        "FIREWATCH_CONFIG": '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}',
    },
)
class TestConfiguration(unittest.TestCase):
    @patch("cli.objects.configuration.Jira")
    def setUp(self, mock_jira):
        self.mock_jira = mock_jira
        mock_jira.return_value = MagicMock()

    def tearDown(self):
        patch.stopall()

    def test_configuration_initializes_with_valid_input(self):
        config = Configuration(
            jira=self.mock_jira,
            fail_with_test_failures=True,
            keep_job_dir=True,
            verbose_test_failure_reporting=True,
            verbose_test_failure_reporting_ticket_limit=10,
            config_file_path=None,
        )
        assert config.fail_with_test_failures
        assert config.keep_job_dir
        assert config.verbose_test_failure_reporting
        assert config.verbose_test_failure_reporting_ticket_limit == 10
