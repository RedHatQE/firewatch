# Copyright (C) 2023 Red Hat, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import pytest

from tests.unittests.objects.failure_rule.failure_rule_base_test import (
    FailureRuleBaseTest,
)


class TestGetStep(FailureRuleBaseTest):
    def test_get_step_valid(self):
        test_rule_dict = {"step": "test-step-name"}
        step = self.rule._get_step(test_rule_dict)
        assert step == "test-step-name"

    def test_get_step_missing(self):
        test_rule_dict = {}
        with pytest.raises(SystemExit):
            self.rule._get_step(test_rule_dict)
        self.mock_logger.error.assert_called_once_with(
            'Unable to find value for "step" in firewatch rule: "{}"',
        )

    def test_get_step_not_string(self):
        test_rule_dict = {"step": 123}
        with pytest.raises(SystemExit):
            self.rule._get_step(test_rule_dict)
        self.mock_logger.error.assert_called_once_with(
            'Value for "step" is not a string in firewatch rule: "{\'step\': 123}"',
        )
