from unittest.mock import patch

import pytest

from cli.objects.rule import Rule
from tests.unittests.objects.rule.rule_base_test import RuleBaseTest


class TestGetJiraPriority(RuleBaseTest):
    def test_get_jira_priority_defined(self):
        test_rule_dict = {"jira_priority": "Major"}
        result = self.rule._get_jira_priority(test_rule_dict)
        assert result == "Major"

    def test_get_jira_priority_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_jira_priority(test_rule_dict)
        assert result is None

    @patch.dict("os.environ", {"FIREWATCH_DEFAULT_JIRA_PRIORITY": "Minor"})
    def test_get_jira_priority_default(self):
        test_rule_dict = {"jira_priority": "!default"}
        result = self.rule._get_jira_priority(test_rule_dict)
        assert result == "Minor"

    def test_get_jira_priority_invalid(self):
        test_rule_dict = {"jira_priority": "Invalid"}
        with pytest.raises(SystemExit):
            self.rule._get_jira_priority(test_rule_dict)

    def test_get_jira_priority_non_string(self):
        test_rule_dict = {"jira_priority": 123}
        with pytest.raises(SystemExit):
            self.rule._get_jira_priority(test_rule_dict)
