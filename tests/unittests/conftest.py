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
from dataclasses import dataclass
from pathlib import Path

import pytest
import requests
import simple_logger.logger
from jinja2 import Environment, select_autoescape, FileSystemLoader

from cli.objects.configuration import Configuration
from cli.objects.jira_base import Jira
from cli.objects.job import Job

LOGGER = simple_logger.logger.get_logger(__name__)

BUILD_ID_ENV_VAR = "BUILD_ID"
FIREWATCH_DEFAULT_JIRA_PROJECT_ENV_VAR = "FIREWATCH_DEFAULT_JIRA_PROJECT"
FIREWATCH_DEFAULT_JIRA_EPIC_ENV_VAR = "FIREWATCH_DEFAULT_JIRA_EPIC"
ARTIFACT_DIR_ENV_VAR = "ARTIFACT_DIR"
JIRA_SERVER_URL_ENV_VAR = "JIRA_SERVER_URL"
DEFAULT_JIRA_SERVER_URL = "https://issues.stage.redhat.com"
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

FAKE_ISSUE_KEY = "fake_issue_123"

FAKE_ISSUE_ID = "10002"

TEST_RESOURCES_DIR_RELATIVE_PATH = "resources"

TEST_TEMPLATES_DIR_NAME = "templates"

JIRA_API_TEST_TEMPLATES_DIR_NAME = "jira_api"

JIRA_FAKE_ISSUE_JSON_TEMPLATE_FILE_NAME = "fake_issue.json"

JIRA_FAKE_SERVER_INFO_JSON_TEMPLATE_FILE_NAME = "fake_server_info.json"

JIRA_FAKE_SEARCH_RESPONSE_JSON_TEMPLATE_FILE_NAME = "fake_search_response.json"

JIRA_FAKE_COMMENT_RESPONSE_JSON_TEMPLATE_FILE_NAME = "fake_comment_response.json"

JIRA_FAKE_FIELDS_RESPONSE_JSON_TEMPLATE_FILE_NAME = "fake_fields_response.json"

FIREWATCH_CONFIG_TEST_TEMPLATES_DIR_NAME = "firewatch_configs"

FIREWATCH_CONFIG_SAMPLE_JSON_FILE_NAME = "firewatch_config_sample.json"


@pytest.fixture
def test_resources_dir():
    test_resources_dir = Path(__file__).parent / TEST_RESOURCES_DIR_RELATIVE_PATH
    assert test_resources_dir.is_dir()
    yield test_resources_dir


@pytest.fixture
def test_templates_dir(test_resources_dir):
    path = test_resources_dir / TEST_TEMPLATES_DIR_NAME
    assert path.is_dir()
    yield path


@pytest.fixture
def jira_api_test_templates_dir(test_templates_dir):
    path = test_templates_dir / JIRA_API_TEST_TEMPLATES_DIR_NAME
    assert path.is_dir()
    yield path


@pytest.fixture
def firewatch_configs_test_templates_dir(test_templates_dir):
    path = test_templates_dir / FIREWATCH_CONFIG_TEST_TEMPLATES_DIR_NAME
    assert path.is_dir()
    yield path


@pytest.fixture
def jira_api_templates(jira_api_test_templates_dir):
    yield Environment(
        loader=FileSystemLoader(jira_api_test_templates_dir),
        autoescape=select_autoescape(),
    )


@pytest.fixture
def firewatch_configs_templates(firewatch_configs_test_templates_dir):
    yield Environment(
        loader=FileSystemLoader(firewatch_configs_test_templates_dir),
        autoescape=select_autoescape(),
    )


@pytest.fixture
def fake_server_info_json(jira_api_templates):
    template = jira_api_templates.get_template(
        JIRA_FAKE_SERVER_INFO_JSON_TEMPLATE_FILE_NAME
    )
    rendered_template = template.render()
    yield json.loads(rendered_template)


@pytest.fixture
def fake_issue_json(jira_api_templates):
    template = jira_api_templates.get_template(JIRA_FAKE_ISSUE_JSON_TEMPLATE_FILE_NAME)
    rendered_template = template.render(
        FAKE_ISSUE_KEY=FAKE_ISSUE_KEY, FAKE_ISSUE_ID=FAKE_ISSUE_ID
    )
    yield json.loads(rendered_template)


@pytest.fixture
def fake_search_response_json(jira_api_templates):
    template = jira_api_templates.get_template(
        JIRA_FAKE_SEARCH_RESPONSE_JSON_TEMPLATE_FILE_NAME
    )
    rendered_template = template.render(
        FAKE_ISSUE_KEY=FAKE_ISSUE_KEY, FAKE_ISSUE_ID=FAKE_ISSUE_ID
    )
    yield json.loads(rendered_template)


@pytest.fixture
def fake_comment_response_json(jira_api_templates):
    template = jira_api_templates.get_template(
        JIRA_FAKE_COMMENT_RESPONSE_JSON_TEMPLATE_FILE_NAME
    )
    rendered_template = template.render(FAKE_ISSUE_ID=FAKE_ISSUE_ID)
    yield json.loads(rendered_template)


@pytest.fixture
def fake_fields_response_json(jira_api_templates):
    template = jira_api_templates.get_template(
        JIRA_FAKE_FIELDS_RESPONSE_JSON_TEMPLATE_FILE_NAME
    )
    rendered_template = template.render()
    yield json.loads(rendered_template)


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
def firewatch_config_json(monkeypatch, firewatch_configs_templates):
    template = firewatch_configs_templates.get_template(
        FIREWATCH_CONFIG_SAMPLE_JSON_FILE_NAME
    )
    rendered_template = template.render()
    monkeypatch.setenv(FIREWATCH_CONFIG_ENV_VAR, rendered_template)
    yield json.loads(rendered_template)


@pytest.fixture
def jira_config_path(tmp_path, jira_token):
    config_path = tmp_path.joinpath("jira_config.json")
    if not config_path.is_file():
        config_path.parent.mkdir(exist_ok=True, parents=True)
        config_path.write_text(
            json.dumps(
                {
                    "token": os.getenv(JIRA_TOKEN_ENV_VAR),
                    "url": os.getenv(JIRA_SERVER_URL_ENV_VAR, DEFAULT_JIRA_SERVER_URL),
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


@pytest.fixture
def fake_issue_id():
    yield FAKE_ISSUE_ID


@pytest.fixture
def fake_issue_key():
    yield FAKE_ISSUE_KEY


@pytest.fixture
def fake_issue_with_labels_json(monkeypatch, fake_issue_json):
    fields = fake_issue_json["fields"]
    fields.update({"labels": ["should-be-labeled", "do-not-remove", "still-testing"]})
    monkeypatch.setitem(fake_issue_json, "fields", fields)
    yield fake_issue_json


@dataclass
class MockJiraApiResponse:
    _json: dict | list = None
    status_code: int = 200

    def ok(self):
        return True

    def json(self):
        return self._json


@pytest.fixture
def patch_jira_api_requests(
    monkeypatch,
    fake_server_info_json,
    fake_issue_json,
    fake_issue_id,
    fake_issue_key,
    fake_search_response_json,
    fake_comment_response_json,
    fake_fields_response_json,
):
    caps = {"get": {}, "post": {}, "put": {}}

    def get(self, url, *args, **kwargs):
        LOGGER.info(f"Patching GET request to URL: {url}")
        caps["get"][url] = (args, kwargs)

        if url.endswith("/serverInfo"):
            LOGGER.info(f"Faking Jira serverInfo")
            return MockJiraApiResponse(_json=fake_server_info_json, status_code=200)

        if url.endswith("/field"):
            LOGGER.info(f"Faking Jira fields")
            return MockJiraApiResponse(_json=fake_fields_response_json, status_code=200)
        if url.endswith("/search"):
            LOGGER.info(f"Faking Jira search results")
            return MockJiraApiResponse(_json=fake_search_response_json, status_code=200)
        if url.endswith(f"/issue/{fake_issue_id}") or url.endswith(
            f"/issue/{fake_issue_key}"
        ):
            LOGGER.info(f"Faking Jira issue: {url}")
            return MockJiraApiResponse(_json=fake_issue_json, status_code=200)
        else:
            monkeypatch.undo()
            return requests.sessions.Session.get(self, url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        LOGGER.info(f"Patching POST request to URL: {url}")
        caps["post"][url] = (args, kwargs)

        if url.endswith(f"/{fake_issue_key}/comment") or url.endswith(
            f"/{fake_issue_id}/comment"
        ):
            return MockJiraApiResponse(
                _json=fake_comment_response_json, status_code=201
            )
        else:
            monkeypatch.undo()
            return requests.sessions.Session.get(self, url, *args, **kwargs)

    def put(self, url, data, *args, **kwargs):
        LOGGER.info(f"Patching PUT request to URL: {url}")
        caps["put"][url] = (data, args, kwargs)

        if url.endswith(f"/issue/{fake_issue_id}") or url.endswith(
            f"/issue/{fake_issue_key}"
        ):
            data = json.loads(data)
            _json = fake_issue_json.copy()
            _json["fields"].update(data["fields"])
            return MockJiraApiResponse(_json=_json, status_code=204)
        else:
            monkeypatch.undo()
            return requests.sessions.Session.get(self, url, *args, **kwargs)

    monkeypatch.setattr(requests.sessions.Session, "get", get)
    monkeypatch.setattr(requests.sessions.Session, "post", post)
    monkeypatch.setattr(requests.sessions.Session, "put", put)

    yield caps
