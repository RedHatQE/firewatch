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


@pytest.fixture(autouse=True)
def setup_test_environment(
    assert_jira_token_in_env,
    assert_jira_config_file_exists,
    assert_default_jira_project_in_env,
    assert_firewatch_config_in_env,
    patch_job_junit_dir,
    patch_job_log_dir,
    assert_build_id_in_env,
    assert_artifact_dir_exists,
    assert_artifact_dir_in_env,
    assert_job_dir_exists,
):
    ...


def test_get_firewatch_config_instance_from_fixture(firewatch_config):
    assert isinstance(firewatch_config, Configuration)


def test_get_job_instance_from_fixture(job):
    assert isinstance(job, Job)


def test_get_jira_instance_from_fixture(jira):
    assert isinstance(jira, Jira)
