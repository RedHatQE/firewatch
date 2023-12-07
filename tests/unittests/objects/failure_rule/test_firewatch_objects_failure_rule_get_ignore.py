import pytest

from cli.objects.failure_rule import FailureRule
from tests.unittests.objects.failure_rule.failure_rule_base_test import (
    FailureRuleBaseTest,
)


class TestGetIgnore(FailureRuleBaseTest):
    def test_get_ignore_defined_boolean(self):
        test_rule_dict = {"ignore": True}
        result = self.rule._get_ignore(test_rule_dict)
        assert result is True

    def test_get_ignore_defined_string(self):
        test_rule_dict = {"ignore": "True"}
        result = self.rule._get_ignore(test_rule_dict)
        assert result is True

    def test_get_ignore_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_ignore(test_rule_dict)
        assert result is False

    def test_get_ignore_non_boolean_string(self):
        test_rule_dict = {"ignore": 123}
        with pytest.raises(SystemExit):
            self.rule._get_ignore(test_rule_dict)
