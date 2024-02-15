import tempfile

from src.objects.job import Job
from tests.unittests import helpers
from tests.unittests.objects.job.job_base_test import JobBaseTest


class TestFindTestFailures(JobBaseTest):
    def test_find_test_failures_with_failures(self):
        temp_dir = tempfile.TemporaryDirectory()
        junit_dir = helpers._get_tmp_junit_dir(tmp_path=temp_dir.name)
        job = Job("job1", "job1_safe", "123", "bucket1", self.config)
        helpers._create_failed_step_junit(junit_dir=junit_dir)
        failures = job._find_test_failures(junit_dir=junit_dir)
        assert len(failures) == 1

    def test_find_test_failures_without_failures(self):
        temp_dir = tempfile.TemporaryDirectory()
        junit_dir = helpers._get_tmp_junit_dir(tmp_path=temp_dir.name)
        job = Job("job1", "job1_safe", "123", "bucket1", self.config)
        helpers._create_successful_step_junit(junit_dir=junit_dir)
        failures = job._find_test_failures(junit_dir=junit_dir)
        assert len(failures) == 0
