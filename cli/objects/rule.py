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
import logging
import re
from typing import Any
from typing import Optional


class Rule:
    def __init__(self, rule_dict: dict[Any, Any]) -> None:
        """
        Builds the Rule object.

        :param rule_dict: A dictionary object representing a firewatch rule.
        """

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(
            __name__,
        )

        # Build the rule using the rule_dict
        self.step = self._get_step(rule_dict)
        self.failure_type = self._get_failure_type(rule_dict)
        self.classification = self._get_classification(rule_dict)
        self.jira_project = self._get_jira_project(rule_dict)
        self.jira_epic = self._get_jira_epic(rule_dict)
        self.jira_component = self._get_jira_component(rule_dict)
        self.jira_affects_version = self._get_jira_affects_version(rule_dict)
        self.jira_additional_labels = self._get_jira_additional_labels(rule_dict)
        self.jira_assignee = self._get_jira_assignee(rule_dict)
        self.jira_priority = self._get_jira_priority(rule_dict)
        self.ignore = self._get_ignore(rule_dict)

    def _get_step(self, rule_dict: dict[Any, Any]) -> str:
        """
        Determines the step that a firewatch rule pertains to.

        :param rule_dict: A dictionary object representing a user-defined firewatch rule.
        :return: A string value representing the full or partial name of a step that this firewatch rule pertains to.
        """
        try:
            step = rule_dict["step"]
        except Exception as ex:
            self.logger.error(ex)
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

        :param rule_dict: A dictionary object representing a user-defined firewatch rule.
        :return: A string value representing the failure_type of a rule.
        """
        valid_failure_types = ["pod_failure", "test_failure", "all", "!none"]

        try:
            failure_type = rule_dict["failure_type"].lower()
        except Exception as ex:
            self.logger.error(ex)
            self.logger.error(
                f'Unable to find value for "failure_type" in firewatch rule: "{rule_dict}"',
            )
            exit(1)

        if isinstance(failure_type, str):
            if failure_type in valid_failure_types:
                return failure_type
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

        :param rule_dict: A dictionary object representing a user-defined firewatch rule.
        :return: A string value representing the classification of a rule.
        """
        try:
            classification = rule_dict["classification"]
        except Exception as ex:
            self.logger.error(ex)
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

        :param rule_dict: A dictionary object representing a user-defined firewatch rule.
        :return: A string value representing the jira_project for a firewatch rule.
        """
        try:
            jira_project = rule_dict["jira_project"]
        except Exception as ex:
            self.logger.error(ex)
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

        :param rule_dict: A dictionary object representing a user-defined firewatch rule.
        :return: A string of the Jira epic to use in a firewatch rule. If one is not defined, return None
        """
        if "jira_epic" in rule_dict.keys():

            jira_epic = rule_dict["jira_epic"]

            if isinstance(jira_epic, str):
                return jira_epic
            else:
                self.logger.error(
                    f'Value for "jira_epic" is not a string in firewatch rule: "{rule_dict}"',
                )
                exit(1)
        else:
            return None

    def _get_jira_component(self, rule_dict: dict[Any, Any]) -> Optional[list[str]]:
        """
        Determines if one or more Jira Components are defined in firewatch rule. If it is, return a list of components.

        :param rule_dict: A dictionary object representing a user-defined firewatch rule.
        :return: A list of strings representing the component(s) defined in a firewatch rule. If not defined, return None
        """
        components = []
        if "jira_component" in rule_dict.keys():

            jira_component = rule_dict["jira_component"]

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
            else:
                self.logger.error(
                    f'Value for "jira_component" must be either a list of strings (multiple components) or a string value (single component) in firewatch rule: "{rule_dict}"',
                )
                exit(1)

        else:
            return None

    def _get_jira_affects_version(self, rule_dict: dict[Any, Any]) -> Optional[str]:
        """
        Determines if the jira_affects_version value is set, if so, returns the string of that version affected.

        :param rule_dict: A dictionary object representing a user-defined firewatch rule.
        :return: A string value representing the affected version for a firewatch rule.
        """
        if "jira_affects_version" in rule_dict.keys():

            jira_affects_version = rule_dict["jira_affects_version"]

            if isinstance(jira_affects_version, str):
                return jira_affects_version
            else:
                self.logger.error(
                    f'Value for "jira_affects_version" is not a string in firewatch rule: "{rule_dict}"',
                )
                exit(1)
        else:
            return None

    def _get_jira_additional_labels(
        self,
        rule_dict: dict[Any, Any],
    ) -> Optional[list[str]]:
        """
        Determines if the jira_additional_labels value is set, if so, returns a list of strings of additional labels.

        :param rule_dict: A dictionary object representing a user-defined firewatch rule.
        :return: A list of strings representing additional labels.
        """
        labels = []

        if "jira_additional_labels" in rule_dict.keys():

            jira_additional_labels = rule_dict["jira_additional_labels"]

            if isinstance(jira_additional_labels, str):
                labels.append(jira_additional_labels)
                return labels
            elif isinstance(jira_additional_labels, list):
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
            else:
                self.logger.error(
                    f'Value for "jira_additional_labels" must be either a list of strings (multiple labels) or a string value (single label) in firewatch rule: "{rule_dict}"',
                )
                exit(1)
        else:
            return None

    def _get_jira_assignee(self, rule_dict: dict[Any, Any]) -> Optional[str]:
        """
        Determines if a Jira Assignee is defined in a rule. If it is, validate it and return the string.

        :param rule_dict: A dictionary object representing a user-defined firewatch rule.
        :return: A string of the Jira assignee to use in a firewatch rule. If one is not defined, return None
        """
        if "jira_assignee" in rule_dict.keys():

            jira_assignee = rule_dict["jira_assignee"]

            if isinstance(jira_assignee, str):
                regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"  # Used to check if email is valid
                if re.fullmatch(regex, jira_assignee):
                    return jira_assignee
                else:
                    self.logger.error(
                        f'Value for "jira_assignee" is not an email address in firewatch rule: "{rule_dict}"',
                    )
                    exit(1)
            else:
                self.logger.error(
                    f'Value for "jira_assignee" is not a string in firewatch rule: "{rule_dict}"',
                )
                exit(1)
        else:
            return None

    def _get_jira_priority(self, rule_dict: dict[Any, Any]) -> Optional[str]:
        """
        Determines if a Jira priority is defined in a rule. If it is, validate it and return the string.

        :param rule_dict: A dictionary object representing a user-defined firewatch rule.
        :return: A string of the Jira priority to use in a firewatch rule. If one is not defined, return None
        """
        valid_priority_values = ["Blocker", "Critical", "Major", "Normal", "Minor"]

        if "jira_priority" in rule_dict.keys():

            jira_priority = (
                rule_dict["jira_priority"].lower().capitalize()
            )  # The value must be an exact match to the values in valid_priority_values (first letter capitalized, the rest lower)

            if isinstance(jira_priority, str):
                if jira_priority in valid_priority_values:
                    return jira_priority
                else:
                    self.logger.error(
                        f'Value for "jira_priority" is not a valid value ({valid_priority_values}) in firewatch rule: "{rule_dict}" ',
                    )
                    exit(1)
            else:
                self.logger.error(
                    f'Value for "jira_priority" is not a string in firewatch rule: "{rule_dict}"',
                )
                exit(1)
        else:
            return None

    def _get_ignore(self, rule_dict: dict[Any, Any]) -> bool:
        """
        Determines if this firewatch rule is an ignore rule. If it is, return true, else return false.

        :param rule_dict: A dictionary object representing a user-defined firewatch rule.
        :return: A boolean value that determines if a firewatch rule is an ignore rule. True=ignore, False=don't ignore
        """
        if "ignore" in rule_dict.keys():

            ignore = rule_dict["ignore"]

            if isinstance(ignore, str):
                if ignore.lower() == "true":
                    return True
                else:
                    return False
            elif isinstance(ignore, bool):
                return ignore

        return False
