import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import pagination_options
from outline_client.cli.output import render


@click.group(name="pins", cls=CommonClickGroup)
def group() -> None:
    """
    Manage the documents pinned for everyone in the workspace.
    """


@group.command(name="list")
@click.option("--collection-id", default=None, help="Limit to one collection's pins.")
@pagination_options
@click.pass_obj
def list_(
    ctx: ClientContext,
    collection_id: str | None,
    offset: int | None,
    limit: int | None,
) -> None:
    """
    List the documents pinned to a collection, or to the home screen.
    """
    render(
        ctx.client.list_pins(collection_id=collection_id, offset=offset, limit=limit)
    )


@group.command(name="get")
@click.argument("document_id")
@click.option("--collection-id", default=None, help="Look in one collection's pins.")
@click.pass_obj
def get(ctx: ClientContext, document_id: str, collection_id: str | None) -> None:
    """
    Show the pin for one document.
    """
    render(ctx.client.get_pin(document_id, collection_id=collection_id))


@group.command(name="create")
@click.argument("document_id")
@click.option(
    "--collection-id",
    default=None,
    help="Pin within this collection. Omit to pin to the home screen.",
)
@click.option("--index", default=None, help="Position among the other pins.")
@click.pass_obj
def create(
    ctx: ClientContext,
    document_id: str,
    collection_id: str | None,
    index: str | None,
) -> None:
    """
    Pin a document, for everyone in the workspace.
    """
    render(ctx.client.create_pin(document_id, collection_id=collection_id, index=index))


@group.command(name="update")
@click.argument("pin_id")
@click.argument("index")
@click.pass_obj
def update(ctx: ClientContext, pin_id: str, index: str) -> None:
    """
    Reorder a pin.
    """
    render(ctx.client.update_pin(pin_id, index))


@group.command(name="delete")
@click.argument("pin_id")
@click.pass_obj
def delete(ctx: ClientContext, pin_id: str) -> None:
    """
    Unpin a document.
    """
    render(ctx.client.delete_pin(pin_id))
