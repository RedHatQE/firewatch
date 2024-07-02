import json
import os
import fnmatch
from typing import Any
from typing import Optional
from typing import Union

from simple_logger.logger import get_logger

from src.objects.failure_rule import FailureRule
from src.objects.jira_base import Jira
from src.objects.rule import Rule


def read_base_config_file(path: str) -> str:
    from urllib.request import urlopen

    try:
        response = urlopen(path)
        response_data = response.read()
        return response_data
    # Path is not a URL type
    except ValueError:
        # Read the contents of the config file
        try:
            with open(path) as file:
                base_config_str = file.read()
                return base_config_str
        except Exception:
            pass
    # Path is an invalid or unreadable URL
    except Exception:
        pass

    return None  # type: ignore


class Configuration:
    def __init__(
        self,
        jira: Jira,
        fail_with_test_failures: bool,
        keep_job_dir: bool,
        verbose_test_failure_reporting: bool,
        verbose_test_failure_reporting_ticket_limit: Optional[int] = 10,
        config_file_path: Union[str, None] = None,
        additional_lables_file: Optional[str] = None,
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
            additional_lables_file (Optional[str]): If set, the filepath provided will be parsed for additional labels. Each label should be separated by a new line.
        """
        self.logger = get_logger(__name__)

        self.jira = jira
        self.default_jira_project = self._get_default_jira_project()
        self.fail_with_test_failures = fail_with_test_failures
        self.keep_job_dir = keep_job_dir
        self.additional_labels_file = additional_lables_file
        self.verbose_test_failure_reporting = verbose_test_failure_reporting
        self.verbose_test_failure_reporting_ticket_limit = verbose_test_failure_reporting_ticket_limit
        self.config_data = self._get_config_data(base_config_file_path=config_file_path)
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
                "Environment variable $FIREWATCH_DEFAULT_JIRA_PROJECT is not set, please set the variable and try "
                "again.",
            )
            exit(1)
        else:
            self.logger.error(
                f'Value for "$FIREWATCH_DEFAULT_JIRA_PROJECT" is not a string: "{default_project}"',
            )
            exit(1)

    def _get_config_data(self, base_config_file_path: Optional[str]) -> dict[Any, Any]:
        """
        Gets the config data from either a configuration file or from the FIREWATCH_CONFIG environment variable or
        both.
        Will exit with code 1 if both a config file isn't provided (or isn't readable) or the FIREWATCH_CONFIG environment variable isn't set.
        The configuration file is considered as the basis of the configuration data,
        And it will be overridden and expended by the additional set of rules that will be applied to the env var.

        Args:
            base_config_file_path (Optional[str]): The firewatch config can be stored in a file or url path.

        Returns:
            dict[Any, Any]: A dictionary object representing the firewatch config data.
        """
        base_config_str = ""
        base_config_data = {}
        steps_map = {}

        if base_config_file_path is not None:
            base_config_str = read_base_config_file(path=base_config_file_path)
            if not base_config_str:
                self.logger.error(
                    f"Unable to read configuration file at {base_config_file_path}."
                    f"\nPlease verify permissions/path and try again.",
                )
                exit(1)

        # Verify that the config data is properly formatted JSON
        try:
            if base_config_str:
                base_config_data = json.loads(base_config_str)

            # Will update base config with additional logic from env vars
            additional_config_data = json.loads(os.getenv("FIREWATCH_CONFIG") or "{}")

        except json.decoder.JSONDecodeError as error:
            self.logger.error(
                "Firewatch config contains malformed JSON. Please check for missing or additional commas:",
            )
            self.logger.error(error)
            self.logger.info(
                'HINT: If there is a comma following the last rule item in the "rules" list, it should be removed.',
            )
            exit(1)

        # If a step exists in base config, and mentioned by use, update and override it using unpack
        config_data = {**base_config_data, **additional_config_data}

        if not config_data:
            self.logger.error(
                "A configuration file must be provided or the $FIREWATCH_CONFIG environment variable must be set. "
                "Please fix error and try again.",
            )
            exit(1)

        # Include patterns from base config and expend user input
        for key in ["failure_rules", "success_rules"]:
            if key in config_data:
                steps_map = {d.get("step"): d for d in config_data[key]}
            if key in base_config_data:
                for step_dict in base_config_data[key]:
                    step = step_dict.get("step")
                    if step and step not in steps_map.keys():
                        # Check if user didn't mention a pattern that already overrides this step
                        if not any(fnmatch.fnmatch(step, k) for k in steps_map.keys()):
                            if key not in config_data:
                                config_data[key] = step_dict
                            else:
                                config_data[key].append(step_dict)
                            steps_map[step] = step_dict  # Also update the steps_map to include this step
        return config_data  # type: ignore
