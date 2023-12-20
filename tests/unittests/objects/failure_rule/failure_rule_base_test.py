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
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from cli.objects.failure_rule import FailureRule


class FailureRuleBaseTest(unittest.TestCase):
    @patch("cli.objects.rule.get_logger")
    def setUp(self, mock_get_logger):
        self.mock_logger = MagicMock()
        mock_get_logger.return_value = self.mock_logger
        self.rule = FailureRule(
            rule_dict={
                "step": "dummy",
                "failure_type": "all",
                "classification": "test classification",
                "jira_project": "TEST",
            },
        )

    def tearDown(self):
        patch.stopall()
