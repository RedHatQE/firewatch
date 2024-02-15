import unittest

from src.objects.failure_rule import FailureRule


class TestFailureRule(unittest.TestCase):
    def setUp(self):
        self.rule_dict = {
            "step": "step1",
            "failure_type": "pod_failure",
            "classification": "classification1",
            "jira_project": "project1",
            "jira_epic": "epic1",
            "jira_component": ["component1"],
            "jira_affects_version": "version1",
            "jira_additional_labels": ["label1"],
            "jira_assignee": "assignee1@email.com",
            "jira_priority": "Blocker",
            "group": {"name": "group1", "priority": 2},
            "ignore": False,
        }

    def test_failure_rule_init(self):
        rule = FailureRule(rule_dict=self.rule_dict)
        assert rule.step == "step1"
        assert rule.failure_type == "pod_failure"
        assert rule.classification == "classification1"
        assert rule.jira_project == "project1"
        assert rule.jira_epic == "epic1"
        assert rule.jira_component == ["component1"]
        assert rule.jira_affects_version == "version1"
        assert rule.jira_additional_labels == ["label1"]
        assert rule.jira_assignee == "assignee1@email.com"
        assert rule.jira_priority == "Blocker"
        assert rule.group_name == "group1"
        assert rule.group_priority == 2
        assert not rule.ignore
