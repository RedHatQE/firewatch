import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from src.objects.job import Job
from tests.unittests.objects.job.job_base_test import JobBaseTest

class TestCheckIsRetriggered(JobBaseTest):
    @patch("src.objects.job.storage.Client")
    def test_check_is_retriggered(self, mock_storage_client):
        # Mock the storage client and bucket
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_blobs = MagicMock()

        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.list_blobs.return_value = mock_blobs

        # Mock the list of blobs with prefixes
        mock_blobs.pages = [
            MagicMock(prefixes=[
                "logs/rehearse-1234-job1/8123/",
                "logs/rehearse-1234-job1/8124/",
                "logs/rehearse-1234-job1/8125/",
            ])
        ]

        # Mock the content of the started.json files
        def mock_download_as_text(blob_name):
            if blob_name == "logs/rehearse-1234-job1/8123/started.json":
                return '{"timestamp": 1617184800}'  # Monday, March 31, 2021 00:00:00 GMT
            elif blob_name == "logs/rehearse-1234-job1/8124/started.json":
                return '{"timestamp": 1617271200}'  # Tuesday, April 1, 2021 00:00:00 GMT
            elif blob_name == "logs/rehearse-1234-job1/8125/started.json":
                return '{"timestamp": 1617357600}'  # Wednesday, April 2, 2021 00:00:00 GMT
            return '{"timestamp": 0}'

        mock_blob = MagicMock()
        mock_blob.download_as_text.side_effect = mock_download_as_text
        mock_bucket.blob.return_value = mock_blob

        job = Job(
            name="rehearse-1234-job1",
            name_safe="job1_safe",
            build_id="8126",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )

        # Mock the current timestamp to be within the same week
        with patch("src.objects.job.datetime") as mock_datetime:
            mock_datetime.fromtimestamp.return_value = datetime(2021, 4, 3, tzinfo=timezone.utc)
            mock_datetime.now.return_value = datetime(2021, 4, 3, tzinfo=timezone.utc)
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            is_retriggered = job._check_is_retriggered(job_name="rehearse-1234-job1", build_id="8126")
            assert is_retriggered is True

if __name__ == "__main__":
    unittest.main()