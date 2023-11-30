from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cli.objects.failure_rule import FailureRule


class TestGetRuleClassification:
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
            },
        )

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
