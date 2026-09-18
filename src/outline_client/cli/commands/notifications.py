import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import pagination_options
from outline_client.cli.output import render


@click.group(name="notifications", cls=CommonClickGroup)
def group() -> None:
    """
    Read and clear your notifications.
    """


@group.command(name="list")
@click.option("--event-type", default=None, help="Limit to one event type.")
@click.option("--archived", is_flag=True, help="Show the archived ones instead.")
@pagination_options
@click.pass_obj
def list_(
    ctx: ClientContext,
    event_type: str | None,
    archived: bool,
    offset: int | None,
    limit: int | None,
) -> None:
    """
    List your notifications.
    """
    render(
        ctx.client.list_notifications(
            event_type=event_type,
            archived=archived or None,
            offset=offset,
            limit=limit,
        )
    )


@group.command(name="update")
@click.argument("notification_id")
@click.option("--viewed-at", default=None, help="Mark read as of this timestamp.")
@click.option("--archived-at", default=None, help="Archive as of this timestamp.")
@click.pass_obj
def update(
    ctx: ClientContext,
    notification_id: str,
    viewed_at: str | None,
    archived_at: str | None,
) -> None:
    """
    Mark one notification read or archived.
    """
    render(
        ctx.client.update_notification(
            notification_id, viewed_at=viewed_at, archived_at=archived_at
        )
    )


@group.command(name="update-all")
@click.option("--viewed-at", default=None, help="Mark all read as of this timestamp.")
@click.option("--archived-at", default=None, help="Archive all as of this timestamp.")
@click.pass_obj
def update_all(
    ctx: ClientContext, viewed_at: str | None, archived_at: str | None
) -> None:
    """
    Mark every notification read or archived.
    """
    render(
        ctx.client.update_all_notifications(
            viewed_at=viewed_at, archived_at=archived_at
        )
    )
