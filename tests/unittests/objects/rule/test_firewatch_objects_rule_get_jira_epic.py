from unittest.mock import patch

from tests.unittests.objects.rule.rule_base_test import RuleBaseTest


class TestGetJiraEpic(RuleBaseTest):
    def test_get_jira_epic_defined(self):
        test_rule_dict = {"jira_epic": "TEST-1234"}
        result = self.rule._get_jira_epic(test_rule_dict)
        assert result == "TEST-1234"

    def test_get_jira_epic_undefined(self):
        test_rule_dict = {}
        result = self.rule._get_jira_epic(test_rule_dict)
        assert result is None

    @patch.dict("os.environ", {"FIREWATCH_DEFAULT_JIRA_EPIC": "DEFAULT-EPIC"})
    def test_get_jira_epic_default(self):
        test_rule_dict = {"jira_epic": "!default"}
        result = self.rule._get_jira_epic(test_rule_dict)
        assert result == "DEFAULT-EPIC"
