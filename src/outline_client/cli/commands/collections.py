import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import (
    clear_option,
    clearable,
    pagination_options,
    parse_json,
    permission_option,
    sorting_options,
)
from outline_client.cli.output import render


@click.group(name="collections", cls=CommonClickGroup)
def group() -> None:
    """
    Manage collections, their documents, and who can reach them.
    """


@group.command(name="list")
@click.option("--filters", default=None, help="Filter expression, as JSON.")
@click.option("--query", default=None, help="Match collection names against this text.")
@pagination_options
@sorting_options
@click.pass_obj
def list_(
    ctx: ClientContext,
    filters: str | None,
    query: str | None,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List the collections you can see.
    """
    render(
        ctx.client.list_collections(
            filters=parse_json(filters),
            query=query,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        )
    )


@group.command(name="get")
@click.argument("collection_id")
@click.pass_obj
def get(ctx: ClientContext, collection_id: str) -> None:
    """
    Show one collection.
    """
    render(ctx.client.get_collection(collection_id))


@group.command(name="structure")
@click.argument("collection_id")
@click.pass_obj
def structure(ctx: ClientContext, collection_id: str) -> None:
    """
    Show a collection's document tree.
    """
    render(ctx.client.get_collection_structure(collection_id))


@group.command(name="create")
@click.argument("name")
@click.option("--description", default=None, help="Description, as markdown.")
@permission_option
@click.option("--icon", default=None, help="Icon name from the outline-icons set.")
@click.option("--color", default=None, help="Hex color for the icon.")
@click.option(
    "--sharing/--no-sharing", default=None, help="Allow public document shares."
)
@click.pass_obj
def create(
    ctx: ClientContext,
    name: str,
    description: str | None,
    permission: str | None,
    icon: str | None,
    color: str | None,
    sharing: bool | None,
) -> None:
    """
    Create a collection.
    """
    render(
        ctx.client.create_collection(
            name,
            description=description,
            permission=permission,
            icon=icon,
            color=color,
            sharing=sharing,
        )
    )


@group.command(name="update")
@click.argument("collection_id")
@click.option("--name", default=None, help="New name.")
@click.option("--description", default=None, help="New description, as markdown.")
@permission_option
@click.option("--icon", default=None, help="New icon name.")
@click.option("--color", default=None, help="New hex color.")
@click.option(
    "--sharing/--no-sharing", default=None, help="Allow public document shares."
)
@clear_option("description", "permission", "icon", "color")
@click.pass_obj
def update(
    ctx: ClientContext,
    collection_id: str,
    name: str | None,
    description: str | None,
    permission: str | None,
    icon: str | None,
    color: str | None,
    sharing: bool | None,
    clear: tuple[str, ...],
) -> None:
    """
    Update a collection, leaving the options you omit as they are.

    `--clear permission` makes the collection private to its members.
    """
    render(
        ctx.client.update_collection(
            collection_id,
            name=name,
            description=clearable(description, "description", clear),
            permission=clearable(permission, "permission", clear),
            icon=clearable(icon, "icon", clear),
            color=clearable(color, "color", clear),
            sharing=sharing,
        )
    )


@group.command(name="delete")
@click.argument("collection_id")
@click.confirmation_option(prompt="Delete this collection and every document in it?")
@click.pass_obj
def delete(ctx: ClientContext, collection_id: str) -> None:
    """
    Delete a collection and every document in it.
    """
    render(ctx.client.delete_collection(collection_id))


@group.command(name="duplicate")
@click.argument("collection_id")
@click.option("--name", default=None, help="Name for the copy.")
@click.pass_obj
def duplicate(ctx: ClientContext, collection_id: str, name: str | None) -> None:
    """
    Copy a collection and its documents.
    """
    render(ctx.client.duplicate_collection(collection_id, name=name))


@group.command(name="archive")
@click.argument("collection_id")
@click.pass_obj
def archive(ctx: ClientContext, collection_id: str) -> None:
    """
    Archive a collection.
    """
    render(ctx.client.archive_collection(collection_id))


@group.command(name="restore")
@click.argument("collection_id")
@click.pass_obj
def restore(ctx: ClientContext, collection_id: str) -> None:
    """
    Restore an archived collection.
    """
    render(ctx.client.restore_collection(collection_id))


@group.command(name="move")
@click.argument("collection_id")
@click.argument("index")
@click.pass_obj
def move(ctx: ClientContext, collection_id: str, index: str) -> None:
    """
    Reorder a collection in the sidebar.
    """
    render(ctx.client.move_collection(collection_id, index))


@group.command(name="memberships")
@click.argument("collection_id")
@click.option("--query", default=None, help="Match member names against this text.")
@permission_option
@pagination_options
@click.pass_obj
def memberships(
    ctx: ClientContext,
    collection_id: str,
    query: str | None,
    permission: str | None,
    offset: int | None,
    limit: int | None,
) -> None:
    """
    List the users given access to a collection individually.
    """
    render(
        ctx.client.list_collection_memberships(
            collection_id,
            query=query,
            permission=permission,
            offset=offset,
            limit=limit,
        )
    )


@group.command(name="add-user")
@click.argument("collection_id")
@click.argument("user_id")
@permission_option
@click.pass_obj
def add_user(
    ctx: ClientContext, collection_id: str, user_id: str, permission: str | None
) -> None:
    """
    Give one user access to a collection.
    """
    render(
        ctx.client.add_collection_user(collection_id, user_id, permission=permission)
    )


@group.command(name="remove-user")
@click.argument("collection_id")
@click.argument("user_id")
@click.pass_obj
def remove_user(ctx: ClientContext, collection_id: str, user_id: str) -> None:
    """
    Take away one user's individual access to a collection.
    """
    render(ctx.client.remove_collection_user(collection_id, user_id))


@group.command(name="group-memberships")
@click.argument("collection_id")
@click.option("--query", default=None, help="Match group names against this text.")
@permission_option
@pagination_options
@click.pass_obj
def group_memberships(
    ctx: ClientContext,
    collection_id: str,
    query: str | None,
    permission: str | None,
    offset: int | None,
    limit: int | None,
) -> None:
    """
    List the groups given access to a collection.
    """
    render(
        ctx.client.list_collection_group_memberships(
            collection_id,
            query=query,
            permission=permission,
            offset=offset,
            limit=limit,
        )
    )


@group.command(name="add-group")
@click.argument("collection_id")
@click.argument("group_id")
@permission_option
@click.pass_obj
def add_group(
    ctx: ClientContext, collection_id: str, group_id: str, permission: str | None
) -> None:
    """
    Give a group access to a collection.
    """
    render(
        ctx.client.add_collection_group(collection_id, group_id, permission=permission)
    )


@group.command(name="remove-group")
@click.argument("collection_id")
@click.argument("group_id")
@click.pass_obj
def remove_group(ctx: ClientContext, collection_id: str, group_id: str) -> None:
    """
    Take away a group's access to a collection.
    """
    render(ctx.client.remove_collection_group(collection_id, group_id))


@group.command(name="export")
@click.argument("collection_id")
@click.option(
    "--format",
    type=click.Choice(["outline-markdown", "json", "html"]),
    default=None,
    help="Export format.",
)
@click.pass_obj
def export(ctx: ClientContext, collection_id: str, format: str | None) -> None:
    """
    Start an export of one collection.

    The export runs in the background; follow it with `outline file-operations`.
    """
    render(ctx.client.export_collection(collection_id, format=format))


@group.command(name="export-all")
@click.option(
    "--format",
    type=click.Choice(["outline-markdown", "json", "html"]),
    default=None,
    help="Export format.",
)
@click.option(
    "--attachments/--no-attachments", default=None, help="Include attachments."
)
@click.option(
    "--private/--no-private", default=None, help="Include private collections."
)
@click.pass_obj
def export_all(
    ctx: ClientContext,
    format: str | None,
    attachments: bool | None,
    private: bool | None,
) -> None:
    """
    Start an export of every collection you can see.
    """
    render(
        ctx.client.export_all_collections(
            format=format,
            include_attachments=attachments,
            include_private=private,
        )
    )


@group.command(name="import")
@click.argument("attachment_id")
@click.option(
    "--format",
    type=click.Choice(["outline-markdown", "json"]),
    default=None,
    help="Format of the uploaded file.",
)
@permission_option
@click.pass_obj
def import_(
    ctx: ClientContext,
    attachment_id: str,
    format: str | None,
    permission: str | None,
) -> None:
    """
    Create a collection from a previously uploaded file.
    """
    render(
        ctx.client.import_collection(
            attachment_id, format=format, permission=permission
        )
    )
