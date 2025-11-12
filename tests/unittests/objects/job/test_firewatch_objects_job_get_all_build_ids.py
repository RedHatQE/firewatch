import unittest
from unittest.mock import patch, MagicMock
from src.objects.job import Job
from tests.unittests.objects.job.job_base_test import JobBaseTest


class TestGetAllBuildIds(JobBaseTest):
    @patch("src.objects.job.storage.Client")
    def test_get_all_build_ids_rehearsal_job(self, mock_storage_client):
        """
        Tests that _get_all_build_ids uses the 'pr-logs' prefix for rehearsal jobs.
        """
        # --- Setup Mocks ---
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blobs = MagicMock()

        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.list_blobs.return_value = mock_blobs

        # Mock the list of *correct* prefixes for a rehearsal job
        mock_blobs.pages = [
            MagicMock(
                prefixes=[
                    "pr-logs/pull/openshift_release/1234/rehearse-1234-job1/8123/",
                    "pr-logs/pull/openshift_release/1234/rehearse-1234-job1/8124/",
                ]
            )
        ]

        # --- Create Rehearsal Job ---
        job = Job(
            name="rehearse-1234-job1",
            name_safe="job1_safe",
            build_id="8124",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )

        # --- Run Method ---
        build_ids = job._get_all_build_ids(
            job_name="rehearse-1234-job1", storage_client=mock_client, gcs_bucket="bucket1"
        )

        # --- Assertions ---
        # 1. Assert the list is correct
        assert build_ids == ["8123", "8124"]

        # 2. (CRITICAL) Assert the correct prefix was used in the GCS call
        expected_prefix = "pr-logs/pull/openshift_release/1234/rehearse-1234-job1/"
        mock_bucket.list_blobs.assert_called_with(prefix=expected_prefix, delimiter="/")

    @patch("src.objects.job.storage.Client")
    def test_get_all_build_ids_regular_job(self, mock_storage_client):
        """
        Tests that _get_all_build_ids uses the 'logs' prefix for regular jobs.
        """
        # --- Setup Mocks ---
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blobs = MagicMock()

        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.list_blobs.return_value = mock_blobs

        # Mock the list of prefixes for a regular job
        mock_blobs.pages = [
            MagicMock(
                prefixes=[
                    "logs/periodic-job-1/100/",
                    "logs/periodic-job-1/101/",
                ]
            )
        ]

        # --- Create Regular Job ---
        job = Job(
            name="periodic-job-1",
            name_safe="job1_safe",
            build_id="101",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )

        # --- Run Method ---
        build_ids = job._get_all_build_ids(job_name="periodic-job-1", storage_client=mock_client, gcs_bucket="bucket1")

        # --- Assertions ---
        # 1. Assert the list is correct
        assert build_ids == ["100", "101"]

        # 2. (CRITICAL) Assert the correct prefix was used in the GCS call
        expected_prefix = "logs/periodic-job-1/"
        mock_bucket.list_blobs.assert_called_with(prefix=expected_prefix, delimiter="/")


if __name__ == "__main__":
    unittest.main()
