import unittest
from unittest.mock import patch, MagicMock
from src.objects.job import Job
from tests.unittests.objects.job.job_base_test import JobBaseTest


class TestGetTimestamp(JobBaseTest):
    @patch("src.objects.job.storage.Client")
    def test_get_timestamp_rehearsal_job(self, mock_storage_client):
        """
        Tests that _get_timestamp uses the correct 'pr-logs' path for rehearsal jobs.
        """
        # --- Setup Mocks ---
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()

        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.download_as_text.return_value = '{"timestamp": 1617184800}'

        # --- Create Rehearsal Job ---
        # __init__ will set self.is_rehearsal = True and self.pr_id = "1234"
        job = Job(
            name="rehearse-1234-job1",
            name_safe="job1_safe",
            build_id="123",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )

        # --- Run Method ---
        timestamp = job._get_timestamp(
            job_name="rehearse-1234-job1",
            build_id="123",
            storage_client=mock_client,
            gcs_bucket="bucket1",  # Pass the bucket name as a string
        )

        # --- Assertions ---
        # 1. Assert the return value is correct
        assert timestamp == 1617184800

        # 2. (CRITICAL) Assert the correct path was used
        expected_path = "pr-logs/pull/openshift_release/1234/rehearse-1234-job1/123/started.json"
        mock_bucket.blob.assert_called_with(expected_path)

    @patch("src.objects.job.storage.Client")
    def test_get_timestamp_regular_job(self, mock_storage_client):
        """
        Tests that _get_timestamp uses the original 'logs' path for regular jobs.
        """
        # --- Setup Mocks ---
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()

        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.download_as_text.return_value = '{"timestamp": 1617184800}'

        # --- Create Regular Job ---
        # __init__ will set self.is_rehearsal = False
        job = Job(
            name="periodic-ci-job-1",
            name_safe="job1_safe",
            build_id="456",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )

        # --- Run Method ---
        timestamp = job._get_timestamp(
            job_name="periodic-ci-job-1", build_id="456", storage_client=mock_client, gcs_bucket="bucket1"
        )

        # --- Assertions ---
        # 1. Assert the return value is correct
        assert timestamp == 1617184800

        # 2. (CRITICAL) Assert the correct (original) path was used
        expected_path = "logs/periodic-ci-job-1/456/started.json"
        mock_bucket.blob.assert_called_with(expected_path)


if __name__ == "__main__":
    unittest.main()
