import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import pagination_options, parse_json, sorting_options
from outline_client.cli.output import render


@click.group(name="data-attributes", cls=CommonClickGroup)
def group() -> None:
    """
    Define the custom attributes documents can carry a value for.
    """


@group.command(name="list")
@pagination_options
@sorting_options
@click.pass_obj
def list_(
    ctx: ClientContext,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List the workspace's custom document attributes.
    """
    render(
        ctx.client.list_data_attributes(
            offset=offset, limit=limit, sort=sort, direction=direction
        )
    )


@group.command(name="get")
@click.argument("attribute_id")
@click.pass_obj
def get(ctx: ClientContext, attribute_id: str) -> None:
    """
    Show one data attribute.
    """
    render(ctx.client.get_data_attribute(attribute_id))


@group.command(name="create")
@click.argument("name")
@click.argument("data_type", type=click.Choice(["string", "number", "boolean", "list"]))
@click.option("--description", default=None, help="What the attribute records.")
@click.option("--options", default=None, help="Extra configuration, as JSON.")
@click.option("--pinned", is_flag=True, help="Show on documents with no value for it.")
@click.pass_obj
def create(
    ctx: ClientContext,
    name: str,
    data_type: str,
    description: str | None,
    options: str | None,
    pinned: bool,
) -> None:
    """
    Define a custom attribute.

    A `list` attribute takes its permitted values from --options, e.g.
    '{"options": [{"value": "Draft"}, {"value": "Final"}]}'.
    """
    render(
        ctx.client.create_data_attribute(
            name,
            data_type,
            description=description,
            options=parse_json(options),
            pinned=pinned or None,
        )
    )


@group.command(name="update")
@click.argument("attribute_id")
@click.argument("name")
@click.option("--description", default=None, help="New description.")
@click.option("--options", default=None, help="New configuration, as JSON.")
@click.option(
    "--pinned/--unpinned", default=None, help="Show on documents with no value."
)
@click.pass_obj
def update(
    ctx: ClientContext,
    attribute_id: str,
    name: str,
    description: str | None,
    options: str | None,
    pinned: bool | None,
) -> None:
    """
    Update a data attribute.
    """
    render(
        ctx.client.update_data_attribute(
            attribute_id,
            name,
            description=description,
            options=parse_json(options),
            pinned=pinned,
        )
    )


@group.command(name="delete")
@click.argument("attribute_id")
@click.confirmation_option(
    prompt="Delete this attribute and every document's value for it?"
)
@click.pass_obj
def delete(ctx: ClientContext, attribute_id: str) -> None:
    """
    Delete a data attribute and every document's value for it.
    """
    render(ctx.client.delete_data_attribute(attribute_id))
