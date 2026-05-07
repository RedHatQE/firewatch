from unittest.mock import patch

import pytest

from tests.unittests.objects.rule.rule_base_test import RuleBaseTest


class TestGetJiraAdditionalAssignees(RuleBaseTest):
    def test_get_jira_additional_assignees_defined(self):
        test_rule_dict = {"jira_additional_assignees": ["a@b.com", "c@d.com"]}
        result = self.rule._get_jira_additional_assignees(test_rule_dict)
        assert result == ["a@b.com", "c@d.com"]

    def test_get_jira_additional_assignees_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_jira_additional_assignees(test_rule_dict)
        assert result is None

    @patch.dict(
        "os.environ",
        {"FIREWATCH_DEFAULT_JIRA_ADDITIONAL_ASSIGNEES": '["x@y.com"]'},
    )
    def test_get_jira_additional_assignees_default(self):
        test_rule_dict = {"jira_additional_assignees": ["!default", "a@b.com"]}
        result = self.rule._get_jira_additional_assignees(test_rule_dict)
        assert result == ["a@b.com", "x@y.com"]

    def test_get_jira_additional_assignees_bang_default_without_env_exits(self):
        with patch.dict("os.environ", {"FIREWATCH_DEFAULT_JIRA_ADDITIONAL_ASSIGNEES": ""}):
            with pytest.raises(SystemExit) as exc_info:
                self.rule._get_jira_additional_assignees({"jira_additional_assignees": ["!default"]})
        assert exc_info.value.code == 1

    def test_get_jira_additional_assignees_invalid_email(self):
        test_rule_dict = {"jira_additional_assignees": ["not-an-email"]}
        with pytest.raises(SystemExit):
            self.rule._get_jira_additional_assignees(test_rule_dict)

    def test_get_jira_additional_assignees_non_list(self):
        test_rule_dict = {"jira_additional_assignees": "a@b.com"}
        with pytest.raises(SystemExit):
            self.rule._get_jira_additional_assignees(test_rule_dict)
