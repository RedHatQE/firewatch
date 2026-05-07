from unittest.mock import patch

import pytest

from tests.unittests.objects.rule.rule_base_test import RuleBaseTest


class TestGetSlackChannel(RuleBaseTest):
    def test_get_slack_channel_defined(self):
        test_rule_dict = {"slack_channel": "#my-channel"}
        result = self.rule._get_slack_channel(test_rule_dict)
        assert result == "#my-channel"

    def test_get_slack_channel_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_slack_channel(test_rule_dict)
        assert result is None

    @patch.dict("os.environ", {"FIREWATCH_DEFAULT_SLACK_CHANNEL": "#default-channel"})
    def test_get_slack_channel_default(self):
        test_rule_dict = {"slack_channel": "!default"}
        result = self.rule._get_slack_channel(test_rule_dict)
        assert result == "#default-channel"

    def test_get_slack_channel_non_string(self):
        test_rule_dict = {"slack_channel": 123}
        with pytest.raises(SystemExit):
            self.rule._get_slack_channel(test_rule_dict)
