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


class TestGetFailureType(FailureRuleBaseTest):
    def test_get_failure_type_valid(self):
        test_rule_dict = {"failure_type": "pod_failure"}
        failure_type = self.rule._get_failure_type(test_rule_dict)
        assert failure_type == "pod_failure"

    def test_get_failure_type_invalid(self):
        test_rule_dict = {"failure_type": "invalid_failure_type"}
        with pytest.raises(SystemExit):
            self.rule._get_failure_type(test_rule_dict)
        self.mock_logger.error.assert_called_once()

    def test_get_failure_type_missing(self):
        test_rule_dict = {}
        with pytest.raises(SystemExit):
            self.rule._get_failure_type(test_rule_dict)
        self.mock_logger.error.assert_called_once()
