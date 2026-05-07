from unittest.mock import patch

import pytest

from tests.unittests.objects.rule.rule_base_test import RuleBaseTest


class TestGetJiraWatchers(RuleBaseTest):
    def test_get_jira_watchers_defined(self):
        test_rule_dict = {"jira_watchers": ["a@b.com", "c@d.com"]}
        result = self.rule._get_jira_watchers(test_rule_dict)
        assert result == ["a@b.com", "c@d.com"]

    def test_get_jira_watchers_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_jira_watchers(test_rule_dict)
        assert result is None

    @patch.dict(
        "os.environ",
        {"FIREWATCH_DEFAULT_JIRA_WATCHERS": '["x@y.com"]'},
    )
    def test_get_jira_watchers_default(self):
        test_rule_dict = {"jira_watchers": ["!default", "a@b.com"]}
        result = self.rule._get_jira_watchers(test_rule_dict)
        assert result == ["a@b.com", "x@y.com"]

    def test_get_jira_watchers_bang_default_without_env_exits(self):
        with patch.dict("os.environ", {"FIREWATCH_DEFAULT_JIRA_WATCHERS": ""}):
            with pytest.raises(SystemExit) as exc_info:
                self.rule._get_jira_watchers({"jira_watchers": ["!default"]})
        assert exc_info.value.code == 1

    def test_get_jira_watchers_invalid_email(self):
        test_rule_dict = {"jira_watchers": ["not-an-email"]}
        with pytest.raises(SystemExit):
            self.rule._get_jira_watchers(test_rule_dict)

    def test_get_jira_watchers_non_list(self):
        test_rule_dict = {"jira_watchers": "a@b.com"}
        with pytest.raises(SystemExit):
            self.rule._get_jira_watchers(test_rule_dict)
