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
"""Module building jira-config-gen cli command"""

import click
from click import Context

from src.jira_config_gen.jira_config_gen import JiraConfig


@click.option(
    "--server-url",
    help='Jira server URL, i.e "https://issues.stage.redhat.com"',
    required=True,
    type=click.STRING,
)
@click.option(
    "--token-path",
    help="Path to the Jira API token",
    required=True,
    type=click.Path(exists=True),
)
@click.option(
    "--output-file",
    help="Where the rendered config will be stored",
    default="/tmp/jira.config",
    type=click.Path(),
)
@click.option(
    "--template-path",
    help="Directory holding templates",
    default="/firewatch/src/templates/jira.config.j2",
    type=click.Path(exists=True),
)
@click.option(
    "--pdb",
    help="Drop to `ipdb` shell on exception",
    is_flag=True,
)
@click.command("jira-config-gen")
@click.pass_context
def jira_config_gen(
    ctx: Context,
    server_url: str,
    token_path: str,
    output_file: str,
    template_path: str,
    pdb: bool,
) -> None:
    ctx.obj["PDB"] = pdb

    JiraConfig(
        server_url=server_url,
        token_path=token_path,
        output_file=output_file,
        template_path=template_path,
    )
