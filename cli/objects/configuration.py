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
from typing import Optional
from typing import Union

from cli.objects.jira_base import Jira


class Configuration:
    def __init__(self, jira: Jira, config_file_path: Union[str, None] = None):
        """
        Used to construct the Configuration object. This class is mainly used to validate the firewatch configuration given

        :param config_file_path: An optional value, the firewatch config can be stored in a file or an environment var
        """
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(
            __name__,
        )

        # Jira Connection
        self.jira = jira

        # Valid failure_type(s)
        self.valid_failure_types = ["pod_failure", "test_failure", "all"]

        # Check if DEFAULT_JIRA_PROJECT
        self.default_jira_project = (
            os.getenv(
                "FIREWATCH_DEFAULT_JIRA_PROJECT",
            )
            or "NONE"
        )

        # Check if config_file_path was provided
        if config_file_path is not None:
            # Read the contents of the file
            with open(config_file_path) as file:
                self.config_data = file.read()
                self.rules = json.loads(self.config_data)
        else:
            # Check if the environment variable FIREWATCH_CONFIG is defined
            self.config_data = os.getenv("FIREWATCH_CONFIG")  # type: ignore
            self.rules = json.loads(self.config_data)

        if not self.config_valid():
            exit(1)

    def config_valid(self) -> bool:
        """
        Used to validate firewatch configuration file.

        :returns: A boolean value. True = valid configuration, False = invalid configuration
        """
        for rule in self.rules:
            step_value_valid = self.step_value_valid(rule["step"])
            failure_type_value_valid = self.failure_type_value_valid(
                rule["failure_type"],
            )
            classification_value_valid = self.classification_value_valid(
                rule["classification"],
            )
            jira_project_value_valid = self.jira_project_value_valid(
                rule["jira_project"],
            )

            if (
                step_value_valid
                and failure_type_value_valid
                and classification_value_valid
                and jira_project_value_valid
            ):
                self.logger.info(
                    "A valid Firewatch config has been found and verified!",
                )
                return True
            else:
                self.logger.error(
                    "The firewatch config that has been provided is not valid...",
                )
                return False
        return False

    def step_value_valid(self, step_value: str) -> bool:
        """
        Used to validate that the "step" value in a firewatch configuration line is valid.

        :param step_value: The string of the value you'd like to validate

        :returns: A boolean value. True = valid, False = invalid
        """
        # Check if step_value is a valid string and not None
        if not value_is_string_and_not_none(step_value):
            self.logger.error(
                f'No value found for "step" or a non-string value was given... ',
            )
            return False

        # Check if step_value contains any spaces
        if " " in step_value:
            self.logger.error(
                f'Space(s) found in config value "step": "{step_value}"... Please remove spaces.',
            )
            return False

        return True

    def failure_type_value_valid(self, failure_type_value: str) -> bool:
        """
        Used to validate that the "failure_type" value in a firewatch configuration line is valid.
        The failure_type value should be in the self.valid_failure_types list

        :param failure_type_value: The string of the value you'd like to validate

        :returns: A boolean value. True = valid, False = invalid
        """

        # Check if failure_type_value is a valid string and not None
        if not value_is_string_and_not_none(failure_type_value):
            self.logger.error(
                f'No value found for "failure_type" or a non-string value was given... ',
            )
            return False

        # Check if failure_type_value is in self.valid_failure_types
        if failure_type_value not in self.valid_failure_types:
            return False

        return True

    def classification_value_valid(self, classification_value: str) -> bool:
        """
        Used to validate that the "failure_type" value in a firewatch configuration line is valid.
        Should be a valid string and not None

        :param classification_value: The string of the value you'd like to validate

        :returns: A boolean value. True = valid, False = invalid
        """
        # Check if classification_value is a valid string and not None
        if not value_is_string_and_not_none(classification_value):
            self.logger.error(
                f'No value found for "classification" or a non-string value was given... ',
            )
            return False

        return True

    def jira_project_value_valid(self, jira_project_value: str) -> bool:
        """
        Used to validate that the "jira_project_value" value in a firewatch configuration line is valid.
         - Should be a valid string and not None
         - Project should exist in the Jira server

        :param jira_project_value: The string of the value you'd like to validate

        :returns: A boolean value. True = valid, False = invalid
        """
        # Check if jira_project_value is a valid string and not None
        if not value_is_string_and_not_none(jira_project_value):
            self.logger.error(
                f'No value found for "jira_project" or a non-string value was given... ',
            )
            return False

        if not self.jira.project_exists(project_key=jira_project_value):
            self.logger.error(f"Jira project {jira_project_value} does not exist...")
            return False

        return True


def value_is_string_and_not_none(value: str) -> bool:
    """
    Used by other functions in this class to validate that a value in the firewatch config is a string and not None

    :param value: The string of the value you'd like to validate

    :returns: A boolean value. True = value is string and not None, False = value is not a string or is None
    """
    if value is None or not isinstance(value, str):
        return False
    return True
