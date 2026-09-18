import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import pagination_options, parse_json, sorting_options
from outline_client.cli.output import render
from outline_client.schemas.models import Invite


@click.group(name="users", cls=CommonClickGroup)
def group() -> None:
    """
    List, invite, and administer workspace members.
    """


@group.command(name="list")
@click.option("--query", default=None, help="Match name or email against this text.")
@click.option("--filters", default=None, help="Filter expression, as JSON.")
@click.option(
    "--role",
    type=click.Choice(["admin", "member", "viewer", "guest"]),
    default=None,
    help="Limit to one workspace role.",
)
@pagination_options
@sorting_options
@click.pass_obj
def list_(
    ctx: ClientContext,
    query: str | None,
    filters: str | None,
    role: str | None,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List the users in the workspace.
    """
    render(
        ctx.client.list_users(
            query=query,
            filters=parse_json(filters),
            role=role,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        )
    )


@group.command(name="get")
@click.argument("user_id")
@click.pass_obj
def get(ctx: ClientContext, user_id: str) -> None:
    """
    Show one user.
    """
    render(ctx.client.get_user(user_id))


@group.command(name="invite")
@click.option(
    "--email", required=True, multiple=True, help="Address to invite (repeatable)."
)
@click.option("--name", multiple=True, help="Name for each address, in the same order.")
@click.option(
    "--role",
    type=click.Choice(["admin", "member", "viewer"]),
    default="member",
    show_default=True,
    help="Role to invite under.",
)
@click.option(
    "--suppress-email", is_flag=True, help="Create the accounts without emailing."
)
@click.pass_obj
def invite(
    ctx: ClientContext,
    email: tuple[str, ...],
    name: tuple[str, ...],
    role: str,
    suppress_email: bool,
) -> None:
    """
    Invite people to the workspace by email address.

    Pass --name once per --email to set the invited names; addresses without a
    matching name are invited under the address itself.
    """
    if name and len(name) != len(email):
        raise click.BadParameter("pass one --name per --email, or none at all")

    invites = [
        Invite(name=name[index] if name else address, email=address, role=role)
        for index, address in enumerate(email)
    ]
    render(ctx.client.invite_users(invites, suppress_email=suppress_email or None))


@group.command(name="resend-invite")
@click.argument("user_id")
@click.pass_obj
def resend_invite(ctx: ClientContext, user_id: str) -> None:
    """
    Send a pending invitation again.
    """
    render(ctx.client.resend_invite(user_id))


@group.command(name="update")
@click.option("--name", default=None, help="New display name.")
@click.option("--language", default=None, help="New interface language, e.g. en_US.")
@click.option("--avatar-url", default=None, help="New avatar URL.")
@click.option("--preferences", default=None, help="Preferences to set, as JSON.")
@click.pass_obj
def update(
    ctx: ClientContext,
    name: str | None,
    language: str | None,
    avatar_url: str | None,
    preferences: str | None,
) -> None:
    """
    Update the calling user's own profile.
    """
    render(
        ctx.client.update_user(
            name=name,
            language=language,
            avatar_url=avatar_url,
            preferences=parse_json(preferences),
        )
    )


@group.command(name="update-email")
@click.argument("email")
@click.option(
    "--user-id", default=None, help="The user to change; defaults to yourself."
)
@click.pass_obj
def update_email(ctx: ClientContext, email: str, user_id: str | None) -> None:
    """
    Change a user's email address.
    """
    render(ctx.client.update_user_email(email, id=user_id))


@group.command(name="update-role")
@click.argument("user_id")
@click.argument("role", type=click.Choice(["admin", "member", "viewer", "guest"]))
@click.pass_obj
def update_role(ctx: ClientContext, user_id: str, role: str) -> None:
    """
    Change a user's workspace role.
    """
    render(ctx.client.update_user_role(user_id, role))


@group.command(name="suspend")
@click.argument("user_id")
@click.pass_obj
def suspend(ctx: ClientContext, user_id: str) -> None:
    """
    Suspend a user, revoking their access.
    """
    render(ctx.client.suspend_user(user_id))


@group.command(name="activate")
@click.argument("user_id")
@click.pass_obj
def activate(ctx: ClientContext, user_id: str) -> None:
    """
    Restore a suspended user's access.
    """
    render(ctx.client.activate_user(user_id))


@group.command(name="delete")
@click.argument("user_id")
@click.confirmation_option(prompt="Delete this user and their personal data?")
@click.pass_obj
def delete(ctx: ClientContext, user_id: str) -> None:
    """
    Delete a user and the personal data attached to them.
    """
    render(ctx.client.delete_user(user_id))


@group.command(name="subscribe")
@click.argument("event_type")
@click.pass_obj
def subscribe(ctx: ClientContext, event_type: str) -> None:
    """
    Subscribe yourself to one kind of notification.
    """
    render(ctx.client.subscribe_to_notifications(event_type))


@group.command(name="unsubscribe")
@click.argument("event_type")
@click.pass_obj
def unsubscribe(ctx: ClientContext, event_type: str) -> None:
    """
    Unsubscribe yourself from one kind of notification.
    """
    render(ctx.client.unsubscribe_from_notifications(event_type))


@group.command(name="memberships")
@pagination_options
@click.pass_obj
def memberships(ctx: ClientContext, offset: int | None, limit: int | None) -> None:
    """
    List the documents shared directly with you.
    """
    render(ctx.client.list_user_memberships(offset=offset, limit=limit))


@group.command(name="update-membership")
@click.argument("membership_id")
@click.argument("index")
@click.pass_obj
def update_membership(ctx: ClientContext, membership_id: str, index: str) -> None:
    """
    Reorder one of your shared documents in the sidebar.
    """
    render(ctx.client.update_user_membership(membership_id, index))
