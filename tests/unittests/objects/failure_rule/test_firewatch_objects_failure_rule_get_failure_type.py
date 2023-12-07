import pytest

from cli.objects.failure_rule import FailureRule
from tests.unittests.objects.failure_rule.failure_rule_base_test import (
    FailureRuleBaseTest,
)


class TestGetFailureType(FailureRuleBaseTest):
    def test_get_failure_type_valid(self):
        test_rule_dict = {"failure_type": "pod_failure"}
        failure_type = self.rule._get_failure_type(test_rule_dict)
        assert failure_type == "pod_failure"

    def test_get_failure_type_invalid(self):
        test_rule_dict = {"failure_type": "invalid_failure_type"}
        with pytest.raises(SystemExit):
            self.rule._get_failure_type(test_rule_dict)
        self.mock_logger.error.assert_called_once()

    def test_get_failure_type_missing(self):
        test_rule_dict = {}
        with pytest.raises(SystemExit):
            self.rule._get_failure_type(test_rule_dict)
        self.mock_logger.error.assert_called_once()
