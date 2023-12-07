import pytest

from cli.objects.failure_rule import FailureRule
from tests.unittests.objects.failure_rule.failure_rule_base_test import (
    FailureRuleBaseTest,
)


class TestGetClassification(FailureRuleBaseTest):
    def test_get_classification_valid(self):
        test_rule_dict = {"classification": "valid_classification"}
        classification = self.rule._get_classification(test_rule_dict)
        assert classification == "valid_classification"

    def test_get_classification_invalid(self):
        test_rule_dict = {"classification": 123}  # non-string value
        with pytest.raises(SystemExit):
            self.rule._get_classification(test_rule_dict)
        self.mock_logger.error.assert_called_once()

    def test_get_classification_missing(self):
        test_rule_dict = {}
        with pytest.raises(SystemExit):
            self.rule._get_classification(test_rule_dict)
        self.mock_logger.error.assert_called_once()
