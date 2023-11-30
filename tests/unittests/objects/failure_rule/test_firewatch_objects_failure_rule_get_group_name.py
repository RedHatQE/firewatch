import pytest

from cli.objects.failure_rule import FailureRule


class TestRuleGetGroupName:
    def setup_method(self):
        self.rule = FailureRule(
            rule_dict={
                "step": "dummy",
                "failure_type": "all",
                "classification": "test classification",
                "jira_project": "TEST",
            }
        )

    def test_get_group_name_defined(self):
        test_rule_dict = {"group": {"name": "test_group"}}
        result = self.rule._get_group_name(test_rule_dict)
        assert result == "test_group"

    def test_get_group_name_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_group_name(test_rule_dict)
        assert result is None

    def test_get_group_name_not_dict(self):
        test_rule_dict = {"group": "not_a_dict"}
        with pytest.raises(SystemExit):
            self.rule._get_group_name(test_rule_dict)

    def test_get_group_name_non_string(self):
        test_rule_dict = {"group": {"name": 123}}
        with pytest.raises(SystemExit):
            self.rule._get_group_name(test_rule_dict)
