import os
import unittest
from unittest.mock import patch, mock_open, MagicMock

from cli.objects.configuration import Configuration
from cli.objects.failure import Failure
from cli.objects.failure_rule import FailureRule
from cli.objects.job import Job
from cli.report import Report


class TestFilterPriorityRulePairs(unittest.TestCase):

    @patch('cli.objects.configuration.Jira')
    @patch.dict(os.environ, {"FIREWATCH_DEFAULT_JIRA_PROJECT": "TEST"})
    @patch.dict(os.environ, {"FIREWATCH_CONFIG": '{"failure_rules": [{"step": "step1", "failure_type": "pod_failure", "classification": "none"}]}'})
    def setUp(self, mock_jira):
        mock_jira.return_value = MagicMock()
        self.config = Configuration(mock_jira, False, False, False)
        self.mock_get_steps = patch.object(Job, '_get_steps', return_value=['step1', 'step2'])
        self.mock_get_steps.start()
        self.mock_logger = patch('cli.objects.job.get_logger')
        self.mock_logger.start().return_value = MagicMock()
        self.mock_storage_client = patch('cli.objects.job.storage.Client.create_anonymous_client')
        self.mock_storage_client.start().return_value = MagicMock()
        self.job = Job('job1', 'job1_safe', '123', 'bucket1', self.config)
        self.report = Report(self.config, self.job)

    def tearDown(self):
        patch.stopall()

    def test_filter_priority_rule_failure_pairs_priorities_set(self):
        # Test when groups/priorities are set
        group_rule_1 = FailureRule(
            rule_dict={
                "step": "failed-step-1",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
                "group": {"name": "failed-steps", "priority": 1},
            },
        )
        group_rule_2 = FailureRule(
            rule_dict={
                "step": "failed-step-2",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
                "group": {"name": "failed-steps", "priority": 2},
            },
        )
        group_failure_1 = Failure(
            failed_step="failed-step-1",
            failure_type="test_failure",
        )
        group_failure_2 = Failure(
            failed_step="failed-step-2",
            failure_type="test_failure",
        )

        original_rule_failure_pairs = [
            {"rule": group_rule_1, "failure": group_failure_1},
            {"rule": group_rule_2, "failure": group_failure_2},
        ]

        filtered_rule_failure_pairs = self.report.filter_priority_rule_failure_pairs(
            rule_failure_pairs=original_rule_failure_pairs,
        )

        assert filtered_rule_failure_pairs == [
            {"rule": group_rule_1, "failure": group_failure_1},
        ]

    def test_filter_priority_rule_failure_pairs_priorities_not_set(self):
        # Test when groups/priorities not set
        rule_1 = FailureRule(
            rule_dict={
                "step": "failed-step-1",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
            },
        )
        rule_2 = FailureRule(
            rule_dict={
                "step": "failed-step-2",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
            },
        )
        failure_1 = Failure(failed_step="failed-step-1", failure_type="test_failure")
        failure_2 = Failure(failed_step="failed-step-2", failure_type="test_failure")

        original_rule_failure_pairs = [
            {"rule": rule_1, "failure": failure_1},
            {"rule": rule_2, "failure": failure_2},
        ]

        filtered_rule_failure_pairs = self.report.filter_priority_rule_failure_pairs(
            rule_failure_pairs=original_rule_failure_pairs,
        )

        assert filtered_rule_failure_pairs == original_rule_failure_pairs
