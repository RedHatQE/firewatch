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


class Failure:
    def __init__(self, failed_step: str, failure_type: str):
        """
        Initializes the Failure object.

        Args:
            failed_step (str): The failed step
            failure_type (str): The failure type
        """
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(
            __name__,
        )

        self.step = self._get_failed_step(failed_step)
        self.failure_type = self._get_failure_type(failure_type)

    def _get_failed_step(self, failed_step: str) -> str:
        """
        Gets the name of the failed step. Used to validate the value provided.

        Args:
            failed_step (str): Failed step name.

        Returns:
            str: String value representing name of step failed
        """
        if isinstance(failed_step, str):
            return failed_step
        else:
            self.logger.error("Failed step must be a string value")
            exit(1)

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
