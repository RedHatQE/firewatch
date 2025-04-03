import click
from click import Context

# from src.jira_automation.jira_automation import JiraAutomation
# from src.objects.configuration import Configuration
from src.objects.jira_base import Jira

# from src.commands.jira_status_updates import jira_status_updates
from src.escalation.jira_escalation import Jira_Escalation
from src.objects.slack_base import SlackClient


@click.option(
    "--jira-config-path",
    help="The path to the jira configuration file",
    default="/tmp/jira.config",
    type=click.Path(exists=True),
)
@click.option(
    "--pdb",
    help="Drop to `ipdb` shell on exception",
    is_flag=True,
)
@click.option(
    "--slack-bot-token",
    help="Slack bot token for slack api",
    required=False,
)
@click.option(
    "--slack-channel",
    help="Slack channel name to send notifications",
    required=True,
)
@click.option(
    "--default-labels",
    help="List of default labels for filtering jira issues",
    required=True,
    multiple=True,
)
@click.option(
    "--additional-labels",
    help="List of additional labels for additional filtering jira issues",
    required=True,
    multiple=True,
)
@click.option(
    "--default-jira-project",
    help="Name of default jira project",
    required=True,
)
@click.command("jira-escalation")
@click.pass_context
def jira_escalation(
    ctx: Context,
    jira_config_path: str,
    pdb: bool,
    slack_bot_token: str,
    slack_channel: str,
    default_labels: list[str],
    additional_labels: list[str],
    default_jira_project: str,
) -> None:
    """Manages jira escalation"""
    ctx.obj["PDB"] = pdb

    # Build Objects
    jira_connection = Jira(jira_config_path=jira_config_path)
    slack_client = SlackClient(slack_bot_token)

    Jira_Escalation(
        jira=jira_connection,
        slack_client=slack_client,
        slack_channel=slack_channel,
        default_labels=default_labels,
        additional_labels=additional_labels,
        default_jira_project=default_jira_project,
    )
