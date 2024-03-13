import click
from pathlib import Path
from simple_logger.logger import get_logger
from jinja2 import Environment
from src.utils.const import JIRA_CONFIG_TEMPLATE

LOGGER = get_logger(name=__name__)


def render_jira_config(
    server_url: str,
    token: str,
    output_file: str,
) -> str:
    """
    Uses Jinja to render the Jira configuration file

    Args:
        server_url (str): Jira server URL, i.e "https://issues.stage.redhat.com"
        token (str): Jira API token
        output_file (str): Where the rendered config will be stored.

    Returns:
        str: The path to the rendered Jira configuration file
    """

    template = Environment().from_string(JIRA_CONFIG_TEMPLATE)
    with open(output_file, "w") as file:
        file.write(template.render(server_url=server_url, token=token))
        LOGGER.info(f"Jira config file written to: {output_file}")
        return file.name


def get_file_contents(file_path: str) -> str:
    """
    Reads the contents of file_path and returns it.

    Args:
        file_path (str): The path to the file to read

    Returns:
        str: A string object that represents the Jira API token
    """
    try:
        file_content = Path(file_path).read_text().strip()
        return file_content
    except Exception as ex:
        LOGGER.error(
            f"Failed to read contents of {file_path}. Error: {ex}",
        )
        raise click.Abort()
