import os
from unittest.mock import patch

from src.objects.configuration import Configuration
from tests.unittests.objects.configuration.configuration_base_test import (
    ConfigurationBaseTest,
)


@patch.dict(
    os.environ,
    {
        "FIREWATCH_CONFIG": '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}',
    },
)
class TestGetDefaultJiraProject(ConfigurationBaseTest):
    @patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "TEST"})
    def test_configuration_gets_default_jira_project_with_valid_env_var(self):
        config = Configuration(self.mock_jira, True, True, True, 10, None)
        assert config._get_default_jira_project() == "TEST"

    def test_configuration_gets_default_jira_project_with_no_env_var(self):
        if "FIREWATCH_DEFAULT_JIRA_PROJECT" in os.environ:
            del os.environ["FIREWATCH_DEFAULT_JIRA_PROJECT"]
        with self.assertRaises(SystemExit):
            Configuration(self.mock_jira, True, True, True, 10, None)
