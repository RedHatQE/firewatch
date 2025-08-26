import json
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
        json.dumps({
            "failure_rules": [
                {
                    "step": "openshift-pipelines-tests",
                    "failure_type": "test_failure",
                    "classification": "NONE",
                    "jira_project": "NONE",
                    "ignore": "true",
                },
            ],
        }),
    )
    yield Configuration(
        jira=mock_jira,
        fail_with_test_failures=True,
        fail_with_pod_failures=True,
        keep_job_dir=True,
        verbose_test_failure_reporting=False,
    )


@pytest.fixture
def job_step_names(monkeypatch):
    step_names = ["openshift-pipelines-tests"]

    def _mock_get_steps(*args, **kwargs):
        return step_names

    monkeypatch.setattr(Job, "_get_steps", _mock_get_steps)
    return step_names


@pytest.fixture(autouse=True)
def patch_job_dirs(firewatch_config, job_step_names, job_log_dir, job_artifacts_dir, patch_job_download_dirs):
    for step_name in job_step_names:
        (job_log_dir / step_name).mkdir(exist_ok=True, parents=True)
        (job_artifacts_dir / step_name).mkdir(exist_ok=True, parents=True)


@pytest.fixture
def test_failure_artifacts_present(job_step_names, job_artifacts_dir):
    for step_name in job_step_names:
        step_dir = job_artifacts_dir / step_name
        step_dir.mkdir(exist_ok=True, parents=True)
        (step_dir / "junit_install.xml").write_text("""
            <testsuite name="cluster install" tests="8" failures="1">
            <testcase name="install should succeed: other"/>
            <testcase name="install should succeed: configuration"/>
            <testcase name="install should succeed: infrastructure"/>
            <testcase name="install should succeed: cluster bootstrap"/>
            <testcase name="install should succeed: cluster creation"/>
            <testcase name="install should succeed: cluster operator stability"/>
            <testcase name="install should succeed: overall"/>
            <testcase name="install should succeed: infrastructure">
              <failure message="">openshift cluster install failed with infrastructure setup</failure>
            </testcase>
          </testsuite>
        """)


@pytest.fixture
def job(firewatch_config, job_step_names):
    yield Job(
        name="periodic-ci-openshift-pipelines-release-tests-release-v1.15-openshift-pipelines-ocp-4.17-lp-interop-openshift-pipelines-interop-aws",
        name_safe="openshift-pipelines-interop-aws",
        build_id="1833066891065692160",
        gcs_bucket="test-platform-results",
        gcs_creds_file=None,
        firewatch_config=firewatch_config,
    )


@pytest.fixture
def firewatch_config_no_ignored_rules(firewatch_config):
    for rule in firewatch_config.failure_rules:
        rule.ignore = False
    yield firewatch_config


def test_fail_with_test_failures_should_not_cause_failure_for_ignored_step(
    firewatch_config, test_failure_artifacts_present, job
):
    assert firewatch_config.fail_with_test_failures
    for rule in firewatch_config.failure_rules:
        if rule.failure_type == "test_failure":
            assert rule.ignore
    assert not job.has_test_failures
    assert not job.failures


def test_fail_with_test_failures_should_cause_failure_unignored_step(
    firewatch_config_no_ignored_rules, test_failure_artifacts_present, job
):
    assert firewatch_config_no_ignored_rules.fail_with_test_failures
    for rule in firewatch_config_no_ignored_rules.failure_rules:
        if rule.failure_type == "test_failure":
            assert not rule.ignore
    assert job.has_test_failures
    assert job.failures
