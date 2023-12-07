import os
import unittest

from unittest.mock import MagicMock, patch

from cli.objects.configuration import Configuration

@patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "TEST"})
class TestGetSuccessRules(unittest.TestCase):

        @patch('cli.objects.configuration.Jira')
        def setUp(self, mock_jira):
            self.mock_jira = mock_jira
            mock_jira.return_value = MagicMock()

        def tearDown(self):
            patch.stopall()

        @patch.dict(os.environ, {"FIREWATCH_CONFIG": '{"success_rules": [{"jira_project": "PROJECT", "jira_epic": "PROJECT-123"}], "failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}'})
        def test_configuration_gets_success_rules_with_valid_input(self):
            config = Configuration(self.mock_jira, False, False, False)
            success_rules = config._get_success_rules(config.config_data.get("success_rules"))
            assert len(success_rules) == 1
            assert success_rules[0].jira_project == "PROJECT"
            assert success_rules[0].jira_epic == "PROJECT-123"

        @patch.dict(os.environ, {"FIREWATCH_CONFIG": '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}'})
        def test_configuration_gets_success_rules_with_no_rules(self):
            config = Configuration(self.mock_jira, False, False, False)
            success_rules = config._get_success_rules(config.config_data.get("success_rules"))
            assert success_rules is None
