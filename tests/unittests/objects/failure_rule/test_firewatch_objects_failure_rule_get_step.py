import pytest

from cli.objects.failure_rule import FailureRule
from tests.unittests.objects.failure_rule.failure_rule_base_test import (
    FailureRuleBaseTest,
)


class TestGetStep(FailureRuleBaseTest):
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
