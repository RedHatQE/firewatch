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

from cli.objects.failure import Failure
from cli.objects.failure_rule import FailureRule


@pytest.fixture(autouse=True)
def setup_tests(assert_default_jira_project_in_env):
    ...


@pytest.fixture
def rule_dict():
    yield {
        "step": "gather-*",
        "failure_type": "test_failure",
        "classification": "NONE",
        "jira_project": "NONE",
        "ignore": "false",
    }


@pytest.fixture
def failure_rule(rule_dict):
    yield FailureRule(rule_dict=rule_dict)


@pytest.fixture
def matching_failure():
    yield Failure(
        failure_type="test_failure",
        failed_test_name="post",
        failed_step="gather-must-gather",
    )


def test_init_failure_rule_from_fixtures(failure_rule):
    assert isinstance(failure_rule, FailureRule)


def test_failure_rule_matches_failure(failure_rule, matching_failure):
    assert failure_rule.matches_failure(matching_failure)
