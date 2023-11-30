from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cli.objects.rule import Rule


class TestRuleGetJiraComponent:
    def setup_method(self):
        self.rule = Rule(
            rule_dict={
                "jira_project": "TEST",
            }
        )
        self.rule.logger = MagicMock()

    def test_get_jira_component_defined(self):
        test_rule_dict = {"jira_component": ["TEST-COMPONENT"]}
        result = self.rule._get_jira_component(test_rule_dict)
        assert result == ["TEST-COMPONENT"]
        self.rule.logger.error.assert_not_called()

    def test_get_jira_component_undefined(self):
        test_rule_dict = {}
        result = self.rule._get_jira_component(test_rule_dict)
        assert result is None
        self.rule.logger.error.assert_not_called()

    @patch.dict(
        "os.environ",
        {
            "FIREWATCH_DEFAULT_JIRA_COMPONENT": '["DEFAULT-COMPONENT", "ANOTHER-COMPONENT"]',
        },
    )
    def test_get_jira_component_default(self):
        test_rule_dict = {"jira_component": ["!default"]}
        result = self.rule._get_jira_component(test_rule_dict)
        assert result[0] == "DEFAULT-COMPONENT"
        self.rule.logger.error.assert_not_called()

    def test_get_jira_component_not_list(self):
        test_rule_dict = {"jira_component": "TEST-COMPONENT"}
        with pytest.raises(SystemExit):
            self.rule._get_jira_component(test_rule_dict)
        self.rule.logger.error.assert_called_once()
