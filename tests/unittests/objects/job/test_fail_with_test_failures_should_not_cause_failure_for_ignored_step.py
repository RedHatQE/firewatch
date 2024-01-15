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
import json
import re

import pytest

from cli.objects.configuration import Configuration
from cli.objects.job import Job


@pytest.fixture(autouse=True)
def setup_tests(
    monkeypatch,
    assert_jira_config_file_exists,
    assert_default_jira_project_in_env,
    patch_job_log_dir,
    patch_job_junit_dir,
):
    monkeypatch.setenv(
        "FIREWATCH_CONFIG",
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


@pytest.fixture
def config(jira):
    yield Configuration(
        jira=jira,
        fail_with_test_failures=True,
        keep_job_dir=True,
        verbose_test_failure_reporting=False,
    )


@pytest.fixture
def job(config, job_junit_dir):
    gather_must_gather_dir = job_junit_dir / "gather-must-gather"
    gather_must_gather_dir.mkdir(exist_ok=True, parents=True)
    (gather_must_gather_dir / "finished.json").write_text(
        '{"timestamp":170340000,"passed":false,"result":"FAILURE","revision":"release-v1.11"}',
    )
    yield Job(
        name="periodic-ci-windup-windup-ui-tests-v1.2-mtr-ocp4.15-lp-interop-mtr-interop-aws",
        name_safe="mtr-interop-aws",
        build_id="1739165508839673856",
        gcs_bucket="test-platform-results",
        firewatch_config=config,
    )


def test_init_job_from_fixtures(job):
    assert isinstance(job, Job)


def test_fail_with_test_failures_should_not_cause_failure_for_ignored_step(config, job):
    rule = config.failure_rules[0]
    assert rule.step == "gather-*"
    assert rule.ignore
    assert re.match(rule.step, "gather-must-gather")
    assert not job.has_failures
