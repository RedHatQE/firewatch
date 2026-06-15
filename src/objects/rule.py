import json
import os
import re
from typing import Any
from typing import Optional

from simple_logger.logger import get_logger

EMAIL_REGEX = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"


class Rule:
    def __init__(self, rule_dict: dict[Any, Any]) -> None:
        """
        Initializes the Rule object.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a firewatch rule.
        """

        self.logger = get_logger(__name__)
        self.jira_project = self._get_jira_project(rule_dict)
        self.jira_epic = self._get_jira_epic(rule_dict)
        self.jira_component = self._get_jira_component(rule_dict)
        self.jira_affects_version = self._get_jira_affects_version(rule_dict)
        self.jira_additional_labels = self._get_jira_additional_labels(rule_dict)
        self.jira_assignee = self._get_jira_assignee(rule_dict)
        self.jira_priority = self._get_jira_priority(rule_dict)
        self.jira_security_level = self._get_jira_security_level(rule_dict)
        self.jira_watchers = self._get_jira_watchers(rule_dict)
        self.jira_additional_assignees = self._get_jira_additional_assignees(rule_dict)
        self.slack_channel = self._get_slack_channel(rule_dict)
        self.slack_user = self._get_slack_user(rule_dict)

    def _get_jira_project(self, rule_dict: dict[Any, Any]) -> str:
        """
        Determines the Jira Project defined in a firewatch rule.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            str: A string value representing the jira_project for a firewatch rule.
        """
        # Check if the jira_project is defined in the rule, if not, check the environment variable
        jira_project = rule_dict.get("jira_project")

        if jira_project == "!default" or not jira_project:
            jira_project = os.getenv("FIREWATCH_DEFAULT_JIRA_PROJECT")

        if not jira_project:
            self.logger.error(
                f'Unable to find value for "jira_project" in firewatch rule and $FIREWATCH_DEFAULT_JIRA_PROJECT environemnt variable is not defined: "{rule_dict}"',
            )
            exit(1)

        if isinstance(jira_project, str):
            return jira_project
        else:
            self.logger.error(
                f'Value for "jira_project" or $FIREWATCH_DEFAULT_JIRA_PROJECT is not a string in firewatch rule: "{rule_dict}"',
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
            if jira_epic == "!default":
                return os.getenv("FIREWATCH_DEFAULT_JIRA_EPIC")
            return jira_epic

        self.logger.error(
            f'Value for "jira_epic" or $FIREWATCH_DEFAULT_JIRA_EPIC is not a string in firewatch rule: "{rule_dict}"',
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

        if isinstance(jira_component, list):
            # If the list contains "!default", include the list in the environment variable
            if "!default" in jira_component:
                default_components = os.getenv("FIREWATCH_DEFAULT_JIRA_COMPONENT")
                if default_components:
                    try:
                        default_components = json.loads(default_components)
                    except json.JSONDecodeError:
                        self.logger.error(
                            f'Invalid JSON format for FIREWATCH_DEFAULT_JIRA_COMPONENT environment variable: "{default_components}"',
                        )
                        exit(1)
                if default_components:
                    jira_component.remove("!default")
                    jira_component.extend(default_components)
                else:
                    self.logger.error(
                        "Environment variable $FIREWATCH_DEFAULT_JIRA_COMPONENT is not set.",
                    )

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
            f'Value for "jira_component" must be a list of strings (multiple components) in firewatch rule: "{rule_dict}"',
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
            if jira_affects_version == "!default":
                return os.getenv("FIREWATCH_DEFAULT_JIRA_AFFECTS_VERSION")
            return jira_affects_version

        self.logger.error(
            f'Value for "jira_affects_version" or $FIREWATCH_DEFAULT_JIRA_AFFECTS_VERSION is not a string in firewatch rule: "{rule_dict}"',
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
            # If the list contains "!default", include the list in the environment variable
            if "!default" in jira_additional_labels:
                default_labels = os.getenv("FIREWATCH_DEFAULT_JIRA_ADDITIONAL_LABELS")
                if default_labels:
                    try:
                        default_labels = json.loads(default_labels)
                    except json.JSONDecodeError:
                        self.logger.error(
                            f'Invalid JSON format for $FIREWATCH_DEFAULT_JIRA_ADDITIONAL_LABELS environment variable: "{default_labels}"',
                        )
                        exit(1)
                if default_labels:
                    jira_additional_labels.remove("!default")
                    jira_additional_labels.extend(default_labels)
                else:
                    self.logger.error(
                        "Environment variable $FIREWATCH_DEFAULT_JIRA_ADDITIONAL_LABELS is not set.",
                    )

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

        if jira_assignee == "!default":
            jira_assignee = os.getenv("FIREWATCH_DEFAULT_JIRA_ASSIGNEE")

        if isinstance(jira_assignee, str):
            if re.fullmatch(EMAIL_REGEX, jira_assignee):
                return jira_assignee
            else:
                self.logger.error(
                    f'Value for "jira_assignee" or $FIREWATCH_DEFAULT_JIRA_ASSIGNEE is not an email address in firewatch rule: "{rule_dict}"',
                )
                exit(1)

        elif not jira_assignee:
            return jira_assignee

        self.logger.error(
            f'Value for "jira_assignee" or $FIREWATCH_DEFAULT_JIRA_ASSIGNEE is not a string in firewatch rule: "{rule_dict}"',
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
            # If the value is "!default", check the environment variable
            if jira_priority == "!default":
                jira_priority = os.getenv("FIREWATCH_DEFAULT_JIRA_PRIORITY")

            jira_priority = jira_priority.lower().capitalize() if isinstance(jira_priority, str) else None

            if jira_priority in valid_priority_values:
                return jira_priority
            else:
                self.logger.error(
                    f'Value for "jira_priority" or $FIREWATCH_DEFAULT_JIRA_PRIORITY is not a valid value ({valid_priority_values}) in firewatch rule: "{rule_dict}" ',
                )
                exit(1)
        elif not jira_priority:
            return jira_priority

        self.logger.error(
            f'Value for "jira_priority" or $FIREWATCH_DEFAULT_JIRA_PRIORITY is not a string in firewatch rule: "{rule_dict}"',
        )
        exit(1)

    def _get_jira_security_level(self, rule_dict: dict[Any, Any]) -> Optional[str]:
        """
        Determines if a Jira security level is defined in a rule. If it is, validate it and return the string.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            Optional[str]: A string of the Jira security level to use in a firewatch rule. If one is not defined, return None
        """
        jira_security_level = rule_dict.get("jira_security_level")

        if isinstance(jira_security_level, str) or not jira_security_level:
            # If the value is "!default", check the environment variable
            if jira_security_level == "!default":
                jira_security_level = os.getenv("FIREWATCH_DEFAULT_JIRA_SECURITY_LEVEL")

            return jira_security_level

        self.logger.error(
            f'Value for "jira_security_level" or $FIREWATCH_DEFAULT_JIRA_SECURITY_LEVEL is not a string in firewatch rule: "{rule_dict}"',
        )
        exit(1)

    def _get_jira_email_list(
        self,
        rule_dict: dict[Any, Any],
        field_name: str,
        env_var: str,
    ) -> Optional[list[str]]:
        values = rule_dict.get(field_name)

        if isinstance(values, list):
            if "!default" in values:
                defaults = os.getenv(env_var)
                if defaults:
                    try:
                        defaults = json.loads(defaults)
                    except json.JSONDecodeError:
                        self.logger.error(
                            f'Invalid JSON format for {env_var} environment variable: "{defaults}"',
                        )
                        exit(1)
                if defaults:
                    values.remove("!default")
                    values.extend(defaults)
                else:
                    self.logger.error(
                        f"Environment variable ${env_var} is not set.",
                    )
                    exit(1)

            emails: list[str] = []
            for entry in values:
                if isinstance(entry, str) and re.fullmatch(EMAIL_REGEX, entry):
                    emails.append(entry)
                else:
                    self.logger.error(
                        f'Value "{entry}" in "{field_name}" is not a valid email address in firewatch rule: "{rule_dict}"',
                    )
                    exit(1)
            return emails
        elif not values:
            return values

        self.logger.error(
            f'Value for "{field_name}" must be a list of email addresses in firewatch rule: "{rule_dict}"',
        )
        exit(1)

    def _get_slack_channel(self, rule_dict: dict[Any, Any]) -> Optional[str]:
        slack_channel = rule_dict.get("slack_channel")

        if isinstance(slack_channel, str) or not slack_channel:
            if slack_channel == "!default":
                return os.getenv("FIREWATCH_DEFAULT_SLACK_CHANNEL")
            return slack_channel

        self.logger.error(
            f'Value for "slack_channel" or $FIREWATCH_DEFAULT_SLACK_CHANNEL is not a string in firewatch rule: "{rule_dict}"',
        )
        exit(1)

    def _get_slack_user(self, rule_dict: dict[Any, Any]) -> Optional[str]:
        slack_user = rule_dict.get("slack_user")

        if isinstance(slack_user, str) or not slack_user:
            return slack_user

        self.logger.error(
            f'Value for "slack_user" is not a string in firewatch rule: "{rule_dict}"',
        )
        exit(1)

    def _get_jira_watchers(self, rule_dict: dict[Any, Any]) -> Optional[list[str]]:
        return self._get_jira_email_list(rule_dict, "jira_watchers", "FIREWATCH_DEFAULT_JIRA_WATCHERS")

    def _get_jira_additional_assignees(self, rule_dict: dict[Any, Any]) -> Optional[list[str]]:
        return self._get_jira_email_list(
            rule_dict, "jira_additional_assignees", "FIREWATCH_DEFAULT_JIRA_ADDITIONAL_ASSIGNEES"
        )
