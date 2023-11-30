from unittest.mock import patch

from cli.objects.rule import Rule


class TestRuleGetJiraAffectsVersion:
    def setup_method(self):
        self.rule = Rule(
            rule_dict={
                "jira_project": "TEST",
            }
        )

    def test_get_jira_affects_version_defined(self):
        test_rule_dict = {"jira_affects_version": "test version"}
        result = self.rule._get_jira_affects_version(test_rule_dict)
        assert result == "test version"

    def test_get_jira_affects_version_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_jira_affects_version(test_rule_dict)
        assert result is None

    @patch.dict(
        "os.environ",
        {"FIREWATCH_DEFAULT_JIRA_AFFECTS_VERSION": "default version"},
    )
    def test_get_jira_affects_version_default(self):
        test_rule_dict = {"jira_affects_version": "!default"}
        result = self.rule._get_jira_affects_version(test_rule_dict)
        assert result == "default version"
