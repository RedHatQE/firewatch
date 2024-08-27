import tempfile

from src.objects.job import Job
from tests.unittests import helpers
from tests.unittests.objects.job.job_base_test import JobBaseTest


class TestFindFailures(JobBaseTest):
    def test_find_test_failures_no_pod_failures(self):
        temp_dir = tempfile.TemporaryDirectory()
        junit_dir = helpers._get_tmp_junit_dir(tmp_path=temp_dir.name)
        logs_dir = helpers._get_tmp_logs_dir(tmp_path=temp_dir.name)
        job = Job(
            name="rehearse-1234-job1",
            name_safe="job1_safe",
            build_id="123",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )
        helpers._create_failed_step_junit(junit_dir=junit_dir)
        failures = job._find_failures(
            junit_dir=junit_dir,
            logs_dir=logs_dir,
        )
        assert failures[0].failure_type == "test_failure" and failures[0].step == "failed-step"

    def test_find_pod_failures_no_test_failures(self):
        temp_dir = tempfile.TemporaryDirectory()
        junit_dir = helpers._get_tmp_junit_dir(tmp_path=temp_dir.name)
        logs_dir = helpers._get_tmp_logs_dir(tmp_path=temp_dir.name)
        job = Job(
            name="rehearse-1234-job1",
            name_safe="job1_safe",
            build_id="123",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )
        helpers._create_failed_step_pod(logs_dir=logs_dir)
        failures = job._find_failures(
            junit_dir=junit_dir,
            logs_dir=logs_dir,
        )
        assert failures[0].failure_type == "pod_failure" and failures[0].step == "failed-step"

    def test_find_all_failures(self):
        temp_dir = tempfile.TemporaryDirectory()
        junit_dir = helpers._get_tmp_junit_dir(tmp_path=temp_dir.name)
        logs_dir = helpers._get_tmp_logs_dir(tmp_path=temp_dir.name)
        job = Job(
            name="rehearse-1234-job1",
            name_safe="job1_safe",
            build_id="123",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )
        helpers._create_failed_step_pod(logs_dir=logs_dir)
        helpers._create_failed_step_junit(junit_dir=junit_dir)
        failures = job._find_failures(
            junit_dir=junit_dir,
            logs_dir=logs_dir,
        )
        assert failures[0].failure_type == "test_failure" and failures[0].step == "failed-step"

    def test_failures_no_failures(self):
        temp_dir = tempfile.TemporaryDirectory()
        junit_dir = helpers._get_tmp_junit_dir(tmp_path=temp_dir.name)
        logs_dir = helpers._get_tmp_logs_dir(tmp_path=temp_dir.name)
        job = Job(
            name="rehearse-1234-job1",
            name_safe="job1_safe",
            build_id="123",
            gcs_bucket="bucket1",
            gcs_creds_file=None,
            firewatch_config=self.config,
        )
        helpers._create_successful_step_pod(logs_dir=logs_dir)
        helpers._create_successful_step_junit(junit_dir=junit_dir)
        failures = job._find_failures(
            junit_dir=junit_dir,
            logs_dir=logs_dir,
        )
        assert not failures
