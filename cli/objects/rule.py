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
import re
from typing import Any
from typing import Optional

from simple_logger.logger import get_logger


class Rule:
    def __init__(self, rule_dict: dict[Any, Any]) -> None:
        """
        Initializes the Rule object.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a firewatch rule.
        """

        self.logger = get_logger(__name__)

        # Build the rule using the rule_dict
        self.job_success = self._get_success_rule(rule_dict)
        self.jira_project = self._get_jira_project(rule_dict)
        self.jira_epic = self._get_jira_epic(rule_dict)
        if not self.job_success:
            self.step = self._get_step(rule_dict)
            self.failure_type = self._get_failure_type(rule_dict)
            self.classification = self._get_classification(rule_dict)
            self.jira_component = self._get_jira_component(rule_dict)
            self.jira_affects_version = self._get_jira_affects_version(rule_dict)
            self.jira_additional_labels = self._get_jira_additional_labels(rule_dict)
            self.jira_assignee = self._get_jira_assignee(rule_dict)
            self.jira_priority = self._get_jira_priority(rule_dict)
            self.group_name = self._get_group_name(rule_dict)
            self.group_priority = self._get_group_priority(rule_dict)
            self.ignore = self._get_ignore(rule_dict)

    def _get_step(self, rule_dict: dict[Any, Any]) -> str:
        """
        Determines the step that a firewatch rule pertains to.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            str: A string value representing the full or partial name of a step that this firewatch rule pertains to.
        """
        step = rule_dict.get("step")

        if not step:
            self.logger.error(
                f'Unable to find value for "step" in firewatch rule: "{rule_dict}"',
            )
            exit(1)

        if isinstance(step, str):
            return step
        else:
            self.logger.error(
                f'Value for "step" is not a string in firewatch rule: "{rule_dict}"',
            )
            exit(1)

    def _get_failure_type(self, rule_dict: dict[Any, Any]) -> str:
        """
        Determines the failure_type of a firewatch rule.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            str: A string value representing the failure_type of a rule.
        """
        valid_failure_types = ["pod_failure", "test_failure", "all", "!none"]

        failure_type = rule_dict.get("failure_type")

        if not failure_type:
            self.logger.error(
                f'Unable to find value for "failure_type" in firewatch rule: "{rule_dict}"',
            )
            exit(1)

        if isinstance(failure_type, str):
            if failure_type.lower() in valid_failure_types:
                return failure_type.lower()
            else:
                self.logger.error(
                    f'Value for "failure_type" is not a valid failure type (pod_failure, test_failure, or all) in firewatch rule: "{rule_dict}"',
                )
                exit(1)
        else:
            self.logger.error(
                f'Value for "failure_type" is not a string in firewatch rule: "{rule_dict}"',
            )
            exit(1)

    def _get_classification(self, rule_dict: dict[Any, Any]) -> str:
        """
        Determines the classification of a firewatch rule.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            str: A string value representing the classification of a rule.
        """
        classification = rule_dict.get("classification")

        if not classification:
            self.logger.error(
                f'Unable to find value for "classification" in firewatch rule: "{rule_dict}"',
            )
            exit(1)

        if isinstance(classification, str):
            return classification
        else:
            self.logger.error(
                f'Value for "classification" is not a string in firewatch rule: "{rule_dict}"',
            )
            exit(1)

    def _get_jira_project(self, rule_dict: dict[Any, Any]) -> str:
        """
        Determines the Jira Project defined in a firewatch rule.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            str: A string value representing the jira_project for a firewatch rule.
        """
        jira_project = rule_dict.get("jira_project")

        if not jira_project:
            self.logger.error(
                f'Unable to find value for "jira_project" in firewatch rule: "{rule_dict}"',
            )
            exit(1)

        if isinstance(jira_project, str):
            return jira_project
        else:
            self.logger.error(
                f'Value for "jira_project" is not a string in firewatch rule: "{rule_dict}"',
            )
            exit(1)

    def _get_jira_epic(self, rule_dict: dict[Any, Any]) -> Optional[str]:
        """
        Determines if a Jira Epic is defined in a rule. If it is, validate it and return the string.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            Optional[str]: A string of the Jira epic to use in a firewatch rule. If one is not defined, return None
        """

        jira_epic = rule_dict.get("jira_epic")

        if isinstance(jira_epic, str) or not jira_epic:
            return jira_epic

        self.logger.error(
            f'Value for "jira_epic" is not a string in firewatch rule: "{rule_dict}"',
        )
        exit(1)

    def _get_jira_component(self, rule_dict: dict[Any, Any]) -> Optional[list[str]]:
        """
        Determines if one or more Jira Components are defined in firewatch rule. If it is, return a list of components.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            Optional[list[str]]: A list of strings representing the component(s) defined in a firewatch rule. If not defined, return None
        """
        components = []

        jira_component = rule_dict.get("jira_component")

        if isinstance(jira_component, str):
            components.append(jira_component)
            return components
        elif isinstance(jira_component, list):
            for component in jira_component:
                if isinstance(component, str):
                    components.append(component)
                else:
                    self.logger.error(
                        f'Component "{component}" in "jira_component" is not a string in firewatch rule: "{rule_dict}"',
                    )
                    exit(1)
            return components
        elif not jira_component:
            return jira_component

        self.logger.error(
            f'Value for "jira_component" must be either a list of strings (multiple components) or a string value (single component) in firewatch rule: "{rule_dict}"',
        )
        exit(1)

    def _get_jira_affects_version(self, rule_dict: dict[Any, Any]) -> Optional[str]:
        """
        Determines if the jira_affects_version value is set, if so, returns the string of that version affected.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            Optional[str]: A string value representing the affected version for a firewatch rule.
        """

        jira_affects_version = rule_dict.get("jira_affects_version")

        if isinstance(jira_affects_version, str) or not jira_affects_version:
            return jira_affects_version

        self.logger.error(
            f'Value for "jira_affects_version" is not a string in firewatch rule: "{rule_dict}"',
        )
        exit(1)

    def _get_jira_additional_labels(
        self,
        rule_dict: dict[Any, Any],
    ) -> Optional[list[str]]:
        """
        Determines if the jira_additional_labels value is set, if so, returns a list of strings of additional labels.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            Optional[list[str]]: A list of strings representing additional labels.
        """
        labels = []
        jira_additional_labels = rule_dict.get("jira_additional_labels")

        if isinstance(jira_additional_labels, list):
            for label in jira_additional_labels:
                if isinstance(label, str):
                    if " " in label:
                        self.logger.error(
                            f'Label "{label}" in rule {rule_dict} contains spaces. Remove spaces and try again.',
                        )
                        exit(1)
                    else:
                        labels.append(label)
                else:
                    self.logger.error(
                        f'Label "{label}" in "jira_additional_labels" is not a string in firewatch rule: "{rule_dict}"',
                    )
                    exit(1)
            return labels
        elif not jira_additional_labels:
            return jira_additional_labels

        self.logger.error(
            f'Value for "jira_additional_labels" is not a list of strings (["label1", "label2"]) in firewatch rule: "{rule_dict}"',
        )
        exit(1)

    def _get_jira_assignee(self, rule_dict: dict[Any, Any]) -> Optional[str]:
        """
        Determines if a Jira Assignee is defined in a rule. If it is, validate it and return the string.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            Optional[str]: A string of the Jira assignee to use in a firewatch rule. If one is not defined, return None
        """

        jira_assignee = rule_dict.get("jira_assignee")

        if isinstance(jira_assignee, str):
            regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"  # Used to check if email is valid
            if re.fullmatch(regex, jira_assignee):
                return jira_assignee
            else:
                self.logger.error(
                    f'Value for "jira_assignee" is not an email address in firewatch rule: "{rule_dict}"',
                )
                exit(1)
        elif not jira_assignee:
            return jira_assignee

        self.logger.error(
            f'Value for "jira_assignee" is not a string in firewatch rule: "{rule_dict}"',
        )
        exit(1)

    def _get_jira_priority(self, rule_dict: dict[Any, Any]) -> Optional[str]:
        """
        Determines if a Jira priority is defined in a rule. If it is, validate it and return the string.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            Optional[str]: A string of the Jira priority to use in a firewatch rule. If one is not defined, return None
        """
        valid_priority_values = ["Blocker", "Critical", "Major", "Normal", "Minor"]

        jira_priority = rule_dict.get("jira_priority")

        if isinstance(jira_priority, str):
            jira_priority = jira_priority.lower().capitalize()

            if jira_priority in valid_priority_values:
                return jira_priority
            else:
                self.logger.error(
                    f'Value for "jira_priority" is not a valid value ({valid_priority_values}) in firewatch rule: "{rule_dict}" ',
                )
                exit(1)
        elif not jira_priority:
            return jira_priority

        self.logger.error(
            f'Value for "jira_priority" is not a string in firewatch rule: "{rule_dict}"',
        )
        exit(1)

    def _get_group_name(self, rule_dict: dict[Any, Any]) -> Optional[str]:
        """
        Determines if a group name is defined in a rule. If it is, validate it and return the string.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            Optional[str]: A string representing the group name. If one is not defined, return None
        """
        group_name = rule_dict.get("group", {}).get("name")
        if isinstance(group_name, str) or not group_name:
            return group_name

        self.logger.error(
            f'Value for "name" in the "group" key is not a string in firewatch rule: "{rule_dict}"',
        )
        exit(1)

    def _get_group_priority(self, rule_dict: dict[Any, Any]) -> Optional[int]:
        """
        Determines if a group priority is defined in a rule. If it is, validate it and return the integer.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            Optional[str]: An integer that determines the priority of a rule. If one is not defined, return None
        """
        group_priority = rule_dict.get("group", {}).get("priority")
        if isinstance(group_priority, int) or not group_priority:
            return group_priority

        self.logger.error(
            f'Value for "priority" in the "group" key is not a integer in firewatch rule: "{rule_dict}"',
        )
        exit(1)

    def _get_ignore(self, rule_dict: dict[Any, Any]) -> bool:
        """
        Determines if this firewatch rule is an ignore rule. If it is, return true, else return false.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            bool: A boolean value that determines if a firewatch rule is an ignore rule. True=ignore, False=don't ignore
        """

        ignore = rule_dict.get("ignore", False)

        if isinstance(ignore, str):
            return ignore.lower() == "true"

        elif isinstance(ignore, bool):
            return ignore

        self.logger.error(
            f'Value for "ignore" is not a boolean or string value in firewatch rule: "{rule_dict}"',
        )
        exit(1)

    def _get_success_rule(self, rule_dict: dict[Any, Any]) -> bool:
        """
        Get success rule

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            bool: A boolean value that determines if a jira ticket will be opened (with `status: closed`) for success job
        """

        job_success = rule_dict.get("job_success", False)

        if isinstance(job_success, bool):
            return job_success

        self.logger.error(
            f'Value for "job_success" is not a boolean: "{rule_dict}"',
        )
        exit(1)
