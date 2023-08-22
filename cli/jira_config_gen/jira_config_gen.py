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
import logging
import os

from jinja2 import Environment
from jinja2 import FileSystemLoader


class JiraConfig:
    def __init__(
        self,
        server_url: str,
        token_path: str,
        output_file: str,
        template_dir: str = os.path.join("firewatch", "cli", "templates"),
        template_filename: str = "jira.config.j2",
    ) -> None:
        """
        Used to build the Jira configuration file for use in the report command.

        :param server_url: Jira server URL, i.e "https://issues.stage.redhat.com"
        :param token_path: Path to the file holding the Jira server API token
        :param output_file: Where the rendered config will be stored.
        :param template_dir: Directory where template is stored
        :param template_filename: Filename of Jinja template
        """

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(
            __name__,
        )

        self.config_file_path = self.render_template(
            server_url=server_url,
            token=self.token(file_path=token_path),
            output_file=output_file,
            template_dir=template_dir,
            template_filename=template_filename,
        )

    def token(self, file_path: str) -> str:
        """
        Reads the contents of file_path and returns it. The file_path should be the file that holds the Jira API token

        :param file_path: The path to the file that holds the Jira API token

        :returns: A string object that represents the Jira API token
        """
        try:
            with open(file_path) as file:
                token = file.read().strip()
                return token
        except FileNotFoundError:
            self.logger.error("File not found:", file_path)
        except OSError as e:
            self.logger.error("Error reading file:", e)
        return "token_not_found"

    def render_template(
        self,
        server_url: str,
        token: str,
        output_file: str,
        template_dir: str,
        template_filename: str,
    ) -> str:
        """
        Uses Jinja to render the Jira configuration file

        :param server_url: Jira server URL, i.e "https://issues.stage.redhat.com"
        :param token: Jira server API token
        :param output_file: Where the rendered config will be stored.
        :param template_dir: Directory where template is stored
        :param template_filename: Filename of Jinja template

        :returns: A string object that represents the path of the rendered template.
        """

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
