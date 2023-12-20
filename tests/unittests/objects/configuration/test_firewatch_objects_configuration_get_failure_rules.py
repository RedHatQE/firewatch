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
class TestGetFailureRules(ConfigurationBaseTest):
    @patch.dict(
        os.environ,
        {
            "FIREWATCH_CONFIG": '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}',
        },
    )
    def test_configuration_gets_failure_rules_with_valid_input(self):
        config = Configuration(self.mock_jira, False, False, False)
        failure_rules = config._get_failure_rules(
            config.config_data.get("failure_rules"),
        )
        assert len(failure_rules) == 1
        assert failure_rules[0].step == "step1"
        assert failure_rules[0].failure_type == "pod_failure"
        assert failure_rules[0].classification == "none"
