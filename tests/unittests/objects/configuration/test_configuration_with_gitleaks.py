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


@pytest.fixture(autouse=True)
def setup_tests(
    assert_jira_config_file_exists,
    assert_default_jira_project_in_env,
    assert_firewatch_config_in_env,
):
    ...


def test_init_configuration_with_gitleaks_enabled(jira):
    config = Configuration(
        verbose_test_failure_reporting=False,
        keep_job_dir=True,
        fail_with_test_failures=False,
        jira=jira,
        gitleaks=True,
    )
    assert isinstance(config, Configuration)
