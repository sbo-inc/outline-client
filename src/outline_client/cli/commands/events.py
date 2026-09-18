import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import pagination_options, sorting_options
from outline_client.cli.output import render


@click.group(name="events", cls=CommonClickGroup)
def group() -> None:
    """
    Read what has happened in the workspace.
    """


@group.command(name="list")
@click.option(
    "--name", default=None, help="Limit to one event name, e.g. documents.update."
)
@click.option("--actor-id", default=None, help="Limit to events caused by one user.")
@click.option("--document-id", default=None, help="Limit to events about one document.")
@click.option(
    "--collection-id", default=None, help="Limit to events about one collection."
)
@click.option(
    "--audit-log", is_flag=True, help="Include administrative events; admin only."
)
@pagination_options
@sorting_options
@click.pass_obj
def list_(
    ctx: ClientContext,
    name: str | None,
    actor_id: str | None,
    document_id: str | None,
    collection_id: str | None,
    audit_log: bool,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List what has happened in the workspace.
    """
    render(
        ctx.client.list_events(
            name=name,
            actor_id=actor_id,
            document_id=document_id,
            collection_id=collection_id,
            audit_log=audit_log or None,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        )
    )
