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
class TestGetSuccessRules(ConfigurationBaseTest):
    @patch.dict(
        os.environ,
        {
            "FIREWATCH_CONFIG": '{"success_rules": [{"jira_project": "PROJECT", "jira_epic": "PROJECT-123"}], "failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}',
        },
    )
    def test_configuration_gets_success_rules_with_valid_input(self):
        config = Configuration(self.mock_jira, False, False, False)
        success_rules = config._get_success_rules(
            config.config_data.get("success_rules"),
        )
        assert len(success_rules) == 1
        assert success_rules[0].jira_project == "PROJECT"
        assert success_rules[0].jira_epic == "PROJECT-123"

    @patch.dict(
        os.environ,
        {
            "FIREWATCH_CONFIG": '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}',
        },
    )
    def test_configuration_gets_success_rules_with_no_rules(self):
        config = Configuration(self.mock_jira, False, False, False)
        success_rules = config._get_success_rules(
            config.config_data.get("success_rules"),
        )
        assert success_rules is None
