from src.objects.failure import Failure
from src.objects.failure_rule import FailureRule
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

    def test_configuration_gets_failure_rules_with_two_matching_steps(self):
        failure = Failure(failed_step="exact-failed-step", failure_type="test_failure")

        match_rule = FailureRule(
            rule_dict={
                "step": "exact-failed-step",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
            },
        )
        different_type_rule = FailureRule(
            rule_dict={
                "step": "exact-failed-step",
                "failure_type": "pod_failure",
                "classification": "NONE",
                "jira_project": "NONE",
            },
        )
        pattern_rule = FailureRule(
            rule_dict={
                "step": "exact-*",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
            },
        )
        rules = [pattern_rule, different_type_rule, match_rule]

        matching_rules = self.report.failure_matches_rule(
            failure=failure,
            rules=rules,
            default_jira_project=self.config.default_jira_project,
        )

        # Check if match_rule is sorted higher than pattern_rule
        assert matching_rules[0].step.__eq__(failure.step)
