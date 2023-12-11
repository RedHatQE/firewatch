import tempfile

from cli.objects.job import Job
from tests.unittests import helpers
from tests.unittests.objects.job.job_base_test import JobBaseTest


class TestFindPodFailures(JobBaseTest):
    def test_find_pod_failures_with_failures(self):
        temp_dir = tempfile.TemporaryDirectory()
        logs_dir = helpers._get_tmp_logs_dir(tmp_path=temp_dir.name)
        job = Job("job1", "job1_safe", "123", "bucket1", self.config)
        helpers._create_failed_step_pod(logs_dir=logs_dir)
        pod_failures = job._find_pod_failures(logs_dir=logs_dir)
        assert len(pod_failures) == 1

    def test_find_pod_failures_without_failures(self):
        temp_dir = tempfile.TemporaryDirectory()
        logs_dir = helpers._get_tmp_logs_dir(tmp_path=temp_dir.name)
        job = Job("job1", "job1_safe", "123", "bucket1", self.config)
        helpers._create_successful_step_pod(logs_dir=logs_dir)
        pod_failures = job._find_pod_failures(logs_dir=logs_dir)
        assert len(pod_failures) == 0
