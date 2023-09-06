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
import os

from google.cloud import storage
from simple_logger.logger import get_logger

import tests.unittests.helpers as helpers
from cli.objects.failure import Failure
from cli.objects.job import Job


class TestFirewatchObjectsJob:
    def test_check_is_rehearsal(self) -> None:
        self.logger = get_logger(__name__)

        build_id = "12345"

        # Test is rehearsal
        job_name = "rehearse_test_job"
        assert Job._check_is_rehearsal(self, job_name=job_name, build_id=build_id)

        # Test is not rehearsal
        job_name = "test_job"
        assert not Job._check_is_rehearsal(self, job_name=job_name, build_id=build_id)

    def test_get_download_path(self) -> None:
        self.logger = get_logger(__name__)

        # Test download path that doesn't exist
        build_id = "12345"
        download_path = Job._get_download_path(self, build_id=build_id)
        assert os.path.exists(download_path) and download_path == f"/tmp/{build_id}"
        os.rmdir(download_path)

        # Test download path that already exists
        os.mkdir(f"/tmp/{build_id}")
        download_path = Job._get_download_path(self, build_id=build_id)
        assert os.path.exists(download_path) and download_path == f"/tmp/{build_id}"
        os.rmdir(download_path)

    def test_check_has_test_failures(self) -> None:
        # Check has test_failures
        failures = [Failure(failed_step="test_step", failure_type="test_failure")]
        assert Job._check_has_test_failures(self, failures)

        # Check does not have test_failures
        failures = [Failure(failed_step="test_step", failure_type="pod_failure")]
        assert not Job._check_has_test_failures(self, failures)

    def test_check_has_pod_failures(self) -> None:
        # Check has pod_failures
        failures = [Failure(failed_step="test_step", failure_type="pod_failure")]
        assert Job._check_has_pod_failures(self, failures)

        # Check does not have pod_failures
        failures = [Failure(failed_step="test_step", failure_type="test_failure")]
        assert not Job._check_has_pod_failures(self, failures)

    def test_download_junit(self, tmp_path) -> None:
        self.logger = get_logger(__name__)

        job_name = "periodic-ci-windup-windup-ui-tests-v1.1-mtr-ocp4.14-lp-interop-mtr-interop-aws"
        job_name_safe = "mtr-interop-aws"
        build_id = "1678283096597729280"
        storage_client = storage.Client.create_anonymous_client()
        gcs_bucket = "origin-ci-test"
        downloads_directory = str(tmp_path)

        junit_path = Job._download_junit(
            self,
            downloads_directory=downloads_directory,
            storage_client=storage_client,
            gcs_bucket=gcs_bucket,
            job_name=job_name,
            build_id=build_id,
            job_name_safe=job_name_safe,
        )

        junit_files = []

        for root, dirs, files in os.walk(junit_path):
            for file_name in files:
                if ("junit" in file_name) and ("xml" in file_name):
                    file_path = os.path.join(root, file_name)
                    junit_files.append(file_path)

        assert len(junit_files) > 0

    def test_download_logs(self, tmp_path) -> None:
        self.logger = get_logger(__name__)

        files_to_download = ["finished.json", "build-log.txt"]

        job_name = "periodic-ci-windup-windup-ui-tests-v1.1-mtr-ocp4.14-lp-interop-mtr-interop-aws"
        job_name_safe = "mtr-interop-aws"
        build_id = "1678283096597729280"
        storage_client = storage.Client.create_anonymous_client()
        gcs_bucket = "origin-ci-test"
        downloads_directory = str(tmp_path)

        logs_path = Job._download_logs(
            self,
            downloads_directory=downloads_directory,
            storage_client=storage_client,
            gcs_bucket=gcs_bucket,
            job_name=job_name,
            build_id=build_id,
            job_name_safe=job_name_safe,
        )
        log_files = []

        for root, dirs, files in os.walk(logs_path):
            for file_name in files:
                assert file_name in files_to_download
                file_path = os.path.join(root, file_name)
                log_files.append(file_path)

        assert len(log_files) > 0

    def test_find_pod_failures(self, tmp_path) -> None:
        self.logger = get_logger(__name__)

        # Set up a logs directory
        logs_dir = helpers._get_tmp_logs_dir(tmp_path=tmp_path)

        # Test a job with no pod_failures
        helpers._create_successful_step_pod(logs_dir=logs_dir)
        pod_failures = Job._find_pod_failures(self, logs_dir=logs_dir)
        assert len(pod_failures) == 0

        # Test a job with a pod_failure
        helpers._create_failed_step_pod(logs_dir=logs_dir)
        pod_failures = Job._find_pod_failures(self, logs_dir=logs_dir)
        assert len(pod_failures) == 1

    def test_find_test_failures(self, tmp_path) -> None:
        self.logger = get_logger(__name__)

        # Set up junit directory
        junit_dir = helpers._get_tmp_junit_dir(tmp_path=tmp_path)

        # Test job with no test_failures
        helpers._create_successful_step_junit(junit_dir=junit_dir)
        failures = Job._find_test_failures(self, junit_dir=junit_dir)
        assert len(failures) == 0

        # Test job with test_failures
        helpers._create_failed_step_junit(junit_dir=junit_dir)
        failures = Job._find_test_failures(self, junit_dir=junit_dir)
        assert len(failures) == 1
