import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import pagination_options, sorting_options
from outline_client.cli.output import render


@click.group(name="revisions", cls=CommonClickGroup)
def group() -> None:
    """
    Browse a document's revision history.
    """


@group.command(name="list")
@click.argument("document_id")
@pagination_options
@sorting_options
@click.pass_obj
def list_(
    ctx: ClientContext,
    document_id: str,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List a document's revision history.
    """
    render(
        ctx.client.list_revisions(
            document_id, offset=offset, limit=limit, sort=sort, direction=direction
        )
    )


@group.command(name="get")
@click.argument("revision_id")
@click.pass_obj
def get(ctx: ClientContext, revision_id: str) -> None:
    """
    Show one revision, including the document text it captured.
    """
    render(ctx.client.get_revision(revision_id))


@group.command(name="update")
@click.argument("revision_id")
@click.argument("name")
@click.pass_obj
def update(ctx: ClientContext, revision_id: str, name: str) -> None:
    """
    Name a revision, so it can be found again in the history.
    """
    render(ctx.client.update_revision(revision_id, name))


@group.command(name="delete")
@click.argument("revision_id")
@click.confirmation_option(prompt="Delete this revision?")
@click.pass_obj
def delete(ctx: ClientContext, revision_id: str) -> None:
    """
    Delete a revision from a document's history.
    """
    render(ctx.client.delete_revision(revision_id))


@group.command(name="export")
@click.argument("revision_id")
@click.pass_obj
def export(ctx: ClientContext, revision_id: str) -> None:
    """
    Start an export of one revision.
    """
    render(ctx.client.export_revision(revision_id))
