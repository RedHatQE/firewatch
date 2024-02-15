import json
import re
from dataclasses import dataclass

import pytest

from src.objects.configuration import Configuration
from src.objects.job import Job
from tests.unittests.conftest import FIREWATCH_CONFIG_ENV_VAR


@pytest.fixture()
def mock_jira():
    @dataclass
    class MockJira: ...

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
