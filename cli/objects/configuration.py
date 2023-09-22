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
import os
from typing import Any
from typing import Optional
from typing import Union

import click
from simple_logger.logger import get_logger

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
        Constructs the Configuration object. This class is mainly used to validate the firewatch configuration given.

        Args:
            jira (Jira): A Jira object used to log in and interact with Jira
            fail_with_test_failures (bool): If a test failure is found, after bugs are filed, firewatch will exit with a non-zero exit code
            config_file_path (Union[str, None], optional): The firewatch config can be stored in a file or an environment var. Defaults to None.
        """
        self.logger = get_logger(__name__)

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
        Creates a list of Rule objects.

        Args:
            rules_json (list[dict[Any, Any]]): The JSON list of rules provided by the user.

        Returns:
            Optional[list[Rule]]: A list of Rule objects.
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
            raise click.abort()

    def _get_default_jira_project(self) -> str:
        """
        Gets the default jira project from the FIREWATCH_DEFAULT_JIRA_PROJECT environment variable.

        Returns:
            str: The string of the default environment variable.
        """

        default_project = os.getenv("FIREWATCH_DEFAULT_JIRA_PROJECT")

        if default_project:
            return default_project
        else:
            self.logger.error(
                "Environment variable $FIREWATCH_DEFAULT_JIRA_PROJECT is not set, please set the variable and try again.",
            )
            raise click.abort()

    def _get_config_data(self, config_file_path: Optional[str]) -> str:
        """
        Gets the config data from either a configuration file or from the FIREWATCH_CONFIG environment variable.
        Will exit with code 1 if either a config file isn't provided (or isn't able to be read) or the FIREWATCH_CONFIG environment variable isn't set.

        Args:
            config_file_path (Optional[str]): The firewatch config can be stored in a file or an environment var.

        Returns:
            str: A string object representing the firewatch config data.
        """
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
                raise click.abort()
        else:
            config_data = os.getenv("FIREWATCH_CONFIG")  # type: ignore
            if config_data:
                return config_data
            else:
                self.logger.error(
                    "A configuration file must be provided or the $FIREWATCH_CONFIG environment variable must be set. Please fix error and try again.",
                )
                raise click.abort()
