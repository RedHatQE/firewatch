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
from cli.objects.gitleaks_detection import GitleaksDetection
from cli.objects.gitleaks_detection import GitleaksDetectionCollection
from cli.objects.gitleaks_detection import GitleaksDetectionsFailureRule
from cli.objects.gitleaks_detection import GitleaksDetectionsJobFailure


def test_init_gitleaks_detection_from_json(gitleaks_detection):
    assert isinstance(gitleaks_detection, GitleaksDetection)
    assert gitleaks_detection.line is GitleaksDetection.REDACTED
    assert gitleaks_detection.offender is GitleaksDetection.REDACTED
    assert gitleaks_detection.line_number == 7
    assert gitleaks_detection.offender_entropy == 5.311
    assert gitleaks_detection.commit_message == "add secrets"
