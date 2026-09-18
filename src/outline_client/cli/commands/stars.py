import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import pagination_options
from outline_client.cli.output import render


@click.group(name="stars", cls=CommonClickGroup)
def group() -> None:
    """
    Manage your starred documents and collections.
    """


@group.command(name="list")
@pagination_options
@click.pass_obj
def list_(ctx: ClientContext, offset: int | None, limit: int | None) -> None:
    """
    List your starred documents and collections.
    """
    render(ctx.client.list_stars(offset=offset, limit=limit))


@group.command(name="create")
@click.option("--document-id", default=None, help="Document to star.")
@click.option("--collection-id", default=None, help="Collection to star.")
@click.option("--index", default=None, help="Position in the sidebar.")
@click.pass_obj
def create(
    ctx: ClientContext,
    document_id: str | None,
    collection_id: str | None,
    index: str | None,
) -> None:
    """
    Star a document or a collection.
    """
    render(
        ctx.client.create_star(
            document_id=document_id, collection_id=collection_id, index=index
        )
    )


@group.command(name="update")
@click.argument("star_id")
@click.argument("index")
@click.pass_obj
def update(ctx: ClientContext, star_id: str, index: str) -> None:
    """
    Reorder a star in the sidebar.
    """
    render(ctx.client.update_star(star_id, index))


@group.command(name="delete")
@click.argument("star_id")
@click.pass_obj
def delete(ctx: ClientContext, star_id: str) -> None:
    """
    Remove a star.
    """
    render(ctx.client.delete_star(star_id))
