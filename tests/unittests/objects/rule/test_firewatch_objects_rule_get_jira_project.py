import os
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from cli.objects.rule import Rule


class TestGetJiraProject(unittest.TestCase):
    def setUp(self):
        self.rule = Rule(
            rule_dict={
                "jira_project": "TEST",
            },
        )
        self.mock_logger = patch('cli.objects.job.get_logger')
        self.mock_logger.start().return_value = MagicMock()

    def tearDown(self):
        patch.stopall()

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

    @patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "DEFAULT"})
    def test_get_jira_project_is_default(self):
        test_rule_dict = {"jira_project": "!default"}
        project = self.rule._get_jira_project(test_rule_dict)
        assert project == "DEFAULT"

    def test_get_jira_project_invalid(self):
        test_rule_dict = {"jira_project": 123}  # non-string value
        with pytest.raises(SystemExit):
            self.rule._get_jira_project(test_rule_dict)
        self.rule.logger.error.assert_called_once()
