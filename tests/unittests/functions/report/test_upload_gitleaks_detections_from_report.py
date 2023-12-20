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
import os

import pytest
import requests

from cli.objects.configuration import Configuration
from cli.objects.jira_base import Jira
from cli.objects.job import Job
from cli.report.report import Report


@pytest.fixture(autouse=True)
def setup_test_environment(
    assert_build_id_in_env,
    assert_patterns_server_token_in_env,
    assert_jira_token_in_env,
    assert_default_jira_project_in_env,
    assert_default_jira_epic_in_env,
    assert_artifact_dir_in_env,
    assert_artifact_dir_exists,
    assert_patterns_server_token_file_exists,
    assert_jira_config_file_exists,
    assert_firewatch_config_in_env,
    assert_job_dir_exists,
    assert_job_log_artifacts_exist,
    assert_job_junit_artifacts_exist,
    assert_fake_secret_in_job_logs_dir_exists,
    assert_fake_secret_in_job_junit_dir_exists,
    patch_gitleaks_config_patterns_server_token_path,
):
    ...


def test_upload_gitleaks_detection_from_report(
    jira_config_path,
    build_id,
    patch_job_log_dir,
    patch_job_junit_dir,
    patch_gitleaks_config_job_dir,
    fake_log_secret_path,
    fake_junit_secret_path,
):
    jira = Jira(jira_config_path=jira_config_path.as_posix())

    firewatch_config = Configuration(
        jira=jira,
        fail_with_test_failures=False,
        keep_job_dir=True,
        verbose_test_failure_reporting=False,
        gitleaks=True,
    )

    job = Job(
        name="periodic-ci-windup-windup-ui-tests-v1.1-mtr-ocp4.14-lp-interop-mtr-interop-aws",
        name_safe="mtr-interop-aws",
        build_id=build_id,
        gcs_bucket="origin-ci-test",
        firewatch_config=firewatch_config,
    )

    report = Report(firewatch_config=firewatch_config, job=job)

    assert len(report._bugs_filed) or len(report._duplicate_bugs_commented)

    last_issue_key = (report._bugs_filed + report._duplicate_bugs_commented).pop()

    attachments = requests.get(
        f"https://issues.stage.redhat.com/rest/api/2/issue/{last_issue_key}",
        headers={"Authorization": f"Bearer {os.getenv('JIRA_TOKEN')}"},
        proxies={
            "http": "http://squid.corp.redhat.com:3128",
            "https": "http://squid.corp.redhat.com:3128",
        },
    ).json()["fields"]["attachment"]

    attachment_file_names = [c["content"].split("/").pop() for c in attachments]

    for exp in [
        fake_log_secret_path.name,
        fake_junit_secret_path.name,
        "gitleaks_report.json",
    ]:
        assert exp in attachment_file_names
