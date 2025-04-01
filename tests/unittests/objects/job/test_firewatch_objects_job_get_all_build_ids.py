import unittest
from unittest.mock import patch, MagicMock
from src.objects.job import Job
from tests.unittests.objects.job.job_base_test import JobBaseTest


class TestGetAllBuildIds(JobBaseTest):
    @patch("src.objects.job.storage.Client")
    def test_get_all_build_ids(self, mock_storage_client):
        # Mock the storage client and bucket
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blobs = MagicMock()

        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.list_blobs.return_value = mock_blobs

        # Mock the list of blobs with prefixes
        mock_blobs.pages = [
            MagicMock(
                prefixes=[
                    "logs/rehearse-1234-job1/8123/",
                    "logs/rehearse-1234-job1/8124/",
                    "logs/rehearse-1234-job1/8125/",
                ]
            )
        ]

        job = Job(
            name="rehearse-1234-job1",
            name_safe="job1_safe",
            build_id="8123",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )

        build_ids = job._get_all_build_ids(job_name="rehearse-1234-job1")
        assert build_ids == ["8123", "8124", "8125"]


if __name__ == "__main__":
    unittest.main()
