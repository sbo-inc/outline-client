import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import permission_option
from outline_client.cli.output import render


@click.group(name="access-requests", cls=CommonClickGroup)
def group() -> None:
    """
    Handle requests for access to documents.
    """


@group.command(name="get")
@click.argument("request_id", required=False)
@click.option("--document-id", default=None, help="Find the request for this document.")
@click.pass_obj
def get(ctx: ClientContext, request_id: str | None, document_id: str | None) -> None:
    """
    Show an access request, by its own id or by the document it is for.
    """
    render(ctx.client.get_access_request(request_id, document_id=document_id))


@group.command(name="create")
@click.argument("document_id")
@click.pass_obj
def create(ctx: ClientContext, document_id: str) -> None:
    """
    Ask for access to a document you cannot read.
    """
    render(ctx.client.create_access_request(document_id))


@group.command(name="approve")
@click.argument("request_id")
@permission_option
@click.pass_obj
def approve(ctx: ClientContext, request_id: str, permission: str | None) -> None:
    """
    Approve an access request.
    """
    render(ctx.client.approve_access_request(request_id, permission=permission))


@group.command(name="dismiss")
@click.argument("request_id")
@click.pass_obj
def dismiss(ctx: ClientContext, request_id: str) -> None:
    """
    Dismiss an access request without granting it.
    """
    render(ctx.client.dismiss_access_request(request_id))
