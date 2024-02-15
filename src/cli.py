import sys

import click
from click import Context
from simple_logger.logger import get_logger

from src.commands.jira_config_gen import jira_config_gen
from src.commands.report import report


@click.group()
@click.option(
    "--pdb",
    help="Drop to `ipdb` shell on exception",
    is_flag=True,
)
@click.pass_context
def main(ctx: Context, pdb: bool) -> None:
    """React to OpenShift CI failures."""
    ctx.ensure_object(dict)
    ctx.obj["PDB"] = pdb


main.add_command(report)
main.add_command(jira_config_gen)

if __name__ == "__main__":
    should_raise = False
    ctx = main.make_context("cli", sys.argv[1:]) or None
    _logger = get_logger(name="main-firewatch")
    try:
        main.invoke(ctx)  # type: ignore
    except Exception as ex:
        import traceback

        ipdb = __import__("ipdb")  # Bypass debug-statements pre-commit hook

        if ctx and ctx.obj is not None and ctx.obj["PDB"]:
            extype, value, tb = sys.exc_info()
            traceback.print_exc()
            ipdb.post_mortem(tb)
        else:
            _logger.error(ex)
            should_raise = True
    finally:
        if should_raise:
            sys.exit(1)
