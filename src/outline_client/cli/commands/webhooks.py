import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import pagination_options, sorting_options
from outline_client.cli.output import render


@click.group(name="webhooks", cls=CommonClickGroup)
def group() -> None:
    """
    Manage the URLs that receive workspace events.
    """


@group.command(name="list")
@click.option(
    "--query", default=None, help="Match subscription names against this text."
)
@pagination_options
@sorting_options
@click.pass_obj
def list_(
    ctx: ClientContext,
    query: str | None,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List the workspace's webhook subscriptions.
    """
    render(
        ctx.client.list_webhook_subscriptions(
            query=query, offset=offset, limit=limit, sort=sort, direction=direction
        )
    )


@group.command(name="create")
@click.argument("name")
@click.argument("url")
@click.option(
    "--event",
    required=True,
    multiple=True,
    help="Event to deliver (repeatable). Use '*' for everything.",
)
@click.option("--secret", default=None, help="Signing secret for the deliveries.")
@click.pass_obj
def create(
    ctx: ClientContext,
    name: str,
    url: str,
    event: tuple[str, ...],
    secret: str | None,
) -> None:
    """
    Subscribe a URL to workspace events.
    """
    render(
        ctx.client.create_webhook_subscription(name, url, list(event), secret=secret)
    )


@group.command(name="update")
@click.argument("subscription_id")
@click.argument("name")
@click.argument("url")
@click.option(
    "--event", required=True, multiple=True, help="Event to deliver (repeatable)."
)
@click.option("--secret", default=None, help="Signing secret for the deliveries.")
@click.pass_obj
def update(
    ctx: ClientContext,
    subscription_id: str,
    name: str,
    url: str,
    event: tuple[str, ...],
    secret: str | None,
) -> None:
    """
    Update a webhook subscription.

    Outline requires the full set of fields, so this replaces the subscription
    rather than patching it.
    """
    render(
        ctx.client.update_webhook_subscription(
            subscription_id, name, url, list(event), secret=secret
        )
    )


@group.command(name="delete")
@click.argument("subscription_id")
@click.confirmation_option(prompt="Delete this webhook subscription?")
@click.pass_obj
def delete(ctx: ClientContext, subscription_id: str) -> None:
    """
    Delete a webhook subscription.
    """
    render(ctx.client.delete_webhook_subscription(subscription_id))
