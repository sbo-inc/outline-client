import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import (
    clear_option,
    clearable,
    pagination_options,
    parse_json,
    sorting_options,
)
from outline_client.cli.output import render


@click.group(name="templates", cls=CommonClickGroup)
def group() -> None:
    """
    Manage document templates.
    """


@group.command(name="list")
@click.option("--collection-id", default=None, help="Limit to one collection.")
@click.option("--query", default=None, help="Match template titles against this text.")
@click.option(
    "--markdown",
    is_flag=True,
    help="Print the body as markdown, under text, in place of the rich-text data.",
)
@pagination_options
@sorting_options
@click.pass_obj
def list_(
    ctx: ClientContext,
    collection_id: str | None,
    query: str | None,
    markdown: bool,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List the templates you can see.
    """
    render(
        ctx.client.list_templates(
            collection_id=collection_id,
            query=query,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        markdown=markdown,
    )


@group.command(name="get")
@click.argument("template_id")
@click.option(
    "--markdown",
    is_flag=True,
    help="Print the body as markdown, under text, in place of the rich-text data.",
)
@click.pass_obj
def get(ctx: ClientContext, template_id: str, markdown: bool) -> None:
    """
    Show one template.
    """
    render(ctx.client.get_template(template_id), markdown=markdown)


@group.command(name="create")
@click.option("--title", default=None, help="Template title.")
@click.option("--data", default=None, help="Body as a rich-text document, as JSON.")
@click.option("--collection-id", default=None, help="Collection to create it in.")
@click.option("--icon", default=None, help="Icon name or emoji.")
@click.option("--color", default=None, help="Hex color for the icon.")
@click.option("--publish/--draft", default=None, help="Publish the template.")
@click.pass_obj
def create(
    ctx: ClientContext,
    title: str | None,
    data: str | None,
    collection_id: str | None,
    icon: str | None,
    color: str | None,
    publish: bool | None,
) -> None:
    """
    Create a template.

    Omitting --collection-id makes it available across the whole workspace.
    """
    render(
        ctx.client.create_template(
            title=title,
            data=parse_json(data),
            collection_id=collection_id,
            icon=icon,
            color=color,
            publish=publish,
        )
    )


@group.command(name="update")
@click.argument("template_id")
@click.option("--title", default=None, help="New title.")
@click.option("--data", default=None, help="New body, as JSON.")
@click.option("--collection-id", default=None, help="Collection to move it to.")
@click.option("--icon", default=None, help="New icon name or emoji.")
@click.option("--color", default=None, help="New hex color.")
@click.option("--full-width/--no-full-width", default=None, help="Render edge to edge.")
@click.option("--publish/--draft", default=None, help="Publish the template.")
@clear_option("collection-id", "icon", "color")
@click.pass_obj
def update(
    ctx: ClientContext,
    template_id: str,
    title: str | None,
    data: str | None,
    collection_id: str | None,
    icon: str | None,
    color: str | None,
    full_width: bool | None,
    publish: bool | None,
    clear: tuple[str, ...],
) -> None:
    """
    Update a template, leaving the options you omit as they are.

    `--clear collection-id` makes it available across the whole workspace.
    """
    render(
        ctx.client.update_template(
            template_id,
            title=title,
            data=parse_json(data),
            collection_id=clearable(collection_id, "collection-id", clear),
            icon=clearable(icon, "icon", clear),
            color=clearable(color, "color", clear),
            full_width=full_width,
            publish=publish,
        )
    )


@group.command(name="duplicate")
@click.argument("template_id")
@click.option("--title", default=None, help="Title for the copy.")
@click.option("--collection-id", default=None, help="Collection to copy into.")
@click.pass_obj
def duplicate(
    ctx: ClientContext,
    template_id: str,
    title: str | None,
    collection_id: str | None,
) -> None:
    """
    Copy a template.
    """
    render(
        ctx.client.duplicate_template(
            template_id, title=title, collection_id=collection_id
        )
    )


@group.command(name="restore")
@click.argument("template_id")
@click.pass_obj
def restore(ctx: ClientContext, template_id: str) -> None:
    """
    Restore a deleted template.
    """
    render(ctx.client.restore_template(template_id))


@group.command(name="delete")
@click.argument("template_id")
@click.confirmation_option(prompt="Delete this template?")
@click.pass_obj
def delete(ctx: ClientContext, template_id: str) -> None:
    """
    Delete a template.
    """
    render(ctx.client.delete_template(template_id))
