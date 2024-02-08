import fnmatch
from typing import Any
from typing import Optional

from cli.objects.failure import Failure
from cli.objects.rule import Rule


class FailureRule(Rule):
    def __init__(self, rule_dict: dict[Any, Any]):
        """
        Initializes the FailureRule object which inherits the Rule object.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a firewatch rule.
        """
        super().__init__(rule_dict=rule_dict)

        self.step = self._get_step(rule_dict=rule_dict)
        self.failure_type = self._get_failure_type(rule_dict=rule_dict)
        self.classification = self._get_classification(rule_dict=rule_dict)
        self.group_name = self._get_group_name(rule_dict=rule_dict)
        self.group_priority = self._get_group_priority(rule_dict=rule_dict)
        self.ignore = self._get_ignore(rule_dict=rule_dict)

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

    def _get_group_name(self, rule_dict: dict[Any, Any]) -> Optional[str]:
        """
        Determines if a group name is defined in a rule. If it is, validate it and return the string.

        Args:
            rule_dict (dict[Any, Any]): A dictionary object representing a user-defined firewatch rule.

        Returns:
            Optional[str]: A string representing the group name. If one is not defined, return None
        """

        if isinstance(rule_dict.get("group"), dict):
            group_name = rule_dict.get("group", {}).get("name")
            if isinstance(group_name, str) or not group_name:
                return group_name

            self.logger.error(
                f'Value for "name" in the "group" key is not a string in firewatch rule: "{rule_dict}"',
            )
            exit(1)
        elif not rule_dict.get("group"):
            return None
        else:
            self.logger.error(
                f'Value for "group" is not a dictionary in firewatch rule: "{rule_dict}"',
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
        if isinstance(rule_dict.get("group"), dict):
            group_priority = rule_dict.get("group", {}).get("priority")
            if isinstance(group_priority, int) or not group_priority:
                return group_priority

            self.logger.error(
                f'Value for "priority" in the "group" key is not a integer in firewatch rule: "{rule_dict}"',
            )
            exit(1)
        elif not rule_dict.get("group"):
            return None
        else:
            self.logger.error(
                f'Value for "group" is not a dictionary in firewatch rule: "{rule_dict}"',
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

    def matches_failure(self, failure: Failure) -> bool:
        return (
            hasattr(self, "step")
            and fnmatch.fnmatch(failure.step, self.step)
            and (
                (failure.failure_type == self.failure_type)
                or self.failure_type == "all"
            )
        )
