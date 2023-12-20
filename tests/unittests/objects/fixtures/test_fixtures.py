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
import pytest

from cli.objects.configuration import Configuration
from cli.objects.jira_base import Jira
from cli.objects.job import Job
from cli.report import Report


@pytest.fixture(autouse=True)
def setup_test_environment(
    assert_jira_token_in_env,
    assert_jira_config_file_exists,
    assert_default_jira_project_in_env,
    assert_firewatch_config_in_env,
    patch_job_junit_dir,
    patch_job_log_dir,
    patch_jira,
    assert_build_id_in_env,
    assert_artifact_dir_exists,
    assert_artifact_dir_in_env,
    patch_gitleaks_config_job_dir,
    assert_job_dir_exists,
    assert_job_log_artifacts_exist,
    assert_job_junit_artifacts_exist,
    assert_patterns_server_token_file_exists,
    patch_gitleaks_config_patterns_server_token_path,
):
    ...


def test_get_firewatch_config_instance_from_fixture(firewatch_config):
    assert isinstance(firewatch_config, Configuration)


def test_get_job_instance_from_fixture(job):
    assert isinstance(job, Job)


def test_get_jira_instance_from_fixture(jira):
    assert isinstance(jira, Jira)


def test_get_report_with_gitleaks_enabled_from_fixture(report_with_gitleaks):
    assert isinstance(report_with_gitleaks, Report)


def test_get_report_with_gitleaks_with_no_leaks_from_fixture(
    report_with_gitleaks_no_leaks,
):
    report_with_gitleaks_no_leaks.gitleaks_config.start_detect_scan()
    assert (
        not report_with_gitleaks_no_leaks.gitleaks_config._gitleaks_report_path.exists()
    )


def test_get_report_with_gitleaks_with_leaks_from_fixture(
    report_with_gitleaks_with_leaks,
):
    report_with_gitleaks_with_leaks.gitleaks_config.start_detect_scan()
    assert (
        report_with_gitleaks_with_leaks.gitleaks_config._gitleaks_report_path.is_file()
    )
