PROJECT_TEMPLATE_PATH = "src/templates/settings.yaml"
PROJECT_DATA_SCHEMA = {
    "rules_config_file_path": {"type": str, "required": False},
    "jira_config_path": {"type": str, "required": False},
    "default_jira_project": {"type": str, "required": False},
    "default_jira_additional_labels": {"type": str, "required": False},
    "fail_with_test_failures": {"type": bool, "required": False},
    "fail_with_pod_failures": {"type": bool, "required": False},
    "keep_job_dir": {"type": bool, "required": False},
    "additional_labels_file": {"type": str, "required": False},
}
