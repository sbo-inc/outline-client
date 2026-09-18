from outline_client.operations.generic import Operation, body, many, one, success
from outline_client.schemas.models import Subscription

# -----------------------------------------------------------------------------
# OPERATION: list_subscriptions
# -----------------------------------------------------------------------------


def list_subscriptions(
    event: str,
    *,
    document_id: str | None = None,
    collection_id: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> Operation[list[Subscription]]:
    """
    Build the `subscriptions.list` operation.

    Returns:
        Operation[list[Subscription]]: The list subscriptions operation.
    """
    return Operation(
        path="subscriptions.list",
        payload=body(
            event=event,
            documentId=document_id,
            collectionId=collection_id,
            offset=offset,
            limit=limit,
        ),
        parse=many(Subscription),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_subscription
# -----------------------------------------------------------------------------


def get_subscription(
    event: str,
    *,
    document_id: str | None = None,
    collection_id: str | None = None,
) -> Operation[Subscription]:
    """
    Build the `subscriptions.info` operation.

    Returns:
        Operation[Subscription]: The get subscription operation.
    """
    return Operation(
        path="subscriptions.info",
        payload=body(
            event=event,
            documentId=document_id,
            collectionId=collection_id,
        ),
        parse=one(Subscription),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_subscription
# -----------------------------------------------------------------------------


def create_subscription(
    event: str,
    *,
    document_id: str | None = None,
    collection_id: str | None = None,
) -> Operation[Subscription]:
    """
    Build the `subscriptions.create` operation.

    Returns:
        Operation[Subscription]: The create subscription operation.
    """
    return Operation(
        path="subscriptions.create",
        payload=body(
            event=event,
            documentId=document_id,
            collectionId=collection_id,
        ),
        parse=one(Subscription),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_subscription
# -----------------------------------------------------------------------------


def delete_subscription(id: str) -> Operation[bool]:
    """
    Build the `subscriptions.delete` operation.

    Returns:
        Operation[bool]: The delete subscription operation.
    """
    return Operation(
        path="subscriptions.delete",
        payload=body(id=id),
        parse=success,
    )
