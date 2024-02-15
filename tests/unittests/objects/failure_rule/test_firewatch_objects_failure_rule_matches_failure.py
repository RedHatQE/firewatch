import pytest

from src.objects.failure import Failure
from src.objects.failure_rule import FailureRule


@pytest.fixture
def failure_rule():
    yield FailureRule(
        rule_dict={
            "step": "gather-*",
            "failure_type": "test_failure",
            "classification": "NONE",
            "jira_project": "NONE",
            "ignore": "false",
        },
    )


@pytest.fixture
def failure():
    yield Failure(
        failure_type="test_failure",
        failed_test_name="post",
        failed_step="gather-must-gather",
    )


def test_failure_rule_matches_failure_if_rule_pattern_equals_failure_step(
    failure,
    failure_rule,
):
    failure_rule.step = failure.step = "gather-must-gather"
    assert failure_rule.matches_failure(
        failure,
    ), f"'{failure_rule.step}' should match '{failure.step}'"


def test_failure_rule_matches_failure_if_glob_style_rule_pattern_matches_failure_step(
    failure,
    failure_rule,
):
    failure.step = "gather-must-gather"
    failure_rule.step = "gather-*"
    assert failure_rule.matches_failure(
        failure,
    ), f"'{failure_rule.step}' should match '{failure.step}'"


def test_failure_rule_does_not_match_non_glob_unequal_failure_step(
    failure,
    failure_rule,
):
    failure.step = "gather-must-gather"
    failure_rule.step = "firewatch_report_issues"
    assert not failure_rule.matches_failure(
        failure,
    ), f"'{failure_rule.step}' should NOT match '{failure.step}'"
