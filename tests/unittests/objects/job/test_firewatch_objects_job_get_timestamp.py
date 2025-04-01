import unittest
from unittest.mock import patch, MagicMock
from src.objects.job import Job
from tests.unittests.objects.job.job_base_test import JobBaseTest


class TestGetTimestamp(JobBaseTest):
    @patch("src.objects.job.storage.Client")
    def test_get_timestamp(self, mock_storage_client):
        # Mock the storage client and bucket
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blob = MagicMock()

        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        # Mock the content of the started.json file
        mock_blob.download_as_text.return_value = '{"timestamp": 1617184800}'

        job = Job(
            name="rehearse-1234-job1",
            name_safe="job1_safe",
            build_id="123",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )

        timestamp = job._get_timestamp(job_name="rehearse-1234-job1", build_id="123")
        assert timestamp == 1617184800


if __name__ == "__main__":
    unittest.main()
