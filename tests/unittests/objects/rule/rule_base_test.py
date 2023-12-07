import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from cli.objects.rule import Rule


class RuleBaseTest(unittest.TestCase):
    def setUp(self):
        self.rule = Rule(
            rule_dict={
                "jira_project": "TEST",
            },
        )
        self.mock_logger = patch("cli.objects.job.get_logger")
        self.mock_logger.start().return_value = MagicMock()

    def tearDown(self):
        patch.stopall()
