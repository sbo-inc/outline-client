import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import (
    clear_option,
    clearable,
    pagination_options,
    sorting_options,
)
from outline_client.cli.output import render


@click.group(name="shares", cls=CommonClickGroup)
def group() -> None:
    """
    Manage the links that expose documents outside the workspace.
    """


@group.command(name="list")
@click.option(
    "--query", default=None, help="Match shared document titles against this text."
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
    List the share links you can see.
    """
    render(
        ctx.client.list_shares(
            query=query, offset=offset, limit=limit, sort=sort, direction=direction
        )
    )


@group.command(name="get")
@click.argument("share_id", required=False)
@click.option("--document-id", default=None, help="Find the shares on this document.")
@click.option(
    "--collection-id", default=None, help="Find the shares on this collection."
)
@click.pass_obj
def get(
    ctx: ClientContext,
    share_id: str | None,
    document_id: str | None,
    collection_id: str | None,
) -> None:
    """
    Show a published share by its id, or the shares on a document or collection.
    """
    render(
        ctx.client.get_share(
            share_id, document_id=document_id, collection_id=collection_id
        )
    )


@group.command(name="create")
@click.option("--document-id", default=None, help="Document to share.")
@click.option("--collection-id", default=None, help="Collection to share.")
@click.pass_obj
def create(
    ctx: ClientContext, document_id: str | None, collection_id: str | None
) -> None:
    """
    Create a share link for a document or a collection.

    Shares are created unpublished; publish one with `shares update --publish`.
    """
    render(
        ctx.client.create_share(document_id=document_id, collection_id=collection_id)
    )


@group.command(name="update")
@click.argument("share_id")
@click.option(
    "--publish/--unpublish",
    "published",
    required=True,
    help="Whether the link works without signing in.",
)
@click.option("--title", default=None, help="Title shown on the shared page.")
@click.option("--icon-url", default=None, help="Icon shown on the shared page.")
@clear_option("title", "icon-url")
@click.pass_obj
def update(
    ctx: ClientContext,
    share_id: str,
    published: bool,
    title: str | None,
    icon_url: str | None,
    clear: tuple[str, ...],
) -> None:
    """
    Publish or unpublish a share, and set how it presents itself.
    """
    render(
        ctx.client.update_share(
            share_id,
            published,
            title=clearable(title, "title", clear),
            icon_url=clearable(icon_url, "icon-url", clear),
        )
    )


@group.command(name="revoke")
@click.argument("share_id")
@click.confirmation_option(prompt="Revoke this share link?")
@click.pass_obj
def revoke(ctx: ClientContext, share_id: str) -> None:
    """
    Revoke a share link, so the URL stops working.
    """
    render(ctx.client.revoke_share(share_id))
