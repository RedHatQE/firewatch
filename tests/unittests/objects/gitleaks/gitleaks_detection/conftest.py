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
import os

import pytest

from cli.objects.gitleaks_detection import GitleaksDetection
from cli.objects.gitleaks_detection import GitleaksDetectionCollection


@pytest.fixture
def gitleaks_detection_json():
    yield {
        "line": "REDACTED",
        "lineNumber": 7,
        "offender": "REDACTED",
        "offenderEntropy": 5.311,
        "commit": "",
        "repo": "",
        "repoURL": "",
        "leakURL": "",
        "rule": "Container Registry Authentication",
        "commitMessage": "add secrets",
        "author": "",
        "email": "",
        "file": "logs/ipi-install-install/build-log.txt",
        "date": "0001-01-01T00:00:00Z",
        "tags": "alert:repo-owner, key, container-registry, type:secret, type:redhat-restricted",
    }


@pytest.fixture
def gitleaks_detection(gitleaks_detection_json):
    yield GitleaksDetection.from_json(gitleaks_detection_json)


@pytest.fixture
def gitleaks_detection_iterator(gitleaks_detection_json):
    def _it():
        for i in range(10):
            json_obj = gitleaks_detection_json.copy()
            json_obj.update({"lineNumber": i})
            yield GitleaksDetection.from_json(json_obj=json_obj)

    yield _it()


@pytest.fixture
def gitleaks_detection_collection(
    gitleaks_detection_iterator,
):
    yield GitleaksDetectionCollection.from_iter(gitleaks_detection_iterator)


@pytest.fixture
def default_jira_project_env(monkeypatch):
    key = "FIREWATCH_DEFAULT_JIRA_PROJECT"
    val = "TEST"
    monkeypatch.setenv(key, val)
    yield os.getenv(key)
