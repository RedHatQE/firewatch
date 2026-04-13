from simple_logger.logger import get_logger
from src.project.config import load_settings_from_dict, validate_settings


class Project:
    def __init__(
        self,
        project_params,
    ):
        self.logger = get_logger(__name__)
        project_config_file_path = project_params.get("project_config_path")
        settings = load_settings_from_dict(project_config_file_path)
        self.project_data = settings.as_dict()
        validate_settings(self.project_data)

        self.jira_config_path = project_params.get("jira_config_path", settings.jira_config_path)
        self.rules_config_file_path = project_params.get("rules_config_file_path", settings.rules_config_file_path)
        self.default_jira_additional_labels = project_params.get(
            "default_jira_additional_labels", settings.default_jira_additional_labels
        )
        self.default_jira_project = project_params.get("default_jira_project", settings.default_jira_project)
        self.fail_with_test_failures = project_params.get("fail_with_test_failures", settings.fail_with_test_failures)
        self.fail_with_pod_failures = project_params.get("fail_with_pod_failures", settings.fail_with_pod_failures)
        self.keep_job_dir = project_params.get("keep_job_dir", settings.keep_job_dir)
        self.additional_labels_file = project_params.get("additional_labels_file", settings.additional_labels_file)
        self.verbose_test_failure_reporting = project_params.get(
            "verbose_test_failure_reporting", settings.verbose_test_failure_reporting
        )
        # Click cli params
        self.verbose_test_failure_reporting_ticket_limit = project_params.get(
            "verbose_test_failure_reporting_ticket_limit"
        )
        self.rules_config_file_path = project_params.get("rules_config_path")
