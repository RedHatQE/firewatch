from unittest.mock import patch, MagicMock
from src.objects.job import Job
from tests.unittests.objects.job.job_base_test import JobBaseTest


class TestGetDownloadPath(JobBaseTest):
    @patch("os.path.exists")
    @patch("os.mkdir")
    @patch("src.objects.job.storage.Client")
    def test_get_download_path_not_exists(self, mock_storage_client, mock_mkdir, mock_exists):
        mock_exists.return_value = False
        mock_client = MagicMock()
        mock_storage_client.return_value = mock_client

        job = Job(
            name="rehearse-1234-job1",
            name_safe="job1_safe",
            build_id="123",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )
        path = job._get_download_path("123")
        self.assertEqual(path, "/tmp/123")

    @patch("os.path.exists")
    @patch("os.mkdir")
    @patch("src.objects.job.storage.Client")
    def test_get_download_path_exists(self, mock_storage_client, mock_mkdir, mock_exists):
        mock_exists.return_value = True
        mock_client = MagicMock()
        mock_storage_client.return_value = mock_client

        job = Job(
            name="rehearse-1234-job1",
            name_safe="job1_safe",
            build_id="123",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )
        path = job._get_download_path("123")
        self.assertEqual(path, "/tmp/123")
