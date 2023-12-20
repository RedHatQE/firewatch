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


class TestFailureMatchesRule(ReportBaseTest):
    failure = Failure(failed_step="failed-step", failure_type="test_failure")

    def test_failure_matches_rule_failure_has_no_match(self):
        default_rule_dict = {
            "step": "!none",
            "failure_type": "!none",
            "classification": "!none",
            "jira_project": self.config.default_jira_project,
        }
        default_rule = FailureRule(default_rule_dict)
        no_match_rule = FailureRule(
            rule_dict={
                "step": "other-step",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
            },
        )
        rules = [no_match_rule]
        matching_rules = self.report.failure_matches_rule(
            failure=self.failure,
            rules=rules,
            default_jira_project=self.config.default_jira_project,
        )
        assert len(matching_rules) == 1
        assert matching_rules[0].step == default_rule.step

    def test_failure_matches_rule_failure_matches_ignore_rule(self):
        ignore_rule = FailureRule(
            rule_dict={
                "step": "failed-step",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
                "ignore": "true",
            },
        )
        rules = [ignore_rule]
        matching_rules = self.report.failure_matches_rule(
            failure=self.failure,
            rules=rules,
            default_jira_project=self.config.default_jira_project,
        )
        assert len(matching_rules) == 0

    def test_failure_matches_rule_with_matches(self):
        match_rule = FailureRule(
            rule_dict={
                "step": "failed-step",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
            },
        )
        rules = [match_rule]
        matching_rules = self.report.failure_matches_rule(
            failure=self.failure,
            rules=rules,
            default_jira_project=self.config.default_jira_project,
        )
        assert len(matching_rules) == 1
        assert (matching_rules[0].step == match_rule.step) and (
            matching_rules[0].failure_type == match_rule.failure_type
        )
