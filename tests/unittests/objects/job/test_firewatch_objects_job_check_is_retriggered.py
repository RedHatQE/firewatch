from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from src.objects.job import Job
from tests.unittests.objects.job.job_base_test import JobBaseTest


class TestCheckRetrigger(JobBaseTest):
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
            MagicMock(
                prefixes=[
                    "logs/rehearse-1234-job1/8123/",
                    "logs/rehearse-1234-job1/8124/",
                    "logs/rehearse-1234-job1/8125/",
                    "logs/rehearse-1234-job1/8126/",
                ]
            )
        ]

        # Create the Job object
        job = Job(
            name="rehearse-1234-job1",
            name_safe="job1_safe",
            build_id="8125",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )

        # Mock and return the corresponding timestamp for the build_id
        def mock_get_timestamp(*args, **kwargs):
            print("called with:", args, kwargs)
            build_id = kwargs.get("build_id")
            return {
                "8123": 1739167564,  # Mon, Feb 10, 2025 (previous week build)
                "8124": 1739772346,  # Mon, Feb 17, 2025 (current week build)
                "8125": 1739979486,  # Wed, Feb 19, 2025 (retriggered build)
                "8126": 1740377174,  # Mon, Feb 24, 2025 (newer week build)
            }.get(build_id, None)

        # Test the check_is_retriggered method with various build_ids
        # Reference job: https://prow.ci.openshift.org/job-history/gs/test-platform-results/logs/periodic-ci-oadp-qe-oadp-qe-automation-main-oadp1.4-ocp4.18-lp-interop-oadp-interop-aws
        with patch.object(job, "_get_timestamp", side_effect=mock_get_timestamp):
            # Mock datetime to control the current time
            with patch("src.objects.job.datetime", autospec=True) as mock_datetime:
                mock_datetime.now.return_value = datetime(2027, 2, 19, tzinfo=timezone.utc)
                print("Job sees datetime.now as:", datetime.now())
                mock_datetime.fromtimestamp.side_effect = lambda ts, tz=timezone.utc: datetime.fromtimestamp(ts, tz)

                # Provide all required arguments to _check_is_retriggered
                all_build_ids = ["8123", "8124", "8125", "8126"]
                storage_client = mock_client
                gcs_bucket = "bucket1"

                # Current week is Mon, Feb 17, 2025 - Sun, Feb 23, 2025
                # Test for retriggered build
                is_retriggered = job._check_is_retriggered(
                    job_name="rehearse-1234-job1",
                    build_id="8125",
                    timestamp=mock_get_timestamp(build_id="8125"),  # Wed, Feb 19, 2025 (retriggered build)
                    all_build_ids=all_build_ids,
                    storage_client=storage_client,
                    gcs_bucket=gcs_bucket,
                )
                assert is_retriggered is True, "8125 should be considered retriggered in the same week"

                # Test for a build before the current week
                is_not_retriggered = job._check_is_retriggered(
                    job_name="rehearse-1234-job1",
                    build_id="8123",  # Build ID in previous week
                    timestamp=mock_get_timestamp(build_id="8123"),  # Mon, Feb 10, 2025 (previous week build)
                    all_build_ids=all_build_ids,
                    storage_client=storage_client,
                    gcs_bucket=gcs_bucket,
                )
                assert is_not_retriggered is False

                # Test for a future invalid build or outside the current week
                is_retriggered = job._check_is_retriggered(
                    job_name="rehearse-1234-job1",
                    build_id="8126",  # New week build
                    timestamp=mock_get_timestamp(build_id="8126"),  # Mon, Feb 24, 2025 (future week build)
                    all_build_ids=all_build_ids,
                    storage_client=mock_storage_client,
                    gcs_bucket="bucket1",
                )
                assert is_retriggered is False
