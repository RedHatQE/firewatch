import os
from unittest.mock import patch

import pytest

from cli.objects.rule import Rule
from tests.unittests.objects.rule.rule_base_test import RuleBaseTest


class TestGetJiraProject(RuleBaseTest):
    def test_get_jira_project_from_rule(self):
        test_rule_dict = {"jira_project": "TEST"}
        result = self.rule._get_jira_project(test_rule_dict)
        assert result == "TEST"

    @patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "DEFAULT"})
    def test_get_jira_project_from_env(self):
        test_rule_dict = {}
        result = self.rule._get_jira_project(test_rule_dict)
        assert result == "DEFAULT"

    @patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "DEFAULT"})
    def test_get_jira_project_is_default(self):
        test_rule_dict = {"jira_project": "!default"}
        project = self.rule._get_jira_project(test_rule_dict)
        assert project == "DEFAULT"

    def test_get_jira_project_invalid(self):
        test_rule_dict = {"jira_project": 123}  # non-string value
        with pytest.raises(SystemExit):
            self.rule._get_jira_project(test_rule_dict)
