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
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Type

import pytest
import requests
import simple_logger.logger
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import select_autoescape

from src.objects.configuration import Configuration
from src.objects.jira_base import Jira
from src.objects.job import Job

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
    "1805119554108526592",
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

JIRA_FAKE_ISSUE_ADD_ATTACHMENT_RESPONSE_JSON_TEMPLATE_FILE_NAME = "fake_issue_add_attachment_response.json"

JIRA_FAKE_TRANSITIONS_RESPONSE_JSON_TEMPLATE_FILE_NAME = "fake_transitions_response.json"

FIREWATCH_CONFIG_TEST_TEMPLATES_DIR_NAME = "firewatch_configs"

FIREWATCH_CONFIG_SAMPLE_JSON_FILE_NAME = "firewatch_config_sample.json"


@pytest.fixture(autouse=True)
def mock_required_env_vars(monkeypatch):
    monkeypatch.setenv("FIREWATCH_DEFAULT_JIRA_COMPONENT", '["default-component"]')
    monkeypatch.setenv("FIREWATCH_DEFAULT_JIRA_ADDITIONAL_LABELS", '["default-label"]')


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
def fake_server_info_json(jira_api_templates) -> dict:
    template = jira_api_templates.get_template(
        JIRA_FAKE_SERVER_INFO_JSON_TEMPLATE_FILE_NAME,
    )
    rendered_template = template.render()
    yield json.loads(rendered_template)


@pytest.fixture
def fake_issue_json(jira_api_templates):
    template = jira_api_templates.get_template(JIRA_FAKE_ISSUE_JSON_TEMPLATE_FILE_NAME)
    rendered_template = template.render(
        FAKE_ISSUE_KEY=FAKE_ISSUE_KEY,
        FAKE_ISSUE_ID=FAKE_ISSUE_ID,
    )
    yield json.loads(rendered_template)


@pytest.fixture
def fake_search_response_json(jira_api_templates):
    template = jira_api_templates.get_template(
        JIRA_FAKE_SEARCH_RESPONSE_JSON_TEMPLATE_FILE_NAME,
    )
    rendered_template = template.render(
        FAKE_ISSUE_KEY=FAKE_ISSUE_KEY,
        FAKE_ISSUE_ID=FAKE_ISSUE_ID,
    )
    yield json.loads(rendered_template)


@pytest.fixture
def fake_comment_response_json(jira_api_templates):
    template = jira_api_templates.get_template(
        JIRA_FAKE_COMMENT_RESPONSE_JSON_TEMPLATE_FILE_NAME,
    )
    rendered_template = template.render(FAKE_ISSUE_ID=FAKE_ISSUE_ID)
    yield json.loads(rendered_template)


@pytest.fixture
def fake_fields_response_json(jira_api_templates):
    template = jira_api_templates.get_template(
        JIRA_FAKE_FIELDS_RESPONSE_JSON_TEMPLATE_FILE_NAME,
    )
    rendered_template = template.render()
    yield json.loads(rendered_template)


@pytest.fixture
def fake_issue_add_attachment_response_json(jira_api_templates):
    template = jira_api_templates.get_template(
        JIRA_FAKE_ISSUE_ADD_ATTACHMENT_RESPONSE_JSON_TEMPLATE_FILE_NAME,
    )
    rendered_template = template.render()
    yield json.loads(rendered_template)


@pytest.fixture
def fake_issue_add_attachment_response(fake_issue_add_attachment_response_json):
    yield MockJiraApiResponse(_json=fake_issue_add_attachment_response_json, _status_code=200)


@pytest.fixture
def jira(jira_config_path):
    yield Jira(jira_config_path=jira_config_path.as_posix())


@pytest.fixture
def firewatch_config(jira):
    yield Configuration(
        jira=jira,
        fail_with_test_failures=False,
        fail_with_pod_failures=False,
        keep_job_dir=True,
        verbose_test_failure_reporting=False,
    )


@pytest.fixture
def patch_job_get_steps(monkeypatch):
    LOGGER.info("Patching Job step names")

    def _get_steps(*args, **kwargs):
        return []

    monkeypatch.setattr(Job, "_get_steps", _get_steps)


@pytest.fixture
def job(firewatch_config, build_id, patch_job_get_steps):
    yield Job(
        name="periodic-ci-openshift-pipelines-release-tests-release-v1.14-openshift-pipelines-ocp4.16-lp-interop-openshift-pipelines-interop-aws",
        name_safe="openshift-pipelines-interop-aws",
        build_id=build_id,
        gcs_bucket="test-platform-results",
        gcs_creds_file=None,
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
def patch_job_download_dirs(monkeypatch, job_artifacts_dir, patch_job_junit_dir, patch_job_log_dir):
    LOGGER.info("Patching Job download dir path")

    def _get_download_path(*args, **kwargs):
        return job_artifacts_dir.parent.as_posix()

    monkeypatch.setattr(Job, "_get_download_path", _get_download_path)


@pytest.fixture
def fake_log_secret_path(job_log_dir):
    yield job_log_dir.joinpath("fake-step/fake_build_log.txt")


@pytest.fixture
def fake_junit_secret_path(job_artifacts_dir):
    yield job_artifacts_dir.joinpath("fake-step/fake_junit.xml")


@pytest.fixture
def firewatch_config_json(monkeypatch, firewatch_configs_templates):
    template = firewatch_configs_templates.get_template(
        FIREWATCH_CONFIG_SAMPLE_JSON_FILE_NAME,
    )
    rendered_template = template.render()
    monkeypatch.setenv(FIREWATCH_CONFIG_ENV_VAR, rendered_template)
    yield json.loads(rendered_template)


@pytest.fixture
def jira_config_path(tmp_path):
    config_path = tmp_path.joinpath("jira_config.json")
    if not config_path.is_file():
        config_path.parent.mkdir(exist_ok=True, parents=True)
        config_path.write_text(
            json.dumps(
                {
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
    path = tmp_path / build_id
    path.mkdir(parents=True, exist_ok=True)
    yield path


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
    _status_code: int = None
    _ok: bool = None
    _content: bytes = None
    _headers: dict = None
    _url: str = None

    @property
    def ok(self):
        if not self._ok:
            if str(self.status_code).startswith("2"):
                self._ok = True
            else:
                self._ok = False
        return self._ok

    @property
    def status_code(self):
        if not self._status_code:
            self._status_code = 200
        return self._status_code

    def json(self):
        if not self._json:
            self._json = json.loads(self.content.decode())
        return self._json

    @property
    def headers(self):
        if not self._headers:
            self._headers = {}
        return self._headers

    @property
    def content(self):
        return self._content

    @property
    def text(self):
        if self.content:
            return self.content.decode("UTF-8")

    @property
    def url(self):
        return self._url


@pytest.fixture
def mock_jira_api_response() -> Type[MockJiraApiResponse]:
    yield MockJiraApiResponse


@pytest.fixture
def fake_transitions_response_json(jira_api_templates):
    template = jira_api_templates.get_template(
        JIRA_FAKE_TRANSITIONS_RESPONSE_JSON_TEMPLATE_FILE_NAME,
    )
    rendered_template = template.render()
    yield json.loads(rendered_template)


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
    fake_issue_add_attachment_response,
    fake_transitions_response_json,
):
    caps = {"get": {}, "post": {}, "put": {}}

    # Helper Functions for URL Matching
    def url_contains_fake_issue_id_or_key(url):
        if fake_issue_id in url or fake_issue_key in url:
            return True
        return False

    def url_ends_with_fake_issue_id_or_key(url):
        return bool(url.endswith(fake_issue_id) or url.endswith(fake_issue_key))

    def url_contains_subpath(url, pat):
        return bool(re.match(pat, url))

    def url_is_transitions_endpoint(url):
        # Matches .../issue/ID/transitions or .../issue/KEY/transitions
        return bool(re.search(rf"/issue/({fake_issue_id}|{fake_issue_key})/transitions$", url))

    def url_contains_issue_subpath(url):
        return bool(url_contains_subpath(url, r".+/issue/.+"))

    # Mocked HTTP Methods
    def get(self, url, *args, **kwargs):
        LOGGER.info(f"Patching GET request to URL: {url}")
        caps["get"][url] = (args, kwargs)
        # Check if URL matches specific endpoints
        if url.endswith("/serverInfo"):
            LOGGER.info("Faking Jira serverInfo")
            return MockJiraApiResponse(_json=fake_server_info_json, _status_code=200)
        elif url.endswith("/field"):
            LOGGER.info("Faking Jira fields")
            return MockJiraApiResponse(_json=fake_fields_response_json, _status_code=200)
        elif url.endswith("/search"):
            LOGGER.info("Faking Jira search results")
            return MockJiraApiResponse(_json=fake_search_response_json, _status_code=200)
        elif url_ends_with_fake_issue_id_or_key(url) and url_contains_issue_subpath(url):
            LOGGER.info(f"Faking Jira issue: {url}")
            return MockJiraApiResponse(_json=fake_issue_json, _status_code=200)
        elif url_is_transitions_endpoint(url):
            LOGGER.info(f"Faking Jira GET transitions: {url}")
            return MockJiraApiResponse(_json=fake_transitions_response_json, _status_code=200, _url=url)

        else:
            LOGGER.info(f"Unpatched GET request to: {url}")
            monkeypatch.undo()
            return requests.sessions.Session.get(self=self, url=url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        LOGGER.info(f"Patching POST request to URL: {url}")
        caps["post"][url] = (args, kwargs)

        if url_contains_fake_issue_id_or_key(url) and url.endswith("/comment"):
            return MockJiraApiResponse(
                _json=fake_comment_response_json,
                _status_code=201,
            )
        elif url_contains_fake_issue_id_or_key(url) and url_contains_issue_subpath and url.endswith("/attachments"):
            LOGGER.info(f"Faking Jira file upload: {url}")
            return fake_issue_add_attachment_response
        elif url_is_transitions_endpoint(url):
            LOGGER.info(f"Faking Jira POST transition: {url}")
            return MockJiraApiResponse(
                _status_code=204,  # 204 No Content is for successful transition
                _url=url,
            )
        else:
            LOGGER.info(f"Unpatched POST request to: {url}")
            monkeypatch.undo()
            return requests.sessions.Session.post(self=self, url=url, *args, **kwargs)

    def put(self, url, data, *args, **kwargs):
        LOGGER.info(f"Patching PUT request to URL: {url}")
        caps["put"][url] = (data, args, kwargs)

        if (
            url_contains_fake_issue_id_or_key(url)
            and url_ends_with_fake_issue_id_or_key(url)
            and url_contains_issue_subpath(url)
        ):
            data = json.loads(data)
            _json = fake_issue_json.copy()
            _json["fields"].update(data["fields"])
            return MockJiraApiResponse(_json=_json, _status_code=204)
        else:
            LOGGER.info(f"Unpatched PUT request to: {url}")
            monkeypatch.undo()
            return requests.sessions.Session.put(self, url, *args, **kwargs)

    # Apply the patches
    monkeypatch.setattr(requests.sessions.Session, "get", get)
    monkeypatch.setattr(requests.sessions.Session, "post", post)
    monkeypatch.setattr(requests.sessions.Session, "put", put)

    # Yield the dictionary storing captured calls, if tests need it
    yield caps
