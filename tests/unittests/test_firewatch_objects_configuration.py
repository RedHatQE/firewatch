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

import pytest

from cli.objects.configuration import Configuration
from cli.objects.configuration import value_is_string_and_not_none
from cli.objects.jira_base import Jira


class TestFirewatchObjectsConfiguration:
    logger = logging.getLogger(__name__)

    def test_value_is_string_and_not_none(self) -> None:
        # Test is string and not none
        test_value = "String"
        assert value_is_string_and_not_none(value=test_value)

        # Test is not string
        test_value = 1
        assert not value_is_string_and_not_none(value=test_value)

        # Test is none
        test_value = None
        assert not value_is_string_and_not_none(value=test_value)

    def test_step_value_valid(self) -> None:
        self.logger = logging.getLogger(__name__)

        # Test valid
        step_value = "some-step"
        assert Configuration.step_value_valid(self, step_value=step_value)

        # Test not valid
        step_value = 1
        assert not Configuration.step_value_valid(self, step_value=step_value)

        # Test spaces
        step_value = "some step"
        assert not Configuration.step_value_valid(self, step_value=step_value)

    def test_failure_type_value_valid(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.valid_failure_types = ["pod_failure", "test_failure", "all"]

        # Test valid
        failure_value = "pod_failure"
        assert Configuration.failure_type_value_valid(self, failure_value)

        # Test not valid
        failure_value = 1
        assert not Configuration.failure_type_value_valid(self, failure_value)

        # Test not in valid_failure_types
        failure_value = "not_in_list"
        assert not Configuration.failure_type_value_valid(self, failure_value)

    def test_classification_value_valid(self) -> None:
        self.logger = logging.getLogger(__name__)

        # Test valid
        classification_value = "some classification value"
        assert Configuration.classification_value_valid(self, classification_value)

        # Test not valid
        classification_value = None
        assert not Configuration.classification_value_valid(self, classification_value)
