from cli.objects.job import Job
from tests.unittests.objects.job.job_base_test import JobBaseTest


class TestJob(JobBaseTest):
    def test_initialization_with_valid_parameters(self):
        job = Job("job1", "job1_safe", "123", "bucket1", self.config)
        self.assertEqual(job.name, "job1")
        self.assertEqual(job.name_safe, "job1_safe")
        self.assertEqual(job.build_id, "123")
        self.assertEqual(job.gcs_bucket, "bucket1")
