import logging
import sys

import click
import httpx

from outline_client.cli.commands import (
    access_requests,
    api_keys,
    attachments,
    auth,
    collections,
    comments,
    data_attributes,
    documents,
    events,
    file_operations,
    groups,
    notifications,
    oauth,
    pins,
    revisions,
    shares,
    stars,
    subscriptions,
    templates,
    users,
    webhooks,
)
from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.errors import OutlineError

CLI_DOCS = """
Outline knowledge base command-line interface.

Connection settings are read from environment variables:

\b
- OUTLINE_API_URL to define the API endpoint. A workspace URL is accepted and
  has /api appended. Defaults to the cloud host.
- OUTLINE_API_TOKEN for authentication. Create one under Settings => API & Apps.
- OUTLINE_API_HEADERS as a JSON object of extra request headers.
- OUTLINE_API_TIMEOUT as a per-request timeout in seconds.
- OUTLINE_API_RETRIES as a connection-retry count.

Results are printed as indented JSON, so they pipe into jq unchanged.
"""


@click.group(
    cls=CommonClickGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    help=CLI_DOCS,
)
@click.option(
    "--log",
    is_flag=True,
    default=False,
    help="Enable request logging at INFO level.",
)
@click.version_option(package_name="outline-client", prog_name="outline")
@click.pass_context
def cli(ctx: click.Context, log: bool) -> None:
    ctx.obj = ClientContext(log=log)


# Registration order is help order; OUTLINE_CLI_DISABLE gates at runtime.
for module in (
    auth,
    documents,
    collections,
    templates,
    comments,
    revisions,
    shares,
    stars,
    pins,
    users,
    groups,
    subscriptions,
    notifications,
    attachments,
    file_operations,
    data_attributes,
    access_requests,
    api_keys,
    oauth,
    webhooks,
    events,
):
    cli.add_command(module.group)


def main() -> None:
    """
    Console-script entry point.

    Translates expected errors into a non-zero exit with a readable message
    instead of a traceback; the API's own message is the useful half of a
    failure, and a stack trace through httpx is not.
    """
    try:
        cli(standalone_mode=False)
    except click.ClickException as exc:
        exc.show()
        sys.exit(exc.exit_code)
    except click.exceptions.Abort:
        sys.exit(1)
    except OutlineError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except httpx.HTTPError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        logging.getLogger("outline_client").debug("CLI error", exc_info=True)
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


__all__ = ["cli", "main"]
