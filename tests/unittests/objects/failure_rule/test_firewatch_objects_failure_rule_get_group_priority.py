import unittest
from unittest.mock import patch, MagicMock

import pytest

from cli.objects.failure_rule import FailureRule


class TestGetGroupPriority(unittest.TestCase):
    def setUp(self):
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

    def test_get_group_priority_defined(self):
        test_rule_dict = {"group": {"priority": 1}}
        result = self.rule._get_group_priority(test_rule_dict)
        assert result == 1

    def test_get_group_priority_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_group_priority(test_rule_dict)
        assert result is None

    def test_get_group_priority_not_dict(self):
        test_rule_dict = {"group": "not_a_dict"}
        with pytest.raises(SystemExit):
            self.rule._get_group_priority(test_rule_dict)

    def test_get_group_priority_non_integer(self):
        test_rule_dict = {"group": {"priority": "not_an_integer"}}
        with pytest.raises(SystemExit):
            self.rule._get_group_priority(test_rule_dict)
