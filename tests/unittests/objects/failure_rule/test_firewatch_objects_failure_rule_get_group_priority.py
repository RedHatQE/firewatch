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


class TestGetGroupPriority(FailureRuleBaseTest):
    def test_get_group_priority_defined(self):
        test_rule_dict = {"group": {"priority": 1}}
        result = self.rule._get_group_priority(test_rule_dict)
        assert result == 1

    def test_get_group_priority_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_group_priority(test_rule_dict)
        assert result is None

    def test_get_group_priority_not_dict(self):
        test_rule_dict = {"group": "not_a_dict"}
        with pytest.raises(SystemExit):
            self.rule._get_group_priority(test_rule_dict)

    def test_get_group_priority_non_integer(self):
        test_rule_dict = {"group": {"priority": "not_an_integer"}}
        with pytest.raises(SystemExit):
            self.rule._get_group_priority(test_rule_dict)
