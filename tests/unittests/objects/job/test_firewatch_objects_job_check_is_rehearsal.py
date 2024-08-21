from src.objects.job import Job
from tests.unittests.objects.job.job_base_test import JobBaseTest


class TestCheckIsRehearsal(JobBaseTest):
    def test_rehearsal_job_true(self):
        job = Job(
            name="rehearse-1234-job1",
            name_safe="job1_safe",
            build_id="123",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )
        self.assertTrue(job.is_rehearsal)

    def test_rehearsal_job_false(self):
        job = Job(
            name="job1",
            name_safe="job1_safe",
            build_id="123",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )
        self.assertFalse(job.is_rehearsal)
