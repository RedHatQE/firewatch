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

from jinja2 import Environment
from jinja2 import FileSystemLoader


class JiraConfig:
    def __init__(self, server_url: str, token: str, output_file: str) -> None:
        """
        Used to build the Jira configuration file for use in the report command.

        :param server_url: Jira server URL, i.e "https://issues.stage.redhat.com"
        :param token: Jira server API token
        :param output_file: Where the rendered config will be stored.
        """

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(
            __name__,
        )

        self.config_file_path = self.render_template(
            server_url=server_url,
            token=token,
            output_file=output_file,
        )

    def render_template(self, server_url: str, token: str, output_file: str) -> str:
        """
        Uses Jinja to render the Jira configuration file

        :param server_url: Jira server URL, i.e "https://issues.stage.redhat.com"
        :param token: Jira server API token
        :param output_file: Where the rendered config will be stored.

        :returns: A string object that represents the path of the rendered template.
        """
        template_dir = "/templates"
        template_filename = "jira.config.j2"

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
