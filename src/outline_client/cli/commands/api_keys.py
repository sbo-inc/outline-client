import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import pagination_options, sorting_options
from outline_client.cli.output import render


@click.group(name="api-keys", cls=CommonClickGroup)
def group() -> None:
    """
    Manage the API keys the workspace has issued.
    """


@group.command(name="list")
@click.option("--user-id", default=None, help="Limit to one user's keys.")
@click.option("--query", default=None, help="Match key names against this text.")
@pagination_options
@sorting_options
@click.pass_obj
def list_(
    ctx: ClientContext,
    user_id: str | None,
    query: str | None,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List the API keys you can see.
    """
    render(
        ctx.client.list_api_keys(
            user_id=user_id,
            query=query,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        )
    )


@group.command(name="create")
@click.argument("name")
@click.option(
    "--expires-at", default=None, help="When the key stops working (ISO 8601)."
)
@click.option("--scope", multiple=True, help="What the key may reach (repeatable).")
@click.pass_obj
def create(
    ctx: ClientContext, name: str, expires_at: str | None, scope: tuple[str, ...]
) -> None:
    """
    Create an API key.

    This is the only time the key's value is shown, so capture it now.
    """
    render(
        ctx.client.create_api_key(
            name, expires_at=expires_at, scope=list(scope) or None
        )
    )


@group.command(name="delete")
@click.argument("key_id")
@click.confirmation_option(prompt="Revoke this API key?")
@click.pass_obj
def delete(ctx: ClientContext, key_id: str) -> None:
    """
    Revoke an API key.
    """
    render(ctx.client.delete_api_key(key_id))
