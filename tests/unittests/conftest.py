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
import os
import pprint
from dataclasses import dataclass

import pytest
import simple_logger.logger

from cli.objects.configuration import Configuration
from cli.objects.jira_base import Jira
from cli.objects.job import Job
from cli.report import Report

LOGGER = simple_logger.logger.get_logger(__name__)

BUILD_ID_ENV_VAR = "BUILD_ID"
FIREWATCH_DEFAULT_JIRA_PROJECT_ENV_VAR = "FIREWATCH_DEFAULT_JIRA_PROJECT"
FIREWATCH_DEFAULT_JIRA_EPIC_ENV_VAR = "FIREWATCH_DEFAULT_JIRA_EPIC"
ARTIFACT_DIR_ENV_VAR = "ARTIFACT_DIR"
JIRA_TOKEN_ENV_VAR = "JIRA_TOKEN"
FIREWATCH_CONFIG_ENV_VAR = "FIREWATCH_CONFIG"

BUILD_IDS_TO_TEST = [
    "1739164176636448768",
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

DEFAULT_MOCK_ISSUE_KEY = "LPTOCPCI-MOCK"


@pytest.fixture
def jira(jira_config_path):
    yield Jira(jira_config_path=jira_config_path.as_posix())


@pytest.fixture
def firewatch_config(jira):
    yield Configuration(
        jira=jira,
        fail_with_test_failures=False,
        keep_job_dir=True,
        verbose_test_failure_reporting=False,
    )


@pytest.fixture
def job(firewatch_config, build_id):
    yield Job(
        name="periodic-ci-openshift-pipelines-release-tests-release-v1.11-openshift-pipelines-ocp4.14-lp-interop-openshift-pipelines-interop-aws",
        name_safe="openshift-pipelines-interop-aws",
        build_id=build_id,
        gcs_bucket="test-platform-results",
        firewatch_config=firewatch_config,
    )


@pytest.fixture()
def patch_jira(monkeypatch):
    @dataclass
    class MockIssue:
        key: str = DEFAULT_MOCK_ISSUE_KEY

    def create_jira_issue(*args, **kwargs):
        LOGGER.info("Patching Report.create_jira_issue")
        LOGGER.info(
            f"Attempted call Report.create_issue with the following keywords: \n{pprint.pformat(kwargs)}",
        )
        return MockIssue()

    def add_duplicate_comment(*args, **kwargs):
        LOGGER.info("Patching Report.add_duplicate_comment")
        LOGGER.info(
            f"Attempted to call Report.add_duplicate_comment with the following keywords: \n{pprint.pformat(kwargs)}",
        )
        return

    monkeypatch.setattr(Report, "create_jira_issue", create_jira_issue)
    monkeypatch.setattr(Report, "add_duplicate_comment", add_duplicate_comment)


@pytest.fixture
def cap_jira(monkeypatch):
    @dataclass
    class MockIssue:
        key: str = "LPTOCPCI-MOCK"

    @dataclass
    class CapInputs:
        args: tuple = None
        kwargs: dict = None

    @dataclass
    class CapJira:
        create_jira_issue: list[CapInputs] = None
        add_duplicate_comment: list[CapInputs] = None

        def __post_init__(self):
            self.create_jira_issue = []
            self.add_duplicate_comment = []

    cap = CapJira()

    def create_jira_issue(*args, **kwargs):
        LOGGER.info("Patching Report.create_jira_issue")
        cap.create_jira_issue.append(CapInputs(args, kwargs))
        return MockIssue()

    def add_duplicate_comment(*args, **kwargs):
        LOGGER.info("Patching Report.add_duplicate_comment")
        cap.add_duplicate_comment.append(CapInputs(args, kwargs))

    monkeypatch.setattr(Report, "create_jira_issue", create_jira_issue)
    monkeypatch.setattr(Report, "add_duplicate_comment", add_duplicate_comment)
    yield cap


@pytest.fixture
def patch_job_log_dir(monkeypatch, job_log_dir):
    LOGGER.info("Patching Job log dir path")

    def _download_logs(*args, **kwargs):
        return job_log_dir.as_posix()

    monkeypatch.setattr(Job, "_download_logs", _download_logs)


@pytest.fixture
def patch_job_junit_dir(monkeypatch, job_artifacts_dir):
    LOGGER.info("Patching Job junit dir path")

    def _download_junit(*args, **kwargs):
        return job_artifacts_dir.as_posix()

    monkeypatch.setattr(Job, "_download_junit", _download_junit)


@pytest.fixture
def fake_log_secret_path(job_log_dir):
    yield job_log_dir.joinpath("fake-step/fake_build_log.txt")


@pytest.fixture
def fake_junit_secret_path(job_artifacts_dir):
    yield job_artifacts_dir.joinpath("fake-step/fake_junit.xml")


@pytest.fixture
def firewatch_config_json(monkeypatch):
    config_json = json.dumps(
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
    )
    monkeypatch.setenv(FIREWATCH_CONFIG_ENV_VAR, config_json)
    yield config_json


@pytest.fixture
def jira_config_path(tmp_path):
    config_path = tmp_path.joinpath("jira_config.json")
    if not config_path.is_file():
        config_path.parent.mkdir(exist_ok=True, parents=True)
        config_path.write_text(
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
    yield config_path


@pytest.fixture(params=JOB_STEP_DIRS_TO_TEST)
def job_log_step_dirs(request, job_log_dir):
    yield (job_log_dir / p for p in request.param)


@pytest.fixture(params=JOB_STEP_DIRS_TO_TEST)
def job_junit_step_dirs(request, job_artifacts_dir):
    yield (job_artifacts_dir / p for p in request.param)


@pytest.fixture
def job_log_dir(job_dir):
    yield job_dir / "logs"


@pytest.fixture
def job_artifacts_dir(job_dir):
    yield job_dir / "artifacts"


@pytest.fixture(params=JOB_DIR_LOG_ARTIFACT_FILE_NAMES_TO_TEST)
def job_dir_log_artifact_paths(request, job_log_step_dirs):
    yield (p / request.param[0] for p in job_log_step_dirs)


@pytest.fixture(params=JOB_DIR_JUNIT_ARTIFACT_FILE_NAMES_TO_TEST)
def job_dir_junit_artifact_paths(request, job_junit_step_dirs):
    yield (p / request.param[0] for p in job_junit_step_dirs)


@pytest.fixture
def artifact_dir(monkeypatch, tmp_path):
    path = tmp_path / "artifacts"
    monkeypatch.setenv(ARTIFACT_DIR_ENV_VAR, path.as_posix())
    path.mkdir(exist_ok=True, parents=True)
    yield path


@pytest.fixture
def job_dir(tmp_path, build_id):
    yield tmp_path / build_id


@pytest.fixture(params=BUILD_IDS_TO_TEST, ids=BUILD_IDS_TO_TEST)
def build_id(monkeypatch, request):
    param = request.param
    monkeypatch.setenv(BUILD_ID_ENV_VAR, param)
    yield param


@pytest.fixture(params=DEFAULT_JIRA_PROJECTS_TO_TEST)
def default_jira_project(monkeypatch, request):
    param = request.param
    monkeypatch.setenv(FIREWATCH_DEFAULT_JIRA_PROJECT_ENV_VAR, param)
    yield param


@pytest.fixture(params=DEFAULT_JIRA_EPICS_TO_TEST, ids=DEFAULT_JIRA_EPICS_TO_TEST)
def default_jira_epic(monkeypatch, request):
    param = request.param
    monkeypatch.setenv(FIREWATCH_DEFAULT_JIRA_EPIC_ENV_VAR, param)
    yield param


@pytest.fixture
def jira_token():
    token = os.getenv(JIRA_TOKEN_ENV_VAR)
    assert token
    yield token
