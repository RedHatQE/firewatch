import unittest
from unittest.mock import patch, MagicMock

import pytest

from cli.objects.rule import Rule


class TestGetJiraSecurityLevel(unittest.TestCase):
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

    def test_get_jira_security_level_defined(self):
        test_rule_dict = {"jira_security_level": "High"}
        result = self.rule._get_jira_security_level(test_rule_dict)
        assert result == "High"

    def test_get_jira_security_level_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_jira_security_level(test_rule_dict)
        assert result is None

    @patch.dict("os.environ", {"FIREWATCH_DEFAULT_JIRA_SECURITY_LEVEL": "Medium"})
    def test_get_jira_security_level_default(self):
        test_rule_dict = {"jira_security_level": "!default"}
        result = self.rule._get_jira_security_level(test_rule_dict)
        assert result == "Medium"

    def test_get_jira_security_level_non_string(self):
        test_rule_dict = {"jira_security_level": 123}
        with pytest.raises(SystemExit):
            self.rule._get_jira_security_level(test_rule_dict)
