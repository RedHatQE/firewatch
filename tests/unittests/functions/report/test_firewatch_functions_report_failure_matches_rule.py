import os
import unittest
from unittest.mock import patch, mock_open, MagicMock

from cli.objects.configuration import Configuration
from cli.objects.failure import Failure
from cli.objects.failure_rule import FailureRule
from cli.objects.job import Job
from cli.report import Report


class TestFailureMatchesRule(unittest.TestCase):

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
        self.failure = Failure(failed_step="failed-step", failure_type="test_failure")
        default_rule_dict = {
            "step": "!none",
            "failure_type": "!none",
            "classification": "!none",
            "jira_project": self.config.default_jira_project,
        }
        self.default_rule = FailureRule(default_rule_dict)

    def tearDown(self):
        patch.stopall()

    def test_failure_matches_rule_failure_has_no_match(self):
        no_match_rule = FailureRule(
            rule_dict={
                "step": "other-step",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
            },
        )
        rules = [no_match_rule]
        matching_rules = self.report.failure_matches_rule(
            failure=self.failure,
            rules=rules,
            default_jira_project=self.config.default_jira_project,
        )
        assert len(matching_rules) == 1
        assert matching_rules[0].step == self.default_rule.step

    def test_failure_matches_rule_failure_matches_ignore_rule(self):
        ignore_rule = FailureRule(
            rule_dict={
                "step": "failed-step",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
                "ignore": "true",
            },
        )
        rules = [ignore_rule]
        matching_rules = self.report.failure_matches_rule(
            failure=self.failure,
            rules=rules,
            default_jira_project=self.config.default_jira_project,
        )
        assert len(matching_rules) == 0

    def test_failure_matches_rule_with_matches(self):
        match_rule = FailureRule(
            rule_dict={
                "step": "failed-step",
                "failure_type": "test_failure",
                "classification": "NONE",
                "jira_project": "NONE",
            },
        )
        rules = [match_rule]
        matching_rules = self.report.failure_matches_rule(
            failure=self.failure,
            rules=rules,
            default_jira_project=self.config.default_jira_project,
        )
        assert len(matching_rules) == 1
        assert (matching_rules[0].step == match_rule.step) and (
            matching_rules[0].failure_type == match_rule.failure_type
        )
