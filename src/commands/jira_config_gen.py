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
