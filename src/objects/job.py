import json
import os
from typing import Any
from typing import Optional
from xml.etree.ElementTree import ParseError
from datetime import datetime, timezone, timedelta

import junitparser
from google.cloud import storage
from google.oauth2 import service_account
from simple_logger.logger import get_logger

from src.objects.configuration import Configuration
from src.objects.failure import Failure


class Job:
    def __init__(
        self,
        name: str,
        name_safe: str,
        build_id: Optional[str],
        gcs_bucket: str,
        gcs_creds_file: Optional[str],
        firewatch_config: Configuration,
        pr_id: Optional[str] = "",
    ) -> None:
        """
        Constructs the Job object.

        Args:
            name (str): The full name of a Prow job. The value of $JOB_NAME
            name_safe (str): The safe name of a test in a Prow job. The value of $JOB_NAME_SAFE
            build_id (Optional[str]): The build ID that needs to be reported. The value of $BUILD_ID
            gcs_bucket (str): The bucket that Prow job logs are stored
            firewatch_config (Configuration): The Configuration object.
            pr_ID (Optional[str]): The pull request number rehearsal job is running for. The value of $PULL_NUMBER
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
        if self.is_rehearsal:
            try:
                self.pr_id = pr_id or os.getenv("PULL_NUMBER") or self.name.split("-")[1]  # type: ignore
            except IndexError:
                self.logger.warning(
                    f"Pull number for job {self.name} not obtained, reporting may not be complete.",
                )
                self.pr_id = "1"
            self.logger.info(f"PR ID: {self.pr_id}")
        else:
            self.pr_id = ""
        self.firewatch_config = firewatch_config
        self.is_private_deck = True if gcs_creds_file else False

        # Set GCS bucket values
        self.gcs_bucket = gcs_bucket
        self.storage_client = (
            storage.Client(credentials=service_account.Credentials.from_service_account_file(gcs_creds_file))
            if gcs_creds_file
            else storage.Client.create_anonymous_client()
        )

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
            pr_id=self.pr_id,
        )
        self.junit_dir = self._download_junit(
            downloads_directory=self.download_path,
            storage_client=self.storage_client,
            gcs_bucket=self.gcs_bucket,
            job_name=self.name,
            build_id=self.build_id,
            job_name_safe=self.name_safe,
            pr_id=self.pr_id,
        )

        # Get a list of failures
        self.failures = self._find_failures(
            logs_dir=self.logs_dir,
            junit_dir=self.junit_dir,
        )

        self.has_pod_failures = self.has_test_failures = False
        for failure in self.failures:
            if failure.failure_type == "test_failure":
                self.has_test_failures = True
            elif failure.failure_type == "pod_failure":
                self.has_pod_failures = True

        # Check if job is retriggered within same week of last build
        self.is_retriggered = self._check_is_retriggered(
            job_name=self.name,
            build_id=self.build_id,
        )

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
        pr_id: Optional[str],
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
            pr_id (Optional[str]): The pull request number of the rehearsal job that artifacts should be downloaded for.

        Returns:
            str: A string object representing the path that artifacts have been downloaded to.
        """
        self.logger.info("Downloading JUnit files...")

        # Create the junit download directory if it does not exist
        path = f"{downloads_directory}/artifacts"
        if not os.path.exists(path):
            os.mkdir(path)

        if self.is_rehearsal:
            blobs = storage_client.list_blobs(
                gcs_bucket,
                prefix=f"pr-logs/pull/openshift_release/{pr_id}/{job_name}/{build_id}/artifacts/{job_name_safe}",
            )
        else:
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
                    file_path = f"{path}/{blob_step}/{filename}_{str(file_counter)}{extension}"
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
        pr_id: Optional[str],
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
            pr_id (Optional[str]): The pull request number for the rehearsal job that artifacts should be downloaded for.

        Returns:
            str: A string object representing the path to the downloaded logs.
        """
        self.logger.info("Downloading log files...")

        files_to_download = ["finished.json", "build-log.txt"]

        # Create the logs download directory if it does not exist
        path = f"{downloads_directory}/logs"
        if not os.path.exists(path):
            os.mkdir(path)

        if self.is_rehearsal:
            blobs = storage_client.list_blobs(
                gcs_bucket,
                prefix=f"pr-logs/pull/openshift_release/{pr_id}/{job_name}/{build_id}/artifacts/{job_name_safe}",
            )
        else:
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
            exit(1)

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

    def _find_failures(self, logs_dir: str, junit_dir: str) -> list[Failure]:
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
        unique_steps_with_failures = set()

        # Combine lists into one list
        for failure in test_failures + pod_failures:
            if failure.step not in unique_steps_with_failures:
                unique_steps_with_failures.add(failure.step)
                if failure_rules := self.firewatch_config.failure_rules:
                    for rule in failure_rules:
                        if rule.matches_failure(failure) and rule.ignore:
                            self.logger.warning(
                                f"Ignoring detected {failure.failure_type} in step {failure.step}",
                            )
                            failure.ignore = True
                if not failure.ignore:
                    failures_list.append(failure)

        return failures_list

    def _find_pod_failures(self, logs_dir: str) -> list[Failure]:
        """
        Used to find pod failures in a given job.

        Args:
            logs_dir (str): The directory that job logs are stored in. Gotten from _download_logs.

        Returns:
            list[Failure]: A list of Failure objects.
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
                            failures.append(
                                Failure(failed_step=step, failure_type="pod_failure"),
                            )
                            self.logger.info(f"Found pod failure in step: {step}")

        return failures

    def _find_test_failures(self, junit_dir: str) -> list[Failure]:
        """
        Used to find test failures in a given job.

        Args:
            junit_dir (str): The directory that job artifacts are stored in. Gotten from _download_junit.

        Returns:
            list[Failure]: A list of Failure objects
        """

        # Initiate the failures list
        failures_list = []

        for root, _, files in os.walk(junit_dir):
            junit_files = [file for file in files if "junit" in file and "xml" in file]

            for file in junit_files:
                file_path = os.path.join(root, file)
                try:
                    junit_xml = junitparser.JUnitXml.fromfile(file_path)
                except (ParseError, junitparser.junitparser.JUnitXmlError):
                    self.logger.warning(
                        f"Attempted to parse {file_path}, but it doesn't seem to be a JUnit results file.",
                    )
                    continue

                step = os.path.basename(os.path.dirname(file_path))
                for suite in junit_xml:
                    for case in suite:
                        if hasattr(case, "result") and case.result:
                            for result in case.result:
                                if isinstance(
                                    result,
                                    (junitparser.Failure, junitparser.Error),
                                ):
                                    failure = {
                                        "step": step,
                                        "failure_type": "test_failure",
                                        "failed_test_name": (
                                            case.name.replace(" ", "_")
                                            if self.firewatch_config.verbose_test_failure_reporting
                                            else None
                                        ),
                                        "failed_test_junit_path": (
                                            file_path if self.firewatch_config.verbose_test_failure_reporting else None
                                        ),
                                    }
                                    if failure not in failures_list:
                                        failures_list.append(failure)
                                        self.logger.info(
                                            f"Found test failure in step {step} {'for test ' + case.name if self.firewatch_config.verbose_test_failure_reporting else ''}",
                                        )
                        elif isinstance(case, (junitparser.Failure, junitparser.Error)):
                            failure = {
                                "step": step,
                                "failure_type": "test_failure",
                                "failed_test_name": (
                                    suite.name.replace(" ", "_")
                                    if self.firewatch_config.verbose_test_failure_reporting
                                    else None
                                ),
                                "failed_test_junit_path": (
                                    file_path if self.firewatch_config.verbose_test_failure_reporting else None
                                ),
                            }
                            if failure not in failures_list:
                                failures_list.append(failure)
                                self.logger.info(
                                    f"Found test failure in step {step} {'for test ' + suite.name if self.firewatch_config.verbose_test_failure_reporting else ''}",
                                )

        # Convert dictionary failures into actual failure objects.
        # This is done here because keep failures_list items as dictionaries allows us to make the "if failure not in failures_list" check above.
        failures = []
        for failure in failures_list:
            failures.append(
                Failure(
                    failed_step=failure["step"],
                    failure_type=failure["failure_type"],
                    failed_test_name=failure["failed_test_name"],
                    failed_test_junit_path=failure["failed_test_junit_path"],
                ),
            )

        return failures

    def _get_timestamp(
        self,
        job_name: Optional[str],
        build_id: Optional[str],
    ) -> Optional[int]:
        """
        Fetches the UNIX timestamp of job

        Args:
            job_name (Optional[str]): The name of the job to get timestamp for.
            build_id (Optional[str]): The build ID of the job to get timestamp for.

        Returns:
            Optional[int]: The timestamp if found, otherwise None.
        """

        client = storage.Client()
        bucket = client.bucket(self.gcs_bucket)
        blob = bucket.blob(f"{job_name}/{build_id}/started.json")

        try:
            started_json = json.loads(blob.download_as_text())
            return started_json.get("timestamp")
        except Exception as e:
            self.logger.error(
                f"Failed to get timestamp for job {job_name} with build ID {build_id} from started.json: {e}"
            )
            return None

    def _get_all_build_ids(
        self,
        job_name: Optional[str],
    ) -> list[str]:
        """
        Get the list of all build IDs from the job directory.

        Args:
            job_name (Optional[str]): The name of the job to get timestamp for.

        Returns:
            List[str]: A list of build IDs.
        """
        client = storage.Client()
        bucket = client.bucket(self.gcs_bucket)
        prefix = f"logs/{job_name}/"
        blobs = bucket.list_blobs(prefix=prefix, delimiter="/")

        build_ids = []
        for page in blobs.pages:
            build_ids.extend(page.prefixes)

        # Get the build IDs from the prefixes
        build_ids = [prefix.split("/")[-2] for prefix in build_ids if prefix.endswith("/")]
        self.logger.info(f"Build IDs retrieved for {job_name}: {build_ids}")
        return build_ids

    def _check_is_retriggered(
        self,
        job_name: Optional[str],
        build_id: Optional[str],
    ) -> bool:
        """Check if the current job build is retriggered within the same week as a previous build.

        Args:
            job_name (Optional[str]): The name of the job to get timestamp for.
            build_id (Optional[str]): The build ID of the job to get timestamp for.

        Returns:
            bool: True if retriggered within the same week, False otherwise.
        """
        if build_id is None:
            self.logger.error("build_id cannot be None")
            return False

        current_timestamp = self._get_timestamp(job_name, build_id)
        if current_timestamp is None:
            return False

        current_datetime = datetime.fromtimestamp(current_timestamp, tz=timezone.utc)

        # Calculate the start of the current week (Monday, 00:00 UTC)
        week_start = current_datetime - timedelta(days=current_datetime.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        build_ids = sorted(self._get_all_build_ids(job_name))
        # Ensure all build_ids are valid integers
        previous_builds = [b_id for b_id in build_ids if b_id is not None and int(b_id) < int(build_id)]
        if not previous_builds:
            self.logger.info("No previous build found within the same week.")
            return False

        # Iterate in descending order to find the previous build within the same week
        for prev_build_id in reversed(previous_builds):
            prev_timestamp = self._get_timestamp(job_name, prev_build_id)
            if prev_timestamp is None:
                continue
            prev_datetime = datetime.fromtimestamp(prev_timestamp, tz=timezone.utc)
            if week_start <= prev_datetime < current_datetime:
                self.logger.info(f"Previous build within the same week found: {prev_build_id}")
                return True
        return False
