from unittest.mock import patch

import pytest

from tests.unittests.objects.rule.rule_base_test import RuleBaseTest


class TestGetJiraComponent(RuleBaseTest):
    def test_get_jira_component_defined(self):
        test_rule_dict = {"jira_component": ["TEST-COMPONENT"]}
        result = self.rule._get_jira_component(test_rule_dict)
        assert result == ["TEST-COMPONENT"]

    def test_get_jira_component_undefined(self):
        test_rule_dict = {}
        result = self.rule._get_jira_component(test_rule_dict)
        assert result is None

    @patch.dict(
        "os.environ",
        {
            "FIREWATCH_DEFAULT_JIRA_COMPONENT": '["DEFAULT-COMPONENT", "ANOTHER-COMPONENT"]',
        },
    )
    def test_get_jira_component_default(self):
        test_rule_dict = {"jira_component": ["!default"]}
        result = self.rule._get_jira_component(test_rule_dict)
        assert result[0] == "DEFAULT-COMPONENT"

    def test_get_jira_component_not_list(self):
        test_rule_dict = {"jira_component": "TEST-COMPONENT"}
        with pytest.raises(SystemExit):
            self.rule._get_jira_component(test_rule_dict)
