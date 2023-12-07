import pytest

from tests.unittests.objects.failure_rule.failure_rule_base_test import (
    FailureRuleBaseTest,
)


class TestGetGroupPriority(FailureRuleBaseTest):
    def test_get_group_priority_defined(self):
        test_rule_dict = {"group": {"priority": 1}}
        result = self.rule._get_group_priority(test_rule_dict)
        assert result == 1

    def test_get_group_priority_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_group_priority(test_rule_dict)
        assert result is None

    def test_get_group_priority_not_dict(self):
        test_rule_dict = {"group": "not_a_dict"}
        with pytest.raises(SystemExit):
            self.rule._get_group_priority(test_rule_dict)

    def test_get_group_priority_non_integer(self):
        test_rule_dict = {"group": {"priority": "not_an_integer"}}
        with pytest.raises(SystemExit):
            self.rule._get_group_priority(test_rule_dict)
