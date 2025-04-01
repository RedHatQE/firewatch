from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from src.objects.job import Job


def test_check_is_retriggered():
    with patch("src.objects.job.storage.Client") as mock_storage_client:
        mock_client = MagicMock()
        mock_bucket = MagicMock()
        mock_storage_client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket

        # Mock the list of blobs with prefixes
        mock_blobs = MagicMock()
        mock_blobs.pages = [
            MagicMock(
                prefixes=[
                    "logs/rehearse-1234-job1/8123/",
                    "logs/rehearse-1234-job1/8124/",
                    "logs/rehearse-1234-job1/8125/",
                ]
            )
        ]
        mock_bucket.list_blobs.return_value = mock_blobs

        # Ensure _get_timestamp returns valid timestamps
        job = Job(
            name="rehearse-1234-job1",
            name_safe="job1_safe",
            build_id="8125",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=None,
        )

        # Mock the content of the started.json files
        # https://prow.ci.openshift.org/job-history/gs/test-platform-results/logs/periodic-ci-oadp-qe-oadp-qe-automation-main-oadp1.4-ocp4.18-lp-interop-oadp-interop-aws
        with patch.object(
            job,
            "_get_timestamp",
            side_effect=lambda job_name, build_id: {
                "8123": 1739167564,  # Mon, Feb 10, 2025(previous week build)
                "8124": 1739772346,  # Mon, Feb 17, 2025(current week build)
                "8125": 1739979486,  # Wed, Feb 19, 2025(retriggered build)
                "8126": 1740377174,  # Mon, Feb 24, 2025 (newer week build)
            }.get(build_id, None),
        ):
            with patch("src.objects.job.datetime", autospec=True) as mock_datetime:
                mock_datetime.now.return_value = datetime(2021, 4, 3, tzinfo=timezone.utc)
                mock_datetime.fromtimestamp.side_effect = lambda ts, tz=timezone.utc: datetime.fromtimestamp(ts, tz)

                is_retriggered = job._check_is_retriggered(job_name="rehearse-1234-job1", build_id="8125")

        assert is_retriggered is True
