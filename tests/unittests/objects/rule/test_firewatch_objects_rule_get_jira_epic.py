import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from cli.objects.rule import Rule


class TestGetJiraEpic(unittest.TestCase):
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

    def test_get_jira_epic_defined(self):
        test_rule_dict = {"jira_epic": "TEST-1234"}
        result = self.rule._get_jira_epic(test_rule_dict)
        assert result == "TEST-1234"

    def test_get_jira_epic_undefined(self):
        test_rule_dict = {}
        result = self.rule._get_jira_epic(test_rule_dict)
        assert result is None

    @patch.dict("os.environ", {"FIREWATCH_DEFAULT_JIRA_EPIC": "DEFAULT-EPIC"})
    def test_get_jira_epic_default(self):
        test_rule_dict = {"jira_epic": "!default"}
        result = self.rule._get_jira_epic(test_rule_dict)
        assert result == "DEFAULT-EPIC"
