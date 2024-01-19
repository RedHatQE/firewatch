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
import json
import re
from dataclasses import dataclass

import pytest

from cli.objects.configuration import Configuration
from cli.objects.job import Job
from tests.unittests.conftest import FIREWATCH_CONFIG_ENV_VAR


@pytest.fixture()
def mock_jira():
    @dataclass
    class MockJira:
        ...

    yield MockJira


@pytest.fixture
def firewatch_config(monkeypatch, mock_jira, default_jira_project):
    monkeypatch.setenv(
        FIREWATCH_CONFIG_ENV_VAR,
        json.dumps(
            {
                "failure_rules": [
                    {
                        "step": "gather-*",
                        "failure_type": "test_failure",
                        "classification": "NONE",
                        "jira_project": "NONE",
                        "ignore": "true",
                    },
                ],
            },
        ),
    )
    yield Configuration(
        jira=mock_jira,
        fail_with_test_failures=True,
        keep_job_dir=True,
        verbose_test_failure_reporting=False,
    )


@pytest.fixture
def job(firewatch_config, patch_job_log_dir, patch_job_junit_dir, job_artifacts_dir):
    gather_must_gather_dir = job_artifacts_dir / "gather-must-gather"
    gather_must_gather_dir.mkdir(exist_ok=True, parents=True)
    (gather_must_gather_dir / "finished.json").write_text(
        '{"timestamp":170340000,"passed":false,"result":"FAILURE","revision":"release-v1.11"}',
    )
    yield Job(
        name="periodic-ci-windup-windup-ui-tests-v1.2-mtr-ocp4.15-lp-interop-mtr-interop-aws",
        name_safe="mtr-interop-aws",
        build_id="1739165508839673856",
        gcs_bucket="test-platform-results",
        firewatch_config=firewatch_config,
    )


def test_fail_with_test_failures_should_not_cause_failure_for_ignored_step(
    monkeypatch,
    firewatch_config,
    job,
):
    rule = firewatch_config.failure_rules[0]
    assert rule.step == "gather-*"
    assert rule.ignore
    assert re.match(rule.step, "gather-must-gather")
    assert not job.has_failures
