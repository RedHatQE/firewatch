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
import os

import pytest
import simple_logger.logger

from cli.gitleaks import GitleaksConfig
from cli.objects.job import Job

_logger = simple_logger.logger.get_logger(__name__)

BUILD_ID_ENV_VAR = "BUILD_ID"
FIREWATCH_DEFAULT_JIRA_PROJECT_ENV_VAR = "FIREWATCH_DEFAULT_JIRA_PROJECT"
FIREWATCH_DEFAULT_JIRA_EPIC_ENV_VAR = "FIREWATCH_DEFAULT_JIRA_EPIC"
ARTIFACT_DIR_ENV_VAR = "ARTIFACT_DIR"
PATTERNS_SERVER_TOKEN_ENV_VAR = "PATTERNS_SERVER_TOKEN"
JIRA_TOKEN_ENV_VAR = "JIRA_TOKEN"
FIREWATCH_CONFIG_ENV_VAR = "FIREWATCH_CONFIG"

FAKE_SECRET = "aws_se" + 'cret="AKIAI' + 'MNOJVGFDXXXE4OA"'

BUILD_IDS_TO_TEST = [
    "1678283096597729280",
]

DEFAULT_JIRA_PROJECTS_TO_TEST = [
    "LPTOCPCI",
]

DEFAULT_JIRA_EPICS_TO_TEST = ["LPTOCPCI-290"]

JOB_STEP_DIRS_TO_TEST = [
    ["gather-must-gather", "gather-extra", "mtr-tests-ui", "firewatch_report_issues"],
]

JOB_DIR_LOG_ARTIFACT_FILE_NAMES_TO_TEST = [["build-log.txt", "finished.json"]]
JOB_DIR_JUNIT_ARTIFACT_FILE_NAMES_TO_TEST = [
    ["junit_install.xml", "junit_install_status.xml", "junit_symptoms.xml"],
]


@pytest.fixture
def patch_gitleaks_config_job_dir(monkeypatch, job_dir):
    _logger.info("Patching GitleaksConfig job dir path")
    monkeypatch.setattr(GitleaksConfig, "job_dir", job_dir)


@pytest.fixture
def patch_gitleaks_config_patterns_server_token_path(
    monkeypatch,
    patterns_server_token_path,
):
    _logger.info("Patching GitleaksConfig patterns server token path")
    monkeypatch.setattr(GitleaksConfig, "token_path", patterns_server_token_path)


@pytest.fixture
def patch_job_log_dir(monkeypatch, job_log_dir):
    _logger.info("Patching Job log dir path")

    def _download_logs(*args, **kwargs):
        return job_log_dir.as_posix()

    monkeypatch.setattr(Job, "_download_logs", _download_logs)


@pytest.fixture
def patch_job_junit_dir(monkeypatch, job_junit_dir):
    _logger.info("Patching Job junit dir path")

    def _download_junit(*args, **kwargs):
        return job_junit_dir.as_posix()

    monkeypatch.setattr(Job, "_download_junit", _download_junit)


@pytest.fixture
def assert_job_dir_exists(job_dir):
    job_dir.mkdir(exist_ok=True, parents=True)
    assert job_dir.is_dir()


@pytest.fixture
def assert_job_log_artifacts_exist(job_dir_log_artifact_paths):
    for p in job_dir_log_artifact_paths:
        if not p.is_file():
            p.parent.mkdir(exist_ok=True, parents=True)
            p.write_text("This should not trigger a gitleaks detection.")
        assert p.is_file()


@pytest.fixture
def assert_job_junit_artifacts_exist(job_dir_junit_artifact_paths):
    for p in job_dir_junit_artifact_paths:
        if not p.is_file():
            p.parent.mkdir(exist_ok=True, parents=True)
            if p.suffix.lower() == ".xml":
                p.write_text(
                    """
                    <testsuite name="This should not trigger a gitleaks detection" tests="0" failures="0">
                    </testsuite>
                """,
                )
            else:
                p.write_text("this should not trigger a detection")
        assert p.is_file()


@pytest.fixture
def assert_fake_secret_in_job_logs_dir_exists(fake_log_secret_path):
    fake_log_secret_path.parent.mkdir(exist_ok=True, parents=True)
    fake_log_secret_path.write_text(FAKE_SECRET)
    assert fake_log_secret_path.is_file()


@pytest.fixture
def assert_fake_secret_in_job_junit_dir_exists(fake_junit_secret_path):
    fake_junit_secret_path.parent.mkdir(exist_ok=True, parents=True)
    fake_junit_secret_path.write_text(
        f"""<testsuite name="This SHOULD trigger a gitleaks detection" tests="0" failures="0">
                    {FAKE_SECRET}
        </testsuite>""",
    )
    assert fake_junit_secret_path.is_file()


@pytest.fixture
def fake_log_secret_path(job_log_dir):
    yield job_log_dir.joinpath("fake-step/fake_build_log.txt")


@pytest.fixture
def fake_junit_secret_path(job_junit_dir):
    yield job_junit_dir.joinpath("fake-step/fake_junit.xml")


@pytest.fixture
def assert_jira_config_file_exists(jira_config_path):
    if not jira_config_path.is_file():
        jira_config_path.parent.mkdir(exist_ok=True, parents=True)
        jira_config_path.write_text(
            json.dumps(
                {
                    "token": os.getenv(JIRA_TOKEN_ENV_VAR),
                    "url": "https://issues.stage.redhat.com",
                    "proxies": {
                        "http": "http://squid.corp.redhat.com:3128",
                        "https": "http://squid.corp.redhat.com:3128",
                    },
                },
            ),
        )
    assert jira_config_path.is_file()


@pytest.fixture
def assert_firewatch_config_in_env(monkeypatch):
    monkeypatch.setenv(
        FIREWATCH_CONFIG_ENV_VAR,
        json.dumps(
            {
                "failure_rules": [
                    {
                        "step": "exact-step-name",
                        "failure_type": "pod_failure",
                        "classification": "Infrastructure",
                        "jira_project": "!default",
                        "jira_component": ["some-component"],
                        "jira_assignee": "some-user@redhat.com",
                        "jira_security_level": "Restricted",
                    },
                    {
                        "step": "*partial-name*",
                        "failure_type": "all",
                        "classification": "Misc.",
                        "jira_project": "OTHER",
                        "jira_component": ["component-1", "component-2", "!default"],
                        "jira_priority": "major",
                        "group": {"name": "some-group", "priority": 1},
                    },
                    {
                        "step": "*ends-with-this",
                        "failure_type": "test_failure",
                        "classification": "Test failures",
                        "jira_epic": "!default",
                        "jira_additional_labels": [
                            "test-label-1",
                            "test-label-2",
                            "!default",
                        ],
                        "group": {"name": "some-group", "priority": 2},
                    },
                    {
                        "step": "*ignore*",
                        "failure_type": "test_failure",
                        "classification": "NONE",
                        "jira_project": "NONE",
                        "ignore": "true",
                    },
                    {
                        "step": "affects-version",
                        "failure_type": "all",
                        "classification": "Affects Version",
                        "jira_project": "TEST",
                        "jira_epic": "!default",
                        "jira_affects_version": "4.14",
                        "jira_assignee": "!default",
                    },
                    {
                        "step": "affects-version",
                        "failure_type": "all",
                        "classification": "Affects Version",
                        "jira_project": "TEST",
                        "jira_epic": "!default",
                        "jira_affects_version": "4.14",
                        "jira_assignee": "!default",
                    },
                ],
            },
        ),
    )
    assert os.getenv(FIREWATCH_CONFIG_ENV_VAR)


@pytest.fixture
def assert_artifact_dir_exists(artifact_dir):
    artifact_dir.mkdir(exist_ok=True, parents=True)
    assert artifact_dir.is_dir()


@pytest.fixture
def jira_config_path(tmp_path):
    yield tmp_path.joinpath("jira.config")


@pytest.fixture
def assert_patterns_server_token_file_exists(patterns_server_token_path):
    if not patterns_server_token_path.is_file():
        patterns_server_token_path.parent.mkdir(exist_ok=True, parents=True)
        patterns_server_token_path.write_text(os.getenv(PATTERNS_SERVER_TOKEN_ENV_VAR))
    assert patterns_server_token_path.is_file()


@pytest.fixture
def patterns_server_token_path(tmp_path):
    yield tmp_path.joinpath("secrets/rh-patterns-server/access-token")


@pytest.fixture(params=JOB_STEP_DIRS_TO_TEST)
def job_log_step_dirs(request, job_log_dir):
    yield (job_log_dir / p for p in request.param)


@pytest.fixture(params=JOB_STEP_DIRS_TO_TEST)
def job_junit_step_dirs(request, job_junit_dir):
    yield (job_junit_dir / p for p in request.param)


@pytest.fixture
def job_log_dir(job_dir):
    yield job_dir / "logs"


@pytest.fixture
def job_junit_dir(job_dir):
    yield job_dir / "artifacts"


@pytest.fixture(params=JOB_DIR_LOG_ARTIFACT_FILE_NAMES_TO_TEST)
def job_dir_log_artifact_paths(request, job_log_step_dirs):
    yield (p / request.param[0] for p in job_log_step_dirs)


@pytest.fixture(params=JOB_DIR_JUNIT_ARTIFACT_FILE_NAMES_TO_TEST)
def job_dir_junit_artifact_paths(request, job_junit_step_dirs):
    yield (p / request.param[0] for p in job_junit_step_dirs)


@pytest.fixture
def assert_artifact_dir_in_env(monkeypatch, artifact_dir):
    monkeypatch.setenv(ARTIFACT_DIR_ENV_VAR, artifact_dir.as_posix())
    assert os.getenv(ARTIFACT_DIR_ENV_VAR)


@pytest.fixture
def artifact_dir(tmp_path):
    yield tmp_path / "artifacts"


@pytest.fixture
def job_dir(tmp_path, build_id):
    yield tmp_path / build_id


@pytest.fixture(params=BUILD_IDS_TO_TEST, ids=BUILD_IDS_TO_TEST)
def build_id(request):
    yield request.param


@pytest.fixture(params=DEFAULT_JIRA_PROJECTS_TO_TEST, ids=DEFAULT_JIRA_PROJECTS_TO_TEST)
def default_jira_project(request):
    yield request.param


@pytest.fixture(params=DEFAULT_JIRA_EPICS_TO_TEST, ids=DEFAULT_JIRA_EPICS_TO_TEST)
def default_jira_epic(request):
    yield request.param


@pytest.fixture
def assert_build_id_in_env(build_id, monkeypatch):
    monkeypatch.setenv(BUILD_ID_ENV_VAR, build_id)
    assert os.getenv(BUILD_ID_ENV_VAR)


@pytest.fixture
def assert_default_jira_project_in_env(default_jira_project, monkeypatch):
    monkeypatch.setenv(FIREWATCH_DEFAULT_JIRA_PROJECT_ENV_VAR, default_jira_project)
    assert os.getenv(FIREWATCH_DEFAULT_JIRA_PROJECT_ENV_VAR)


@pytest.fixture
def assert_default_jira_epic_in_env(default_jira_epic, monkeypatch):
    monkeypatch.setenv(FIREWATCH_DEFAULT_JIRA_EPIC_ENV_VAR, default_jira_epic)
    assert os.getenv(FIREWATCH_DEFAULT_JIRA_EPIC_ENV_VAR)


@pytest.fixture
def assert_patterns_server_token_in_env():
    assert os.getenv(PATTERNS_SERVER_TOKEN_ENV_VAR)


@pytest.fixture
def assert_jira_token_in_env():
    assert os.getenv(JIRA_TOKEN_ENV_VAR)
