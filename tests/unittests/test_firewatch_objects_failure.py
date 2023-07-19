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
from cli.objects.failure import Failure


class TestFirewatchObjectsFailure:
    def test_failure(self) -> None:
        failed_step = "test-step"
        failure_type = "test_failure"
        failure = Failure(failed_step=failed_step, failure_type=failure_type)
        assert failure.failure_type == "test_failure"
        assert failure.step == "test-step"

    def test_get_failed_step(self) -> None:
        test_failed_step = "test-step"
        failed_step = Failure._get_failed_step(self, test_failed_step)
        assert failed_step == "test-step"

    def test_get_failure_type(self) -> None:
        # Test pod_failure
        test_failure_type = "pod_failure"
        failure_type = Failure._get_failure_type(self, test_failure_type)
        assert failure_type == "pod_failure"

        # Test test_failure
        test_failure_type = "test_failure"
        failure_type = Failure._get_failure_type(self, test_failure_type)
        assert failure_type == "test_failure"
