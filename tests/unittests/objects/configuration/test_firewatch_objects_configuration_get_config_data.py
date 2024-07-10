import os
import tempfile
from unittest.mock import patch

from src.objects.configuration import Configuration
from tests.unittests.objects.configuration.configuration_base_test import (
    ConfigurationBaseTest,
)


@patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "TEST"})
class TestGetConfigData(ConfigurationBaseTest):
    def test_configuration_gets_config_data_with_valid_file_path(self):
        valid_config_data = (
            '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}'
        )
        with tempfile.TemporaryDirectory() as tmp_path:
            config_file = os.path.join(tmp_path, "config.json")
            with open(config_file, "w") as f:
                f.write(valid_config_data)
            config = Configuration(
                jira=self.mock_jira,
                fail_with_test_failures=True,
                fail_with_pod_failures=True,
                keep_job_dir=True,
                verbose_test_failure_reporting=True,
                verbose_test_failure_reporting_ticket_limit=10,
                config_file_path=config_file,
            )
            assert config.config_data == {
                "failure_rules": [
                    {
                        "step": "step1",
                        "failure_type": "pod_failure",
                        "classification": "none",
                    },
                ],
            }

    def test_configuration_gets_config_data_with_invalid_file_path(self):
        with self.assertRaises(SystemExit):
            Configuration(
                jira=self.mock_jira,
                fail_with_test_failures=True,
                fail_with_pod_failures=True,
                keep_job_dir=True,
                verbose_test_failure_reporting=True,
                verbose_test_failure_reporting_ticket_limit=10,
                config_file_path="/tmp/invalid.json",
            )

    @patch.dict(
        os.environ,
        {
            "FIREWATCH_CONFIG": '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}',
        },
    )
    def test_configuration_gets_config_data_with_valid_env_var(self):
        config = Configuration(
            jira=self.mock_jira,
            fail_with_test_failures=True,
            fail_with_pod_failures=True,
            keep_job_dir=True,
            verbose_test_failure_reporting=True,
            verbose_test_failure_reporting_ticket_limit=10,
            config_file_path=None,
        )
        assert config.config_data == {
            "failure_rules": [
                {
                    "step": "step1",
                    "failure_type": "pod_failure",
                    "classification": "none",
                },
            ],
        }

    def test_configuration_gets_config_data_with_no_env_var(self):
        if "FIREWATCH_CONFIG" in os.environ:
            del os.environ["FIREWATCH_CONFIG"]
        with self.assertRaises(SystemExit):
            Configuration(
                jira=self.mock_jira,
                fail_with_test_failures=True,
                fail_with_pod_failures=True,
                keep_job_dir=True,
                verbose_test_failure_reporting=True,
                verbose_test_failure_reporting_ticket_limit=10,
                config_file_path=None,
            )

    @patch.dict(
        os.environ,
        {
            "FIREWATCH_CONFIG": '{"failure_rules": [{"step": "specific-step-pattern","failure_type": "pod_failure",'
            '"classification": "none"},{"step": "*step-logic*","failure_type": "pod_failure",'
            '"classification": "none"}]}',
        },
    )
    def test_configuration_gets_config_data_with_base_config_using_patterns(self):
        base_config_data = (
            '{"failure_rules": [{"step": "*step-pattern*", "failure_type": "pod_failure", '
            '"classification": "none"}, {"step": "old-step-logic", "failure_type": "pod_failure", '
            '"classification": "none"}]}'
        )
        with tempfile.TemporaryDirectory() as tmp_path:
            base_config_file = os.path.join(tmp_path, "base_config.json")
            with open(base_config_file, "w") as f:
                f.write(base_config_data)
            config = Configuration(
                jira=self.mock_jira,
                fail_with_test_failures=True,
                fail_with_pod_failures=True,
                keep_job_dir=True,
                verbose_test_failure_reporting=True,
                verbose_test_failure_reporting_ticket_limit=10,
                config_file_path=base_config_file,
            )
            new_steps = [rule["step"] for rule in config.config_data["failure_rules"]]
            assert new_steps == ["specific-step-pattern", "*step-logic*", "*step-pattern*"]

    def test_configuration_gets_config_data_with_base_config_from_invalid_url(self):
        base_config_file = "https://"
        with self.assertRaises(SystemExit):
            Configuration(
                jira=self.mock_jira,
                fail_with_test_failures=True,
                fail_with_pod_failures=True,
                keep_job_dir=True,
                verbose_test_failure_reporting=True,
                verbose_test_failure_reporting_ticket_limit=10,
                config_file_path=base_config_file,
            )
