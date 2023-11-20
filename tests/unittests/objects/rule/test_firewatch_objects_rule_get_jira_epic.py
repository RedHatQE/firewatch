from unittest.mock import MagicMock
from unittest.mock import patch

from cli.objects.rule import Rule


class TestRuleGetJiraEpic:
    def setup_method(self):
        self.rule = Rule(
            {
                "step": "dummy",
                "failure_type": "all",
                "classification": "test classification",
                "jira_project": "TEST",
            },
        )
        self.rule.logger = MagicMock()

    def test_get_jira_epic_defined(self):
        test_rule_dict = {"jira_epic": "TEST-1234"}
        result = self.rule._get_jira_epic(test_rule_dict)
        assert result == "TEST-1234"
        self.rule.logger.error.assert_not_called()

    def test_get_jira_epic_undefined(self):
        test_rule_dict = {}
        result = self.rule._get_jira_epic(test_rule_dict)
        assert result is None
        self.rule.logger.error.assert_not_called()

    @patch.dict("os.environ", {"FIREWATCH_DEFAULT_JIRA_EPIC": "DEFAULT-EPIC"})
    def test_get_jira_epic_default(self):
        test_rule_dict = {"jira_epic": "!default"}
        result = self.rule._get_jira_epic(test_rule_dict)
        assert result == "DEFAULT-EPIC"
        self.rule.logger.error.assert_not_called()
