from typing import Optional

from simple_logger.logger import get_logger


class Failure:
    def __init__(
        self,
        failed_step: str,
        failure_type: str,
        failed_test_name: Optional[str] = None,
        failed_test_junit_path: Optional[str] = None,
        ignore: bool = False,
    ):
        """
        Initializes the Failure object.

        Args:
            failed_step (str): The failed step
            failure_type (str): The failure type
            failed_test_name (Optional[str], optional): The failed test name. Defaults to None.
            failed_test_junit_path (Optional[str], optional): The path to the failed test's junit file. Defaults to None.
            ignore (bool): Flag to indicate that the failure should be ignored.
        """
        self.logger = get_logger(__name__)

        self.step = failed_step
        self.failure_type = self._get_failure_type(failure_type)

        # if the failure is a test failure, set additional attributes
        if self.failure_type == "test_failure":
            self.failed_test_name = failed_test_name
            self.failed_test_junit_path = failed_test_junit_path

        self.ignore = ignore

    def _get_failure_type(self, failure_type: str) -> str:
        """
        Gets the failure type. Used to validate the value provided.

        Args:
            failure_type (str): Failure type.

        Returns:
            str: A string value representing failure type
        """

        valid_failure_types = ["pod_failure", "test_failure"]
        if isinstance(failure_type, str) and (failure_type in valid_failure_types):
            return failure_type
        else:
            self.logger.error(
                f'Failure type "{failure_type}" is either not a string or not a valid failure type.',
            )
            exit(1)
