import os
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from cli.objects.configuration import Configuration


@patch.dict(
    os.environ,
    {
        "FIREWATCH_CONFIG": '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}'
    },
)
class TestGetDefaultJiraProject(unittest.TestCase):
    @patch("cli.objects.configuration.Jira")
    def setUp(self, mock_jira):
        self.mock_jira = mock_jira
        mock_jira.return_value = MagicMock()

    def tearDown(self):
        patch.stopall()

    @patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "TEST"})
    def test_configuration_gets_default_jira_project_with_valid_env_var(self):
        config = Configuration(self.mock_jira, True, True, True, 10, None)
        assert config._get_default_jira_project() == "TEST"

    def test_configuration_gets_default_jira_project_with_no_env_var(self):
        if "FIREWATCH_DEFAULT_JIRA_PROJECT" in os.environ:
            del os.environ["FIREWATCH_DEFAULT_JIRA_PROJECT"]
        with self.assertRaises(SystemExit):
            Configuration(self.mock_jira, True, True, True, 10, None)
