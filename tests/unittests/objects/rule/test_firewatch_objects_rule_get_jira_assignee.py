from unittest.mock import patch

import pytest

from cli.objects.rule import Rule


class TestRuleGetJiraAssignee:
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

    def test_get_jira_assignee_defined(self):
        test_rule_dict = {"jira_assignee": "test@example.com"}
        result = self.rule._get_jira_assignee(test_rule_dict)
        assert result == "test@example.com"

    def test_get_jira_assignee_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_jira_assignee(test_rule_dict)
        assert result is None

    @patch.dict(
        "os.environ",
        {"FIREWATCH_DEFAULT_JIRA_ASSIGNEE": "default@example.com"},
    )
    def test_get_jira_assignee_default(self):
        test_rule_dict = {"jira_assignee": "!default"}
        result = self.rule._get_jira_assignee(test_rule_dict)
        assert result == "default@example.com"

    def test_get_jira_assignee_invalid_email(self):
        test_rule_dict = {"jira_assignee": "invalid_email"}
        with pytest.raises(SystemExit):
            self.rule._get_jira_assignee(test_rule_dict)

    def test_get_jira_assignee_non_string(self):
        test_rule_dict = {"jira_assignee": 123}
        with pytest.raises(SystemExit):
            self.rule._get_jira_assignee(test_rule_dict)
