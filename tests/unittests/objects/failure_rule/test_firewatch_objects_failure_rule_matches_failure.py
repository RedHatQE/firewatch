# Copyright (C) 2024 Red Hat, Inc.
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

from cli.objects.failure import Failure
from cli.objects.failure_rule import FailureRule


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
