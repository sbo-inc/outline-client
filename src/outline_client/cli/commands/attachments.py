import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import pagination_options, sorting_options
from outline_client.cli.output import render, write_bytes


@click.group(name="attachments", cls=CommonClickGroup)
def group() -> None:
    """
    List, fetch, and register the files attached to documents.
    """


@group.command(name="list")
@click.option("--document-id", default=None, help="Limit to one document.")
@click.option("--user-id", default=None, help="Limit to one uploader.")
@pagination_options
@sorting_options
@click.pass_obj
def list_(
    ctx: ClientContext,
    document_id: str | None,
    user_id: str | None,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List the attachments you can see.
    """
    render(
        ctx.client.list_attachments(
            document_id=document_id,
            user_id=user_id,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        )
    )


@group.command(name="create")
@click.argument("name")
@click.argument("content_type")
@click.argument("size", type=int)
@click.option("--document-id", default=None, help="Document to attach it to.")
@click.pass_obj
def create(
    ctx: ClientContext,
    name: str,
    content_type: str,
    size: int,
    document_id: str | None,
) -> None:
    """
    Reserve an attachment and print where to upload it to.

    This creates the record only; the bytes are uploaded separately, to the
    storage host the response names.
    """
    render(
        ctx.client.create_attachment(name, content_type, size, document_id=document_id)
    )


@group.command(name="create-from-url")
@click.argument("url")
@click.option("--document-id", default=None, help="Document to attach it to.")
@click.pass_obj
def create_from_url(ctx: ClientContext, url: str, document_id: str | None) -> None:
    """
    Create an attachment by having Outline fetch a URL itself.
    """
    render(ctx.client.create_attachment_from_url(url, document_id=document_id))


@group.command(name="url")
@click.argument("attachment_id")
@click.pass_obj
def url(ctx: ClientContext, attachment_id: str) -> None:
    """
    Print the URL an attachment's bytes can be fetched from.
    """
    render(ctx.client.get_attachment_url(attachment_id))


@group.command(name="download")
@click.argument("attachment_id")
@click.option(
    "--output", "-o", default=None, help="Write to this path instead of stdout."
)
@click.pass_obj
def download(ctx: ClientContext, attachment_id: str, output: str | None) -> None:
    """
    Download an attachment's contents.
    """
    write_bytes(ctx.client.download_attachment(attachment_id), output)


@group.command(name="delete")
@click.argument("attachment_id")
@click.confirmation_option(prompt="Delete this attachment and the file behind it?")
@click.pass_obj
def delete(ctx: ClientContext, attachment_id: str) -> None:
    """
    Delete an attachment and the file behind it.
    """
    render(ctx.client.delete_attachment(attachment_id))
