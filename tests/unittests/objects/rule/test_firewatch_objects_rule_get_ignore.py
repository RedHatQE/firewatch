import pytest

from cli.objects.rule import Rule


class TestRuleGetIgnore:
    def setup_method(self):
        self.rule = Rule(
            rule_dict={
                "step": "dummy",
                "failure_type": "all",
                "classification": "test classification",
                "jira_project": "TEST",
            },
            rule_type="failure",
        )

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
