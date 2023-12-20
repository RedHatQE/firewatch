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
from unittest.mock import patch

from cli.objects.configuration import Configuration
from tests.unittests.objects.configuration.configuration_base_test import (
    ConfigurationBaseTest,
)


@patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "TEST"})
@patch.dict(
    os.environ,
    {
        "FIREWATCH_CONFIG": '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}',
    },
)
class TestConfiguration(ConfigurationBaseTest):
    def test_configuration_initializes_with_valid_input(self):
        config = Configuration(
            jira=self.mock_jira,
            fail_with_test_failures=True,
            keep_job_dir=True,
            verbose_test_failure_reporting=True,
            verbose_test_failure_reporting_ticket_limit=10,
            config_file_path=None,
        )
        assert config.fail_with_test_failures
        assert config.keep_job_dir
        assert config.verbose_test_failure_reporting
        assert config.verbose_test_failure_reporting_ticket_limit == 10
