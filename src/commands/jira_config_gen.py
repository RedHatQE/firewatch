import click
from click import Context

from src.utils.general import render_jira_config, get_jira_token


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
    pdb: bool,
) -> None:
    ctx.obj["PDB"] = pdb

    token = get_jira_token(file_path=token_path)
    render_jira_config(
        server_url=server_url,
        token=token,
        output_file=output_file,
    )
