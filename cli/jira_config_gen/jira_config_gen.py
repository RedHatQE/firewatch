#
# Copyright (C) 2023 Red Hat, Inc.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from pathlib import Path

import click
from jinja2 import Environment
from jinja2 import FileSystemLoader
from simple_logger.logger import get_logger


class JiraConfig:
    def __init__(
        self,
        server_url: str,
        token_path: str,
        output_file: str,
        template_path: str,
    ) -> None:
        """
        Used to build the Jira configuration file for use in the report command.

        Args:
            server_url (str): Jira server URL, i.e "https://issues.stage.redhat.com"
            token_path (str): Path to the file holding the Jira server API token
            output_file (str): Where the rendered config will be stored.
            template_path (str): Path to Jinja template used to generate Jira credentials. Defaults to /firewatch/cli/templates/jira.config.j2.
        """
        self.logger = get_logger(__name__)

        self.config_file_path = self.render_template(
            server_url=server_url,
            token=self.token(file_path=token_path),
            output_file=output_file,
            template_path=template_path,
        )

    def token(self, file_path: str) -> str:
        """
        Reads the contents of file_path and returns it. The file_path should be the file that holds the Jira API token

        Args:
            file_path (str): The path to the file that holds the Jira API token

        Returns:
            str: A string object that represents the Jira API token
        """
        try:
            with open(file_path) as file:
                return file.read().strip()
        except Exception as ex:
            self.logger.error(
                f"Failed to read Jira token from {file_path}. error: {ex}",
            )
            raise click.Abort()

    def render_template(
        self,
        server_url: str,
        token: str,
        output_file: str,
        template_path: str,
    ) -> str:
        """
        Uses Jinja to render the Jira configuration file

        Args:
            server_url (str): Jira server URL, i.e "https://issues.stage.redhat.com"
            token (str): Jira server API token
            output_file (str): Where the rendered config will be stored.
            template_path (str): Path to Jinja template used to generate Jira credentials. Defaults to /firewatch/cli/templates/jira.config.j2.

        Returns:
            str: A string object that represents the path of the rendered template.
        """

        template_dir = Path(template_path).parent
        template_filename = Path(template_path).name

        # Load Jinja template file
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_filename)

        # Render the template
        context = {"server_url": server_url, "token": token}
        rendered_template = template.render(**context)

        with open(output_file, "w") as file:
            file.write(rendered_template)

        self.logger.info(f"Config file written to {output_file}")

        return output_file
