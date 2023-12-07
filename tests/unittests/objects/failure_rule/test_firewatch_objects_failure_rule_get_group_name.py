import unittest
from unittest.mock import patch, MagicMock

import pytest

from cli.objects.failure_rule import FailureRule


class TestGetGroupName(unittest.TestCase):

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

    def test_get_group_name_defined(self):
        test_rule_dict = {"group": {"name": "test_group"}}
        result = self.rule._get_group_name(test_rule_dict)
        assert result == "test_group"

    def test_get_group_name_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_group_name(test_rule_dict)
        assert result is None

    def test_get_group_name_not_dict(self):
        test_rule_dict = {"group": "not_a_dict"}
        with pytest.raises(SystemExit):
            self.rule._get_group_name(test_rule_dict)

    def test_get_group_name_non_string(self):
        test_rule_dict = {"group": {"name": 123}}
        with pytest.raises(SystemExit):
            self.rule._get_group_name(test_rule_dict)
