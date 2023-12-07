import unittest
from unittest.mock import patch, MagicMock

import pytest

from cli.objects.failure_rule import FailureRule


class TestGetIgnore(unittest.TestCase):

    @patch("cli.objects.rule.get_logger")
    def setUp(self, mock_get_logger):
        self.rule = FailureRule(
            rule_dict={
                "step": "dummy",
                "failure_type": "all",
                "classification": "test classification",
                "jira_project": "TEST",
            },
        )
        self.mock_logger = patch('cli.objects.job.get_logger')
        self.mock_logger.start().return_value = MagicMock()

    def tearDown(self):
        patch.stopall()

    def test_get_ignore_defined_boolean(self):
        test_rule_dict = {"ignore": True}
        result = self.rule._get_ignore(test_rule_dict)
        assert result is True

    def test_get_ignore_defined_string(self):
        test_rule_dict = {"ignore": "True"}
        result = self.rule._get_ignore(test_rule_dict)
        assert result is True

    def test_get_ignore_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_ignore(test_rule_dict)
        assert result is False

    def test_get_ignore_non_boolean_string(self):
        test_rule_dict = {"ignore": 123}
        with pytest.raises(SystemExit):
            self.rule._get_ignore(test_rule_dict)
