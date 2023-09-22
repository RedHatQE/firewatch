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
import json
import os
from typing import Any
from typing import Optional

import click
import junitparser
from google.cloud import storage
from simple_logger.logger import get_logger

from cli.objects.failure import Failure


class Job:
    def __init__(
        self,
        name: str,
        name_safe: str,
        build_id: Optional[str],
        gcs_bucket: str,
    ) -> None:
        """
        Constructs the Job object.

        Args:
            name (str): The full name of a Prow job. The value of $JOB_NAME
            name_safe (str): The safe name of a test in a Prow job. The value of $JOB_NAME_SAFE
            build_id (Optional[str]): The build ID that needs to be reported. The value of $BUILD_ID
            gcs_bucket (str): The bucket that Prow job logs are stored
        """
        self.logger = get_logger(__name__)

        # Set variables
        self.name = name or os.getenv("JOB_NAME")  # type: ignore
        self.name_safe = name_safe or os.getenv("JOB_NAME_SAFE")
        self.build_id = build_id or os.getenv("BUILD_ID")
        self.is_rehearsal = self._check_is_rehearsal(
            job_name=self.name,
            build_id=self.build_id,
        )

        # Set GCS bucket values
        self.gcs_bucket = gcs_bucket
        self.storage_client = storage.Client.create_anonymous_client()
        self.bucket = self.storage_client.bucket(gcs_bucket)

        # Get a list of steps
        self.steps = self._get_steps(
            job_name=self.name,
            job_name_safe=self.name_safe,
            build_id=self.build_id,
            storage_client=self.storage_client,
            gcs_bucket=self.gcs_bucket,
        )

        # Download logs and junit files
        self.download_path = self._get_download_path(build_id=self.build_id)
        self.logs_dir = self._download_logs(
            downloads_directory=self.download_path,
            storage_client=self.storage_client,
            gcs_bucket=self.gcs_bucket,
            job_name=self.name,
            build_id=self.build_id,
            job_name_safe=self.name_safe,
        )
        self.junit_dir = self._download_junit(
            downloads_directory=self.download_path,
            storage_client=self.storage_client,
            gcs_bucket=self.gcs_bucket,
            job_name=self.name,
            build_id=self.build_id,
            job_name_safe=self.name_safe,
        )

        # Get a list of failures
        self.failures = self._find_failures(
            logs_dir=self.logs_dir,
            junit_dir=self.junit_dir,
        )
        self.has_test_failures = self._check_has_test_failures(failures=self.failures)
        self.has_pod_failures = self._check_has_pod_failures(failures=self.failures)
        self.has_failures = True if self.failures else False

    def _check_is_rehearsal(
        self,
        job_name: Optional[str],
        build_id: Optional[str],
    ) -> bool:
        """
        Used to determine if the job being checked is a rehearsal job.

        Args:
            job_name (Optional[str]): A string object representing the name of the job to be checked.
            build_id (Optional[str]): A string object representing the build ID of the job to be checked.

        Returns:
            bool: True, means it is a rehearsal. False, means it is NOT a rehearsal.
        """
        if job_name.startswith("rehearse"):  # type: ignore
            self.logger.info(f"Run #{build_id} is a rehearsal job.")
            return True
        return False

    def _download_junit(
        self,
        downloads_directory: str,
        storage_client: Any,
        gcs_bucket: str,
        job_name: Optional[str],
        build_id: Optional[str],
        job_name_safe: Optional[str],
    ) -> str:
        """
        Used to download any JUnit files found in the artifacts directory of a job.

        Args:
            downloads_directory (str): The directory that downloads should be stored in.
            storage_client (Any): The storage client being used to download the files from GCS.
            gcs_bucket (str): The GCS bucket that logs and artifacts are stored in.
            job_name (Optional[str]): The name of the job that artifacts should be downloaded for.
            build_id (Optional[str]): The build ID of the job that artifacts should be downloaded for.
            job_name_safe (Optional[str]): The safe job name of the job that artifacts should be downloaded for.

        Returns:
            str: A string object representing the path that artifacts have been downloaded to.
        """
        self.logger.info("Downloading JUnit files...")

        # Create the junit download directory if it does not exist
        path = f"{downloads_directory}/artifacts"
        if not os.path.exists(path):
            os.mkdir(path)

        blobs = storage_client.list_blobs(
            gcs_bucket,
            prefix=f"logs/{job_name}/{build_id}/artifacts/{job_name_safe}",
        )

        for blob in blobs:
            blob_name = blob.name.split("/")[-1]

            if "junit" in blob_name:
                blob_step = blob.name.split("/")[5]

                # Create a step directory if it does not already exist
                if not os.path.exists(f"{path}/{blob_step}"):
                    os.mkdir(f"{path}/{blob_step}")

                # Check if the filename exists
                file_counter = 1
                filename, extension = os.path.splitext(blob_name)
                file_path = f"{path}/{blob_step}/{filename}{extension}"
                while os.path.exists(file_path):
                    self.logger.info(f"File {file_path} already exists...")
                    file_path = (
                        f"{path}/{blob_step}/{filename}_{str(file_counter)}{extension}"
                    )
                    file_counter += 1

                # Download blob
                f"{path}/{blob_step}/{blob_name}"
                with open(file_path, "xb") as target:
                    blob.download_to_file(target)
                    self.logger.debug(f"{file_path} downloaded successfully...")

        return path

    def _download_logs(
        self,
        downloads_directory: str,
        storage_client: Any,
        gcs_bucket: str,
        job_name: Optional[str],
        build_id: Optional[str],
        job_name_safe: Optional[str],
    ) -> str:
        """
        Used to download the logs of the job to be checked.

        Args:
            downloads_directory (str): The directory that downloaded logs should be stored in.
            storage_client (Any): The storage client to be used to download logs from the GCS bucket.
            gcs_bucket (str): The GCS bucket that logs are stored in.
            job_name (Optional[str]): The name of the job that logs should be downloaded for.
            build_id (Optional[str]): The build ID of the job that logs should be downloaded for.
            job_name_safe (Optional[str]): The safe job name of the job that logs should be downloaded for.

        Returns:
            str: A string object representing the path to the downloaded logs.
        """
        self.logger.info("Downloading log files...")

        files_to_download = ["finished.json", "build-log.txt"]

        # Create the logs download directory if it does not exist
        path = f"{downloads_directory}/logs"
        if not os.path.exists(path):
            os.mkdir(path)

        blobs = storage_client.list_blobs(
            gcs_bucket,
            prefix=f"logs/{job_name}/{build_id}/artifacts/{job_name_safe}",
        )

        for blob in blobs:
            blob_name = blob.name.split("/")[-1]
            blob_step = blob.name.split("/")[-2]

            if blob_name in files_to_download:
                # Create step directory if it does not already exist
                if not os.path.exists(f"{path}/{blob_step}"):
                    os.mkdir(f"{path}/{blob_step}")

                # Download blob
                file = f"{path}/{blob_step}/{blob_name}"
                with open(file, "xb") as target:
                    blob.download_to_file(target)
                    self.logger.debug(f"{file} downloaded successfully...")

        return path

    def _get_steps(
        self,
        job_name: Optional[str],
        job_name_safe: Optional[str],
        build_id: Optional[str],
        storage_client: Any,
        gcs_bucket: str,
    ) -> Optional[list[str]]:
        """
        Used to get a list of step names within a job.

        Args:
            job_name (Optional[str]): The name of the job that steps should be gathered for.
            job_name_safe (Optional[str]): The safe name of the job that steps should be gathered for.
            build_id (Optional[str]): The build ID of the job that steps should be gathered for.
            storage_client (Any): The storage client used to gather steps from GCS.
            gcs_bucket (str): The GCS bucket that job logs are stored in.

        Returns:
            Optional[list[str]]: A list of strings representing a list of steps in a job.
        """

        steps = []

        blobs = storage_client.list_blobs(
            gcs_bucket,
            prefix=f"logs/{job_name}/{build_id}/artifacts/{job_name_safe}",
        )

        # Populate list of steps
        for blob in blobs:
            blob_step = blob.name.split("/")[-2]
            steps.append(blob_step)

        # Return steps
        if len(steps) > 0 or self.is_rehearsal:
            return steps
        else:
            self.logger.error(f"No steps found for job {job_name}")
            raise click.abort()

    def _get_download_path(self, build_id: Optional[str]) -> str:
        """
        Creates the download path and if the directory does not exist, it creates the directory.

        Args:
            build_id (Optional[str]): A string object representing the build ID of the job.

        Returns:
            str: A string object representing the download path.
        """
        download_path = f"/tmp/{build_id}"

        if not os.path.exists(download_path):
            self.logger.info(
                f"Download path {download_path} does not exist, creating directory.",
            )
            os.mkdir(download_path)

        return download_path

    def _find_failures(self, logs_dir: str, junit_dir: str) -> Optional[list[Failure]]:
        """
        Used to find failures from a given job using that downloaded logs and JUnit artifacts.

        Args:
            logs_dir (str): The directory that job logs are stored in. Gotten from _download_logs.
            junit_dir (str): The directory that job artifacts are stored in. Gotten from _download_junit.

        Returns:
            Optional[list[Failure]]: A list of Failure objects.
        """

        pod_failures = self._find_pod_failures(logs_dir=logs_dir)
        test_failures = self._find_test_failures(junit_dir=junit_dir)
        failures_list = []

        # Combine lists into one list
        for test_failure in test_failures:
            failures_list.append(test_failure)
        for pod_failure in pod_failures:
            already_exists = False
            for existing_failure in failures_list:
                if existing_failure["step"] == pod_failure["step"]:
                    already_exists = True
            if not already_exists:
                failures_list.append(pod_failure)

        failures = []
        for failure in failures_list:
            failures.append(
                Failure(
                    failed_step=failure["step"],
                    failure_type=failure["failure_type"],
                ),
            )

        if len(failures) > 0:
            return failures
        else:
            return None

    def _find_pod_failures(self, logs_dir: str) -> list[dict[str, str]]:
        """
        Used to find pod failures in a given job.

        Args:
            logs_dir (str): The directory that job logs are stored in. Gotten from _download_logs.

        Returns:
            list[dict[str, str]]: A list of dictionary objects defining a pod failure to be turned into Failure objects.
        """

        # Initiate the failures list
        failures = []

        # Find failed pods in the logs directory
        for root, dirs, files in os.walk(logs_dir):
            for file_name in files:
                if file_name == "finished.json":
                    file_path = os.path.join(root, file_name)
                    with open(file_path) as file:
                        data = json.load(file)
                        if data.get("passed", False) is False:
                            step = os.path.basename(os.path.dirname(file_path))
                            failure = {
                                "step": step,
                                "failure_type": "pod_failure",
                            }
                            failures.append(failure)
                            self.logger.info(f"Found pod failure in step: {step}")

        return failures

    def _find_test_failures(self, junit_dir: str) -> list[dict[str, str]]:
        """
        Used to find test failures in a given job.

        Args:
            junit_dir (str): The directory that job artifacts are stored in. Gotten from _download_junit.

        Returns:
            list[dict[str, str]]: A list of dictionary objects defining a test failure to be turned into Failure objects.
        """

        # Initiate the failures list
        failures = []

        # Find failures in JUnit results
        for root, dirs, files in os.walk(junit_dir):
            for file_name in files:
                if ("junit" in file_name) and ("xml" in file_name):
                    file_path = os.path.join(root, file_name)
                    try:
                        junit_xml = junitparser.JUnitXml.fromfile(file_path)
                    except junitparser.junitparser.JUnitXmlError:
                        self.logger.warning(
                            f"Attempted to parse {file_name}, but it doesn't seem to be a JUnit results file.",
                        )
                        continue
                    step = os.path.basename(os.path.dirname(file_path))

                    for suite in junit_xml:
                        for case in suite:
                            if hasattr(case, "result") and case.result:
                                for result in case.result:
                                    if isinstance(result, junitparser.Failure):
                                        failure = {
                                            "step": step,
                                            "failure_type": "test_failure",
                                        }
                                        if failure not in failures:
                                            failures.append(failure)
                                            self.logger.info(
                                                f"Found test failure in step: {step}",
                                            )
                            elif isinstance(case, junitparser.Failure):
                                failure = {
                                    "step": step,
                                    "failure_type": "test_failure",
                                }
                                if failure not in failures:
                                    failures.append(failure)
                                    self.logger.info(
                                        f"Found test failure in step: {step}",
                                    )

        return failures

    def _check_has_test_failures(self, failures: Optional[list[Failure]]) -> bool:
        """
        Determines if the job has any test failures given a list of Failure objects.

        Args:
            failures (Optional[list[Failure]]): A list of failures found in the job.

        Returns:
            bool: True if there are test failures, False otherwise.
        """
        has_test_failures = False

        if failures:
            for failure in failures:
                if failure.failure_type == "test_failure":
                    has_test_failures = True

        return has_test_failures

    def _check_has_pod_failures(self, failures: Optional[list[Failure]]) -> bool:
        """
        Determines if the job has any pod failures given a list of Failure objects.

        Args:
            failures (Optional[list[Failure]]): A list of failures in the job.

        Returns:
            bool: True if there are pod failures, False otherwise.
        """
        has_pod_failures = False
        if failures:
            for failure in failures:
                if failure.failure_type == "pod_failure":
                    has_pod_failures = True

        return has_pod_failures
