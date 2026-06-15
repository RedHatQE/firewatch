#
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
from pathlib import Path

import pytest
from dotenv import load_dotenv
import simple_logger.logger
from jinja2 import Environment
from jinja2 import select_autoescape
from jinja2.loaders import FileSystemLoader

from src.objects.jira_base import Jira
from src.report.constants import JOB_PASSED_SINCE_TICKET_CREATED_LABEL

_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env", override=False)

logger = simple_logger.logger.get_logger(__name__)


@pytest.fixture
def job_dir(build_id):
    yield Path("/tmp").joinpath(build_id)


@pytest.fixture
def jira_token():
    res = os.getenv("JIRA_TOKEN")
    assert res, "JIRA_TOKEN was not found in environment"
    yield res


@pytest.fixture
def jira_email():
    yield os.getenv("JIRA_EMAIL")


@pytest.fixture
def jira_server_url():
    res = os.getenv("JIRA_SERVER_URL")
    assert res, "JIRA_SERVER_URL was not found in environment"
    yield res


@pytest.fixture
def firewatch_config_path(tmp_path):
    path = tmp_path.joinpath("firewatch_config.json")
    path.parent.mkdir(exist_ok=True, parents=True)
    path.write_text(
        json.dumps(
            {
                "failure_rules": [
                    {
                        "step": "*",
                        "failure_type": "all",
                        "classification": "e2e-open-bugs fixture",
                        "group": {"name": "cluster", "priority": 1},
                        "jira_additional_labels": ["!default"],
                    },
                ],
            },
        ),
    )
    logger.info(f"wrote firewatch config to {path.as_uri()}")
    yield path


@pytest.fixture(autouse=True)
def jira_project(monkeypatch):
    monkeypatch.setenv("FIREWATCH_DEFAULT_JIRA_PROJECT", "LPINTEROP")


@pytest.fixture(autouse=True)
def firewatch_default_jira_additional_labels(monkeypatch):
    monkeypatch.setenv("FIREWATCH_DEFAULT_JIRA_ADDITIONAL_LABELS", '["default-label"]')


@pytest.fixture(autouse=True)
def templates_path():
    yield Path(__file__).parent.joinpath("templates")


@pytest.fixture(autouse=True)
def jira_configs_templates_path(templates_path):
    yield templates_path.joinpath("jira_configs")


@pytest.fixture(autouse=True)
def firewatch_configs_templates_path(templates_path):
    yield templates_path.joinpath("firewatch_configs")


@pytest.fixture(autouse=True)
def jira_config_path(tmp_path, jira_configs_templates_path, jira_token, jira_email, jira_server_url):
    path = tmp_path.joinpath("jira.config")
    path.parent.mkdir(exist_ok=True, parents=True)
    loader = Environment(
        loader=FileSystemLoader(jira_configs_templates_path.as_posix()),
        autoescape=select_autoescape(),
    )
    template = loader.get_template("jira.config.j2")
    rendered_template = template.render(token=jira_token, email=jira_email, server_url=jira_server_url)
    path.write_text(rendered_template)
    logger.info(f"wrote Jira config to {path.as_uri()}")
    yield path


@pytest.fixture
def job_log_dir(job_dir):
    yield job_dir / "logs"


@pytest.fixture
def job_artifacts_dir(job_dir):
    yield job_dir / "artifacts"


@pytest.fixture
def tmp_job_dir(tmp_path, build_id):
    yield tmp_path / build_id


@pytest.fixture
def jira_api_issue_endpoint_url(jira_server_url):
    yield f"{jira_server_url}/rest/api/3/issue"


@pytest.fixture
def jira(jira_config_path):
    yield Jira(jira_config_path.as_posix())


@pytest.fixture
def register_jira_issues_for_e2e_cleanup(jira):
    keys: list[str] = []

    def register(*issue_keys: str) -> None:
        for k in issue_keys:
            if k and k not in keys:
                keys.append(k)

    yield register
    target_label = JOB_PASSED_SINCE_TICKET_CREATED_LABEL
    for issue_key in keys:
        try:
            issue = jira.get_issue_by_id_or_key(issue_key)
            if target_label in issue.fields.labels:
                logger.info('removing label "%s" from %s', target_label, issue_key)
                issue.update(update={"labels": [{"remove": target_label}]})
        except Exception as exc:
            logger.warning(
                "e2e cleanup: could not strip label from %s: %s",
                issue_key,
                exc,
            )
        jira.close_issue(issue_key)
