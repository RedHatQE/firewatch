import os
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from cli.objects.configuration import Configuration


@patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "TEST"})
class TestGetFailureRules(unittest.TestCase):
    @patch("cli.objects.configuration.Jira")
    def setUp(self, mock_jira):
        self.mock_jira = mock_jira
        mock_jira.return_value = MagicMock()

    def tearDown(self):
        patch.stopall()

    @patch.dict(
        os.environ,
        {
            "FIREWATCH_CONFIG": '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}'
        },
    )
    def test_configuration_gets_failure_rules_with_valid_input(self):
        config = Configuration(self.mock_jira, False, False, False)
        failure_rules = config._get_failure_rules(
            config.config_data.get("failure_rules")
        )
        assert len(failure_rules) == 1
        assert failure_rules[0].step == "step1"
        assert failure_rules[0].failure_type == "pod_failure"
        assert failure_rules[0].classification == "none"
