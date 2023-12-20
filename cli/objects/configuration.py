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

from simple_logger.logger import get_logger

from cli.objects.failure_rule import FailureRule
from cli.objects.jira_base import Jira
from cli.objects.rule import Rule


class Configuration:
    def __init__(
        self,
        jira: Jira,
        fail_with_test_failures: bool,
        keep_job_dir: bool,
        verbose_test_failure_reporting: bool,
        verbose_test_failure_reporting_ticket_limit: Optional[int] = 10,
        config_file_path: Union[str, None] = None,
        gitleaks: bool = False,
    ):
        """
        Constructs the Configuration object. This class is mainly used to validate the firewatch configuration given.

        Args:
            jira (Jira): A Jira object used to log in and interact with Jira
            fail_with_test_failures (bool): If a test failure is found, after bugs are filed, firewatch will exit with a non-zero exit code
            keep_job_dir (bool): If true, firewatch will not delete the job directory (/tmp/12345) that is created to hold logs and results for a job following execution.
            verbose_test_failure_reporting (bool): If true, firewatch will report all test failures found in the job.
            verbose_test_failure_reporting_ticket_limit (Optional[int]): Used as a safeguard to prevent firewatch from filing too many bugs. If verbose_test_reporting is set to true, this value will be used to limit the number of bugs filed. Defaults to 10.
            config_file_path (Union[str, None], optional): The firewatch config can be stored in a file or an environment var. Defaults to None.
        """
        self.logger = get_logger(__name__)

        # Jira Connection
        self.jira = jira

        # Get defaults
        self.default_jira_project = self._get_default_jira_project()

        # Boolean value representing if the program should fail if test failures are found.
        self.fail_with_test_failures = fail_with_test_failures

        # Boolean value to decide if firewatch should delete the job directory following execution.
        self.keep_job_dir = keep_job_dir

        # Boolean value to decide if firewatch should report all test failures found in the job.
        self.verbose_test_failure_reporting = verbose_test_failure_reporting
        self.verbose_test_failure_reporting_ticket_limit = (
            verbose_test_failure_reporting_ticket_limit
        )

        # Get the config data
        self.config_data = self._get_config_data(config_file_path=config_file_path)

        # Create the lists of Rule objects using the config data
        self.success_rules = self._get_success_rules(
            rules_list=self.config_data.get("success_rules"),
        )
        self.failure_rules = self._get_failure_rules(
            rules_list=self.config_data.get("failure_rules"),
        )

    def _get_failure_rules(
        self,
        rules_list: Optional[list[dict[Any, Any]]],
    ) -> Optional[list[FailureRule]]:
        """
        Creates a list of FailureRule objects.

        Returns:
            Optional[list[FailureRule]]: A list of FailureRule objects.
        """
        if rules_list is not None:
            rules = []
            for line in rules_list:
                rules.append(FailureRule(rule_dict=line))

            if len(rules) > 0:
                return rules

        self.logger.error(
            'Firewatch config does not contain any "failure_rules". Please populate the configuration and try again.',
        )
        exit(1)

    def _get_success_rules(
        self,
        rules_list: Optional[list[dict[Any, Any]]],
    ) -> Optional[list[Rule]]:
        """
        Creates a list of Rule objects.

        Returns:
            Optional[list[Rule]]: A list of Rule objects.
        """
        if rules_list is not None:
            rules = []
            for line in rules_list:
                rules.append(Rule(rule_dict=line))

            if len(rules) > 0:
                return rules

        return None

    def _get_default_jira_project(self) -> str:
        """
        Gets the default jira project from the $FIREWATCH_DEFAULT_JIRA_PROJECT environment variable.

        Returns:
            str: The default Jira project name defined in environment variable.
        """

        default_project = os.getenv("FIREWATCH_DEFAULT_JIRA_PROJECT")

        # Verify that value is a string if it exists, return
        if isinstance(default_project, str):
            return default_project
        elif not default_project:
            self.logger.error(
                "Environment variable $FIREWATCH_DEFAULT_JIRA_PROJECT is not set, please set the variable and try again.",
            )
            exit(1)
        else:
            self.logger.error(
                f'Value for "$FIREWATCH_DEFAULT_JIRA_PROJECT" is not a string: "{default_project}"',
            )
            exit(1)

    def _get_config_data(self, config_file_path: Optional[str]) -> dict[Any, Any]:
        """
        Gets the config data from either a configuration file or from the FIREWATCH_CONFIG environment variable.
        Will exit with code 1 if either a config file isn't provided (or isn't able to be read) or the FIREWATCH_CONFIG environment variable isn't set.

        Args:
            config_file_path (Optional[str]): The firewatch config can be stored in a file or an environment var.

        Returns:
            dict[Any, Any]: A dictionary object representing the firewatch config data.
        """
        if config_file_path is not None:
            # Read the contents of the config file
            try:
                with open(config_file_path) as file:
                    config_data = file.read()
            except Exception:
                self.logger.error(
                    f"Unable to read configuration file at {config_file_path}. Please verify permissions/path and try again.",
                )
                exit(1)
        else:
            config_data = os.getenv("FIREWATCH_CONFIG")  # type: ignore
            if not config_data:
                self.logger.error(
                    "A configuration file must be provided or the $FIREWATCH_CONFIG environment variable must be set. Please fix error and try again.",
                )
                exit(1)

        # Verify that the config data is properly formatted JSON
        try:
            config_data = json.loads(config_data)
        except json.decoder.JSONDecodeError as error:
            self.logger.error(
                "Firewatch config contains malformed JSON. Please check for missing or additional commas:",
            )
            self.logger.error(error)
            self.logger.info(
                'HINT: If there is a comma following the last rule item in the "rules" list, it should be removed.',
            )
            exit(1)

        return config_data  # type: ignore
