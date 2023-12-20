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
import tempfile
from unittest.mock import patch

from cli.objects.configuration import Configuration
from tests.unittests.objects.configuration.configuration_base_test import (
    ConfigurationBaseTest,
)


@patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "TEST"})
class TestGetConfigData(ConfigurationBaseTest):
    def test_configuration_gets_config_data_with_valid_file_path(self):
        valid_config_data = '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}'
        with tempfile.TemporaryDirectory() as tmp_path:
            config_file = os.path.join(tmp_path, "config.json")
            with open(config_file, "w") as f:
                f.write(valid_config_data)
            config = Configuration(self.mock_jira, True, True, True, 10, config_file)
            assert config.config_data == {
                "failure_rules": [
                    {
                        "step": "step1",
                        "failure_type": "pod_failure",
                        "classification": "none",
                    },
                ],
            }

    def test_configuration_gets_config_data_with_invalid_file_path(self):
        with self.assertRaises(SystemExit):
            Configuration(self.mock_jira, True, True, True, 10, "/tmp/invalid.json")

    @patch.dict(
        os.environ,
        {
            "FIREWATCH_CONFIG": '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}',
        },
    )
    def test_configuration_gets_config_data_with_valid_env_var(self):
        config = Configuration(self.mock_jira, True, True, True, 10, None)
        assert config.config_data == {
            "failure_rules": [
                {
                    "step": "step1",
                    "failure_type": "pod_failure",
                    "classification": "none",
                },
            ],
        }

    def test_configuration_gets_config_data_with_no_env_var(self):
        if "FIREWATCH_CONFIG" in os.environ:
            del os.environ["FIREWATCH_CONFIG"]
        with self.assertRaises(SystemExit):
            Configuration(self.mock_jira, True, True, True, 10, None)
