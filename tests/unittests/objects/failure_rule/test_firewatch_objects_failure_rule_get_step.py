from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cli.objects.failure_rule import FailureRule


class TestRuleGetStep:
    @patch("cli.objects.rule.get_logger")
    def setup_method(self, method, mock_get_logger):
        self.mock_logger = MagicMock()
        mock_get_logger.return_value = self.mock_logger
        self.rule = FailureRule(
            rule_dict={
                "step": "dummy",
                "failure_type": "all",
                "classification": "test classification",
                "jira_project": "TEST",
            }
        )

    def test_get_step_valid(self):
        test_rule_dict = {"step": "test-step-name"}
        step = self.rule._get_step(test_rule_dict)
        assert step == "test-step-name"

    def test_get_step_missing(self):
        test_rule_dict = {}
        with pytest.raises(SystemExit):
            self.rule._get_step(test_rule_dict)
        self.mock_logger.error.assert_called_once_with(
            'Unable to find value for "step" in firewatch rule: "{}"',
        )

    def test_get_step_not_string(self):
        test_rule_dict = {"step": 123}
        with pytest.raises(SystemExit):
            self.rule._get_step(test_rule_dict)
        self.mock_logger.error.assert_called_once_with(
            'Value for "step" is not a string in firewatch rule: "{\'step\': 123}"',
        )
