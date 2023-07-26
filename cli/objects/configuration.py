#
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
import json
import logging
import os
from typing import Any
from typing import Optional
from typing import Union

from cli.objects.jira_base import Jira
from cli.objects.rule import Rule


class Configuration:
    def __init__(
        self,
        jira: Jira,
        fail_with_test_failures: bool,
        config_file_path: Union[str, None] = None,
    ):
        """
        Used to construct the Configuration object. This class is mainly used to validate the firewatch configuration given.

        :param jira: A Jira object used to log in and interact with Jira
        :param fail_with_test_failures: A boolean value. If a test failure is found, after bugs are filed, firewatch will exit with a non-zero exit code
        :param config_file_path: An optional value, the firewatch config can be stored in a file or an environment var.
        """
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(
            __name__,
        )

        # Jira Connection
        self.jira = jira

        # Check if DEFAULT_JIRA_PROJECT
        self.default_jira_project = self._get_default_jira_project()

        # Boolean value representing if the program should fail if test failures are found.
        self.fail_with_test_failures = fail_with_test_failures

        # Get the config data
        self.config_data = self._get_config_data(config_file_path=config_file_path)

        # Create the list of Rule objects using the config data
        self.rules = self._get_rules(json.loads(self.config_data))

    def _get_rules(self, rules_json: list[dict[Any, Any]]) -> Optional[list[Rule]]:
        """
        Used to create a list of Rule objects.

        :param rules_json: The JSON list of rules provided by the user.
        :return: A list of Rule objects.
        """
        rules = []
        for line in rules_json:
            rules.append(Rule(line))
        if len(rules) > 0:
            return rules
        else:
            self.logger.error(
                "Firewatch config is empty, please populate the configuration and try again.",
            )
            exit(1)

    def _get_default_jira_project(self) -> str:
        """
        Used to get the default jira project from the FIREWATCH_DEFAULT_JIRA_PROJECT environment variable
        :return: The string of the default environment variable.
        """

        default_project = os.getenv("FIREWATCH_DEFAULT_JIRA_PROJECT")

        if default_project:
            return default_project
        else:
            self.logger.error(
                "Environment variable $FIREWATCH_DEFAULT_JIRA_PROJECT is not set, please set the variable and try again.",
            )
            exit(1)

    def _get_config_data(self, config_file_path: Optional[str]) -> str:
        """"""
        if config_file_path is not None:
            # Read the contents of the config file
            try:
                with open(config_file_path) as file:
                    config_data = file.read()
                    return config_data
            except Exception:
                self.logger.error(
                    f"Unable to read configuration file at {config_file_path}. Please verify permissions/path and try again.",
                )
                exit(1)
        else:
            config_data = os.getenv("FIREWATCH_CONFIG")  # type: ignore
            if config_data:
                return config_data
            else:
                self.logger.error(
                    "A configuration file must be provided or the $FIREWATCH_CONFIG environment variable must be set. Please fix error and try again.",
                )
                exit(1)
