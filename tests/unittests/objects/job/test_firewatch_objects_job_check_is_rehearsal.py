from cli.objects.job import Job
from tests.unittests.objects.job.job_base_test import JobBaseTest


class TestCheckIsRehearsal(JobBaseTest):
    def test_rehearsal_job_true(self):
        job = Job("rehearse_job1", "job1_safe", "123", "bucket1", self.config)
        self.assertTrue(job.is_rehearsal)

    def test_rehearsal_job_false(self):
        job = Job("job1", "job1_safe", "123", "bucket1", self.config)
        self.assertFalse(job.is_rehearsal)
