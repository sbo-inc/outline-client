import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import pagination_options, sorting_options
from outline_client.cli.output import render


@click.group(name="groups", cls=CommonClickGroup)
def group() -> None:
    """
    Manage groups and their members.
    """


@group.command(name="list")
@click.option(
    "--user-id", default=None, help="Limit to the groups this user belongs to."
)
@click.option(
    "--external-id", default=None, help="Match the group linked to this directory id."
)
@click.option("--query", default=None, help="Match group names against this text.")
@pagination_options
@sorting_options
@click.pass_obj
def list_(
    ctx: ClientContext,
    user_id: str | None,
    external_id: str | None,
    query: str | None,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List the groups in the workspace.
    """
    render(
        ctx.client.list_groups(
            user_id=user_id,
            external_id=external_id,
            query=query,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        )
    )


@group.command(name="get")
@click.argument("group_id")
@click.pass_obj
def get(ctx: ClientContext, group_id: str) -> None:
    """
    Show one group.
    """
    render(ctx.client.get_group(group_id))


@group.command(name="create")
@click.argument("name")
@click.pass_obj
def create(ctx: ClientContext, name: str) -> None:
    """
    Create a group.
    """
    render(ctx.client.create_group(name))


@group.command(name="update")
@click.argument("group_id")
@click.argument("name")
@click.pass_obj
def update(ctx: ClientContext, group_id: str, name: str) -> None:
    """
    Rename a group.
    """
    render(ctx.client.update_group(group_id, name))


@group.command(name="delete")
@click.argument("group_id")
@click.confirmation_option(prompt="Delete this group and the access it grants?")
@click.pass_obj
def delete(ctx: ClientContext, group_id: str) -> None:
    """
    Delete a group.
    """
    render(ctx.client.delete_group(group_id))


@group.command(name="members")
@click.argument("group_id")
@click.option("--query", default=None, help="Match member names against this text.")
@pagination_options
@click.pass_obj
def members(
    ctx: ClientContext,
    group_id: str,
    query: str | None,
    offset: int | None,
    limit: int | None,
) -> None:
    """
    List the members of one group.
    """
    render(
        ctx.client.list_group_users(group_id, query=query, offset=offset, limit=limit)
    )


@group.command(name="add-user")
@click.argument("group_id")
@click.argument("user_id")
@click.pass_obj
def add_user(ctx: ClientContext, group_id: str, user_id: str) -> None:
    """
    Add a user to a group.
    """
    render(ctx.client.add_group_user(group_id, user_id))


@group.command(name="update-user")
@click.argument("group_id")
@click.argument("user_id")
@click.argument("permission", type=click.Choice(["member", "admin"]))
@click.pass_obj
def update_user(
    ctx: ClientContext, group_id: str, user_id: str, permission: str
) -> None:
    """
    Change a user's role within a group.
    """
    render(ctx.client.update_group_user(group_id, user_id, permission))


@group.command(name="remove-user")
@click.argument("group_id")
@click.argument("user_id")
@click.pass_obj
def remove_user(ctx: ClientContext, group_id: str, user_id: str) -> None:
    """
    Remove a user from a group.
    """
    render(ctx.client.remove_group_user(group_id, user_id))


@group.command(name="memberships")
@click.option("--group-id", default=None, help="Limit to one group's memberships.")
@pagination_options
@click.pass_obj
def memberships(
    ctx: ClientContext,
    group_id: str | None,
    offset: int | None,
    limit: int | None,
) -> None:
    """
    List the documents shared with groups you belong to.
    """
    render(
        ctx.client.list_group_memberships(group_id=group_id, offset=offset, limit=limit)
    )
