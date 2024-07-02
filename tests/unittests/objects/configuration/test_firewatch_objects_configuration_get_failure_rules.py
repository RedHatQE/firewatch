import os
from unittest.mock import patch

from src.objects.configuration import Configuration
from tests.unittests.objects.configuration.configuration_base_test import (
    ConfigurationBaseTest,
)


@patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "TEST"})
class TestGetFailureRules(ConfigurationBaseTest):
    @patch.dict(
        os.environ,
        {
            "FIREWATCH_CONFIG": '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}',
        },
    )
    def test_configuration_gets_failure_rules_with_valid_input(self):
        config = Configuration(
            jira=self.mock_jira,
            fail_with_test_failures=False,
            fail_with_pod_failures=False,
            keep_job_dir=False,
            verbose_test_failure_reporting=False,
        )
        failure_rules = config._get_failure_rules(
            config.config_data.get("failure_rules"),
        )
        assert len(failure_rules) == 1
        assert failure_rules[0].step == "step1"
        assert failure_rules[0].failure_type == "pod_failure"
        assert failure_rules[0].classification == "none"
