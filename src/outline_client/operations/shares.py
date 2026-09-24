from outline_client.not_given import NOT_GIVEN, NotGiven
from outline_client.operations.generic import (
    Operation,
    body,
    many,
    nullable,
    one,
    success,
)
from outline_client.schemas.models import Share, SortDirection

# -----------------------------------------------------------------------------
# OPERATION: list_shares
# -----------------------------------------------------------------------------


def list_shares(
    *,
    query: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[Share]]:
    """
    Build the `shares.list` operation.

    Returns:
        Operation[list[Share]]: The list shares operation.
    """
    return Operation(
        path="shares.list",
        payload=body(
            query=query,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(Share),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_share
# -----------------------------------------------------------------------------


def get_share(
    id: str | None = None,
    *,
    document_id: str | None = None,
) -> Operation[Share]:
    """
    Build the `shares.info` operation.

    Returns:
        Operation[Share]: The get share operation.
    """
    return Operation(
        path="shares.info",
        payload=body(id=id, documentId=document_id),
        parse=one(Share),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_share
# -----------------------------------------------------------------------------


def create_share(
    *,
    document_id: str | None = None,
    collection_id: str | None = None,
) -> Operation[Share]:
    """
    Build the `shares.create` operation.

    Returns:
        Operation[Share]: The create share operation.
    """
    return Operation(
        path="shares.create",
        payload=body(documentId=document_id, collectionId=collection_id),
        parse=one(Share),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_share
# -----------------------------------------------------------------------------


def update_share(
    id: str,
    published: bool,
    *,
    title: str | None | NotGiven = NOT_GIVEN,
    icon_url: str | None | NotGiven = NOT_GIVEN,
) -> Operation[Share]:
    """
    Build the `shares.update` operation.

    Returns:
        Operation[Share]: The update share operation.
    """
    return Operation(
        path="shares.update",
        payload=body(id=id, published=published)
        | nullable(title=title, iconUrl=icon_url),
        parse=one(Share),
    )


# -----------------------------------------------------------------------------
# OPERATION: revoke_share
# -----------------------------------------------------------------------------


def revoke_share(id: str) -> Operation[bool]:
    """
    Build the `shares.revoke` operation.

    Returns:
        Operation[bool]: The revoke share operation.
    """
    return Operation(
        path="shares.revoke",
        payload=body(id=id),
        parse=success,
    )
