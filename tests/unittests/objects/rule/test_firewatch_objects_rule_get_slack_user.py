import pytest

from tests.unittests.objects.rule.rule_base_test import RuleBaseTest


class TestGetSlackUser(RuleBaseTest):
    def test_get_slack_user_defined(self):
        test_rule_dict = {"slack_user": "mpruitt@redhat.com"}
        result = self.rule._get_slack_user(test_rule_dict)
        assert result == "mpruitt@redhat.com"

    def test_get_slack_user_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_slack_user(test_rule_dict)
        assert result is None

    def test_get_slack_user_non_string(self):
        test_rule_dict = {"slack_user": 123}
        with pytest.raises(SystemExit):
            self.rule._get_slack_user(test_rule_dict)
