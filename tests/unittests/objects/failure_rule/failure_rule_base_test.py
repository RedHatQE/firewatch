import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from cli.objects.failure_rule import FailureRule


class FailureRuleBaseTest(unittest.TestCase):
    @patch("cli.objects.rule.get_logger")
    def setUp(self, mock_get_logger):
        self.mock_logger = MagicMock()
        mock_get_logger.return_value = self.mock_logger
        self.rule = FailureRule(
            rule_dict={
                "step": "dummy",
                "failure_type": "all",
                "classification": "test classification",
                "jira_project": "TEST",
            },
        )

    def tearDown(self):
        patch.stopall()
