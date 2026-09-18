from outline_client.operations.generic import Operation, body, one, success
from outline_client.schemas.models import Star
from outline_client.schemas.results import StarsResult

# -----------------------------------------------------------------------------
# OPERATION: list_stars
# -----------------------------------------------------------------------------


def list_stars(
    *,
    offset: int | None = None,
    limit: int | None = None,
) -> Operation[StarsResult]:
    """
    Build the `stars.list` operation.

    Returns:
        Operation[StarsResult]: The list stars operation.
    """
    return Operation(
        path="stars.list",
        payload=body(offset=offset, limit=limit),
        parse=one(StarsResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_star
# -----------------------------------------------------------------------------


def create_star(
    *,
    document_id: str | None = None,
    collection_id: str | None = None,
    index: str | None = None,
) -> Operation[Star]:
    """
    Build the `stars.create` operation.

    Returns:
        Operation[Star]: The create star operation.
    """
    return Operation(
        path="stars.create",
        payload=body(
            documentId=document_id,
            collectionId=collection_id,
            index=index,
        ),
        parse=one(Star),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_star
# -----------------------------------------------------------------------------


def update_star(id: str, index: str) -> Operation[Star]:
    """
    Build the `stars.update` operation.

    Returns:
        Operation[Star]: The update star operation.
    """
    return Operation(
        path="stars.update",
        payload=body(id=id, index=index),
        parse=one(Star),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_star
# -----------------------------------------------------------------------------


def delete_star(id: str) -> Operation[bool]:
    """
    Build the `stars.delete` operation.

    Returns:
        Operation[bool]: The delete star operation.
    """
    return Operation(
        path="stars.delete",
        payload=body(id=id),
        parse=success,
    )
