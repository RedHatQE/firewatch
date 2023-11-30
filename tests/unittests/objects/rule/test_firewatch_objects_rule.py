import pytest

from cli.objects.rule import Rule


class TestRule:
    def setup_method(self):
        self.rule_dict = {
            "jira_project": "project1",
            "jira_epic": "epic1",
            "jira_component": ["component1"],
            "jira_affects_version": "version1",
            "jira_additional_labels": ["label1"],
            "jira_assignee": "assignee1@email.com",
            "jira_priority": "Blocker",
        }

    def test_rule_init(self):
        rule = Rule(rule_dict=self.rule_dict)
        assert rule.jira_project == "project1"
        assert rule.jira_epic == "epic1"
        assert rule.jira_component == ["component1"]
        assert rule.jira_affects_version == "version1"
        assert rule.jira_additional_labels == ["label1"]
        assert rule.jira_assignee == "assignee1@email.com"
        assert rule.jira_priority == "Blocker"
