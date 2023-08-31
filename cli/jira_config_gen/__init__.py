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
"""Module building jira_config_gen cli command"""
import click

from cli.jira_config_gen.jira_config_gen import JiraConfig


@click.option(
    "--server_url",
    help='Jira server URL, i.e "https://issues.stage.redhat.com"',
    required=True,
    type=click.STRING,
)
@click.option(
    "--token_path",
    help="Path to the Jira API token",
    required=True,
    type=click.STRING,
)
@click.option(
    "--output_file",
    help="Where the rendered config will be stored",
    default="/tmp/jira.config",
    type=click.STRING,
)
@click.option(
    "--template_path",
    help="Directory holding templates",
    default="/firewatch/cli/templates/jira.config.j2",
    type=click.STRING,
)
@click.command("jira_config_gen")
@click.pass_context
def jira_config_gen(
    ctx: click.Context,
    server_url: str,
    token_path: str,
    output_file: str,
    template_path: str,
) -> None:
    config = JiraConfig(
        server_url=server_url,
        token_path=token_path,
        output_file=output_file,
        template_path=template_path,
    )
