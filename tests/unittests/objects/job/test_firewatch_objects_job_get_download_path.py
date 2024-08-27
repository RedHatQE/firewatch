from unittest.mock import patch

from src.objects.job import Job
from tests.unittests.objects.job.job_base_test import JobBaseTest


class TestGetDownloadPath(JobBaseTest):
    mock_exists = patch("os.path.exists")
    mock_exists.start()
    mock_mkdir = patch("os.mkdir")
    mock_mkdir.start()

    def test_get_download_path_not_exists(self):
        job = Job(
            name="rehearse-1234-job1",
            name_safe="job1_safe",
            build_id="123",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )
        self.mock_exists.return_value = False
        path = job._get_download_path("123")
        self.assertEqual(path, "/tmp/123")

    def test_get_download_path_exists(self):
        job = Job(
            name="rehearse-1234-job1",
            name_safe="job1_safe",
            build_id="123",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )
        self.mock_exists.return_value = True
        path = job._get_download_path("123")
        self.assertEqual(path, "/tmp/123")
