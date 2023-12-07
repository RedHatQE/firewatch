from unittest.mock import patch

import pytest

from cli.objects.rule import Rule
from tests.unittests.objects.rule.rule_base_test import RuleBaseTest


class TestGetJiraAdditionalLabels(RuleBaseTest):
    def test_get_jira_additional_labels_defined(self):
        test_rule_dict = {"jira_additional_labels": ["label1", "label2"]}
        result = self.rule._get_jira_additional_labels(test_rule_dict)
        assert result == ["label1", "label2"]

    def test_get_jira_additional_labels_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_jira_additional_labels(test_rule_dict)
        assert result is None

    @patch.dict(
        "os.environ",
        {
            "FIREWATCH_DEFAULT_JIRA_ADDITIONAL_LABELS": '["default_label1", "default_label2"]',
        },
    )
    def test_get_jira_additional_labels_default(self):
        test_rule_dict = {"jira_additional_labels": ["!default", "label1"]}
        result = self.rule._get_jira_additional_labels(test_rule_dict)
        assert result == ["label1", "default_label1", "default_label2"]

    def test_get_jira_additional_labels_with_spaces(self):
        test_rule_dict = {"jira_additional_labels": ["label 1", "label2"]}
        with pytest.raises(SystemExit):
            self.rule._get_jira_additional_labels(test_rule_dict)

    def test_get_jira_additional_labels_non_string(self):
        test_rule_dict = {"jira_additional_labels": [123, "label2"]}
        with pytest.raises(SystemExit):
            self.rule._get_jira_additional_labels(test_rule_dict)
