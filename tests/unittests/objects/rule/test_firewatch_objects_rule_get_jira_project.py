import os
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cli.objects.rule import Rule


class TestRuleGetJiraProject:
    def setup_method(self):
        self.rule = Rule(
            rule_dict={
                "jira_project": "TEST",
            }
        )
        self.rule.logger = MagicMock()

    def test_get_jira_project_from_rule(self):
        test_rule_dict = {"jira_project": "TEST"}
        result = self.rule._get_jira_project(test_rule_dict)
        assert result == "TEST"
        self.rule.logger.error.assert_not_called()

    @patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "DEFAULT"})
    def test_get_jira_project_from_env(self):
        test_rule_dict = {}
        result = self.rule._get_jira_project(test_rule_dict)
        assert result == "DEFAULT"
        self.rule.logger.error.assert_not_called()

    def test_get_jira_project_none(self):
        test_rule_dict = {}
        with pytest.raises(SystemExit):
            self.rule._get_jira_project(test_rule_dict)
        self.rule.logger.error.assert_called_once()

    def test_get_jira_project_invalid(self):
        test_rule_dict = {"jira_project": 123}  # non-string value
        with pytest.raises(SystemExit):
            self.rule._get_jira_project(test_rule_dict)
        self.rule.logger.error.assert_called_once()
