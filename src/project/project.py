# import yaml
# from pathlib import Path
# from jinja2 import Environment, FileSystemLoader
from simple_logger.logger import get_logger
from src.project.config import load_settings_from_dict


class Project:
    def __init__(
        self,
        project_params,
    ):
        self.logger = get_logger(__name__)

        import ipdb

        ipdb.set_trace()
        project_config_file_path = project_params["project_config_path"]
        settings = load_settings_from_dict(project_config_file_path)

        # validate_settings(settings)
        self.project_data = settings.as_dict()
        self.jira_config_path = project_params.get("jira_config_path", settings.jira_config_path)
        self.default_jira_project = project_params.get("firewatch_default_jira_project", settings.default_jira_project)
        self.fail_with_test_failures = project_params.get("fail_with_test_failures", settings.fail_with_test_failures)
        self.fail_with_pod_failures = project_params.get("fail_with_pod_failures", settings.fail_with_pod_failures)
        self.keep_job_dir = project_params.get("keep_job_dir", settings.keep_job_dir)
        self.additional_labels_file = project_params.get("additional_labels_file", settings.additional_labels_file)
        self.verbose_test_failure_reporting = project_params.get(
            "verbose_test_failure_reporting", settings.verbose_test_failure_reporting
        )
        self.verbose_test_failure_reporting_ticket_limit = project_params.get(
            "verbose_test_failure_reporting_ticket_limit", settings.verbose_test_failure_reporting_ticket_limit
        )
        self.rules_config_file_path = project_params.get("firewatch_rules_config_path", settings.rules_config_file_path)

    # def _get_project_config_data(self, project_file_path: Optional[str]) -> dict:
    #     """
    #     Gets the config data from either a configuration file or from the FIREWATCH_CONFIG environment variable or
    #     both.
    #     Will exit with code 1 if both a config file isn't provided (or isn't readable) or the FIREWATCH_CONFIG environment variable isn't set.
    #     The configuration file is considered as the basis of the configuration data,
    #     And it will be overridden and expended by the additional set of rules that will be applied to the env var.
    #
    #     Args:
    #         project_file_path (Optional[str]): The firewatch config can be stored in a file or url path.
    #
    #     Returns:
    #         dict[Any, Any]: A dictionary object representing the firewatch config data.
    #     """
    #     project_config_str = ""
    #     project_config_data = {}
    #     rendered_project_config_data = {}
    #
    #     if project_file_path is not None:
    #         project_config_str = read_url_config(path=project_file_path)
    #         if not project_config_str:
    #             self.logger.error(
    #                 f"Unable to read project config file at {project_file_path}."
    #                 f"\nPlease verify permissions/path and try again.",
    #             )
    #             exit(1)
    #
    #     # Verify that the config data is properly formatted YAML
    #     if project_config_str:
    #         try:
    #             project_config_data = yaml.safe_load(project_config_str)
    #         except:
    #             self.logger.error(
    #                 "The Firewatch project config file contains malformed YAML.",
    #             )
    #             exit(1)
    #
    #     if project_config_data:
    #         template_dir = Path(PROJECT_TEMPLATE_PATH).parent
    #         template_filename = Path(PROJECT_TEMPLATE_PATH).name
    #
    #         # Load Jinja template file
    #         env = Environment(loader=FileSystemLoader(template_dir))
    #         template = env.get_template(template_filename)
    #
    #         # Render the template with the loaded dictionary
    #         rendered_project_config_data = template.render(**project_config_data)
    #
    #     return rendered_project_config_data
