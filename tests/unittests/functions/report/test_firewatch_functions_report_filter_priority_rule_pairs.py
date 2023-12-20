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
from cli.objects.failure import Failure
from cli.objects.failure_rule import FailureRule
from tests.unittests.functions.report.report_base_test import ReportBaseTest


class TestFilterPriorityRulePairs(ReportBaseTest):
    def test_filter_priority_rule_failure_pairs_priorities_set(self):
        # Test when groups/priorities are set
        group_rule_1 = FailureRule(
            rule_dict={
                "step": "failed-step-1",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
                "group": {"name": "failed-steps", "priority": 1},
            },
        )
        group_rule_2 = FailureRule(
            rule_dict={
                "step": "failed-step-2",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
                "group": {"name": "failed-steps", "priority": 2},
            },
        )
        group_failure_1 = Failure(
            failed_step="failed-step-1",
            failure_type="test_failure",
        )
        group_failure_2 = Failure(
            failed_step="failed-step-2",
            failure_type="test_failure",
        )

        original_rule_failure_pairs = [
            {"rule": group_rule_1, "failure": group_failure_1},
            {"rule": group_rule_2, "failure": group_failure_2},
        ]

        filtered_rule_failure_pairs = self.report.filter_priority_rule_failure_pairs(
            rule_failure_pairs=original_rule_failure_pairs,
        )

        assert filtered_rule_failure_pairs == [
            {"rule": group_rule_1, "failure": group_failure_1},
        ]

    def test_filter_priority_rule_failure_pairs_priorities_not_set(self):
        # Test when groups/priorities not set
        rule_1 = FailureRule(
            rule_dict={
                "step": "failed-step-1",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
            },
        )
        rule_2 = FailureRule(
            rule_dict={
                "step": "failed-step-2",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
            },
        )
        failure_1 = Failure(failed_step="failed-step-1", failure_type="test_failure")
        failure_2 = Failure(failed_step="failed-step-2", failure_type="test_failure")

        original_rule_failure_pairs = [
            {"rule": rule_1, "failure": failure_1},
            {"rule": rule_2, "failure": failure_2},
        ]

        filtered_rule_failure_pairs = self.report.filter_priority_rule_failure_pairs(
            rule_failure_pairs=original_rule_failure_pairs,
        )

        assert filtered_rule_failure_pairs == original_rule_failure_pairs
