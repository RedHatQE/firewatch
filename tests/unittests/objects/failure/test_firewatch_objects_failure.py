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
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

from cli.objects.failure import Failure


class TestFailure(unittest.TestCase):
    def setUp(self):
        self.mock_logger = patch("simple_logger.logger.get_logger")
        self.mock_logger.start().return_value = MagicMock()

    def tearDown(self):
        patch.stopall()

    def test_initialization_with_valid_failure_type(self):
        failure = Failure("step1", "pod_failure")
        self.assertEqual(failure.step, "step1")
        self.assertEqual(failure.failure_type, "pod_failure")

    def test_initialization_with_invalid_failure_type(self):
        self.mock_logger.error = MagicMock()
        with self.assertRaises(SystemExit):
            Failure("step1", "invalid_failure_type")

    def test_initialization_with_test_failure_type(self):
        failure = Failure("step1", "test_failure", "test1", "/path/to/junit")
        self.assertEqual(failure.step, "step1")
        self.assertEqual(failure.failure_type, "test_failure")
        self.assertEqual(failure.failed_test_name, "test1")
        self.assertEqual(failure.failed_test_junit_path, "/path/to/junit")

    def test_initialization_with_pod_failure_type(self):
        failure = Failure("step1", "pod_failure")
        self.assertEqual(failure.step, "step1")
        self.assertEqual(failure.failure_type, "pod_failure")
