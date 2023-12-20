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


class TestGetIgnore(FailureRuleBaseTest):
    def test_get_ignore_defined_boolean(self):
        test_rule_dict = {"ignore": True}
        result = self.rule._get_ignore(test_rule_dict)
        assert result is True

    def test_get_ignore_defined_string(self):
        test_rule_dict = {"ignore": "True"}
        result = self.rule._get_ignore(test_rule_dict)
        assert result is True

    def test_get_ignore_not_defined(self):
        test_rule_dict = {}
        result = self.rule._get_ignore(test_rule_dict)
        assert result is False

    def test_get_ignore_non_boolean_string(self):
        test_rule_dict = {"ignore": 123}
        with pytest.raises(SystemExit):
            self.rule._get_ignore(test_rule_dict)
