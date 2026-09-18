import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import pagination_options, sorting_options
from outline_client.cli.output import render, write_bytes


@click.group(name="file-operations", cls=CommonClickGroup)
def group() -> None:
    """
    Follow the workspace's imports and exports, and fetch what they produced.
    """


@group.command(name="list")
@click.argument("type", type=click.Choice(["import", "export"]))
@pagination_options
@sorting_options
@click.pass_obj
def list_(
    ctx: ClientContext,
    type: str,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List the workspace's imports or exports.
    """
    render(
        ctx.client.list_file_operations(
            type, offset=offset, limit=limit, sort=sort, direction=direction
        )
    )


@group.command(name="get")
@click.argument("file_operation_id")
@click.pass_obj
def get(ctx: ClientContext, file_operation_id: str) -> None:
    """
    Show one file operation, to check how far it has got.
    """
    render(ctx.client.get_file_operation(file_operation_id))


@group.command(name="download")
@click.argument("file_operation_id")
@click.option(
    "--output", "-o", default=None, help="Write to this path instead of stdout."
)
@click.pass_obj
def download(ctx: ClientContext, file_operation_id: str, output: str | None) -> None:
    """
    Download the archive a completed export produced.
    """
    write_bytes(ctx.client.download_file_operation(file_operation_id), output)


@group.command(name="delete")
@click.argument("file_operation_id")
@click.confirmation_option(
    prompt="Delete this file operation and the file it produced?"
)
@click.pass_obj
def delete(ctx: ClientContext, file_operation_id: str) -> None:
    """
    Delete a file operation and the file it produced.
    """
    render(ctx.client.delete_file_operation(file_operation_id))
