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

from cli.jira_config_gen.jira_config_gen import JiraConfig


class TestFirewatchJiraConfigGen:
    logger = logging.getLogger(__name__)

    def test_jira_config_generation(self, tmp_path) -> None:
        # Define required variables
        template = """
        {
            "token": "{{ token }}",
            "url": "{{ server_url }}",
            {% if "stage" in server_url %}
            "proxies": {
                "http": "http://squid.corp.redhat.com:3128",
                "https": "http://squid.corp.redhat.com:3128"
            }
            {% endif %}
        }
        """
        self.logger = logging.getLogger(__name__)
        template_dir = str(tmp_path)
        template_filename = "jira.config.j2"
        output_path = f"{tmp_path}/jira.config"
        token = "some-test-token"
        url = "some-jira-url"

        with open(f"{template_dir}/{template_filename}", "w") as file:
            file.write(str(template))

        config = JiraConfig(
            server_url=url,
            token=token,
            output_file=output_path,
            template_dir=template_dir,
            template_filename=template_filename,
        )

        assert os.path.exists(config.config_file_path)
