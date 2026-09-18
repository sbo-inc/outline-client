import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import pagination_options
from outline_client.cli.output import render


@click.group(name="subscriptions", cls=CommonClickGroup)
def group() -> None:
    """
    Follow and unfollow documents and collections.
    """


@group.command(name="list")
@click.argument("event")
@click.option("--document-id", default=None, help="Limit to one document.")
@click.option("--collection-id", default=None, help="Limit to one collection.")
@pagination_options
@click.pass_obj
def list_(
    ctx: ClientContext,
    event: str,
    document_id: str | None,
    collection_id: str | None,
    offset: int | None,
    limit: int | None,
) -> None:
    """
    List your subscriptions to an event, e.g. documents.update.
    """
    render(
        ctx.client.list_subscriptions(
            event,
            document_id=document_id,
            collection_id=collection_id,
            offset=offset,
            limit=limit,
        )
    )


@group.command(name="get")
@click.argument("event")
@click.option("--document-id", default=None, help="The document to check.")
@click.option("--collection-id", default=None, help="The collection to check.")
@click.pass_obj
def get(
    ctx: ClientContext,
    event: str,
    document_id: str | None,
    collection_id: str | None,
) -> None:
    """
    Show your subscription to one document or collection.
    """
    render(
        ctx.client.get_subscription(
            event, document_id=document_id, collection_id=collection_id
        )
    )


@group.command(name="create")
@click.argument("event")
@click.option("--document-id", default=None, help="The document to follow.")
@click.option("--collection-id", default=None, help="The collection to follow.")
@click.pass_obj
def create(
    ctx: ClientContext,
    event: str,
    document_id: str | None,
    collection_id: str | None,
) -> None:
    """
    Subscribe to changes on a document or collection.
    """
    render(
        ctx.client.create_subscription(
            event, document_id=document_id, collection_id=collection_id
        )
    )


@group.command(name="delete")
@click.argument("subscription_id")
@click.pass_obj
def delete(ctx: ClientContext, subscription_id: str) -> None:
    """
    Unsubscribe from a document or collection.
    """
    render(ctx.client.delete_subscription(subscription_id))
