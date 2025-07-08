import yaml
from urllib.request import urlopen
from typing import Optional
from simple_logger.logger import get_logger

logger = get_logger(__name__)


def read_url_config(path: str) -> str:
    try:
        response = urlopen(path)
        response_data = response.read()
        return response_data
    # Path is not a URL type
    except ValueError:
        # Read the contents of the config file
        try:
            with open(path) as file:
                base_config_str = file.read()
                return base_config_str
        except Exception:
            pass
    # Path is an invalid or unreadable URL
    except Exception:
        pass
    return ""


def get_project_config_data(project_file_path: Optional[str]) -> dict:
    """
    Gets the config data from either a configuration file or from the FIREWATCH_CONFIG environment variable or
    both.
    Will exit with code 1 if both a config file isn't provided (or isn't readable) or the FIREWATCH_CONFIG environment variable isn't set.
    The configuration file is considered as the basis of the configuration data,
    And it will be overridden and expended by the additional set of rules that will be applied to the env var.

    Args:
        project_file_path (Optional[str]): The firewatch config can be stored in a file or url path.

    Returns:
        dict: A dictionary object representing the firewatch config data.
    """
    project_config_str = ""
    project_config_data = {}

    if project_file_path is not None:
        project_config_str = read_url_config(path=project_file_path)
        if not project_config_str:
            logger.error(
                f"Unable to read project config file at {project_file_path}."
                f"\nPlease verify permissions/path and try again.",
            )
            exit(1)

    # Verify that the config data is properly formatted YAML
    if project_config_str:
        try:
            project_config_data = yaml.safe_load(project_config_str)
        except:
            logger.error(
                "The Firewatch project config file contains malformed YAML.",
            )
            exit(1)

    return project_config_data
