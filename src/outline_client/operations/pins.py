from outline_client.operations.generic import Operation, body, nested, one, success
from outline_client.schemas.models import Pin

# -----------------------------------------------------------------------------
# OPERATION: list_pins
# -----------------------------------------------------------------------------


def list_pins(
    *,
    collection_id: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> Operation[list[Pin]]:
    """
    Build the `pins.list` operation.

    Returns:
        Operation[list[Pin]]: The list pins operation.
    """
    return Operation(
        path="pins.list",
        payload=body(collectionId=collection_id, offset=offset, limit=limit),
        parse=nested("pins", Pin),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_pin
# -----------------------------------------------------------------------------


def get_pin(
    document_id: str,
    *,
    collection_id: str | None = None,
) -> Operation[Pin]:
    """
    Build the `pins.info` operation.

    Returns:
        Operation[Pin]: The get pin operation.
    """
    return Operation(
        path="pins.info",
        payload=body(documentId=document_id, collectionId=collection_id),
        parse=one(Pin),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_pin
# -----------------------------------------------------------------------------


def create_pin(
    document_id: str,
    *,
    collection_id: str | None = None,
    index: str | None = None,
) -> Operation[Pin]:
    """
    Build the `pins.create` operation.

    Returns:
        Operation[Pin]: The create pin operation.
    """
    return Operation(
        path="pins.create",
        payload=body(
            documentId=document_id,
            collectionId=collection_id,
            index=index,
        ),
        parse=one(Pin),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_pin
# -----------------------------------------------------------------------------


def update_pin(id: str, index: str) -> Operation[Pin]:
    """
    Build the `pins.update` operation.

    Returns:
        Operation[Pin]: The update pin operation.
    """
    return Operation(
        path="pins.update",
        payload=body(id=id, index=index),
        parse=one(Pin),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_pin
# -----------------------------------------------------------------------------


def delete_pin(id: str) -> Operation[bool]:
    """
    Build the `pins.delete` operation.

    Returns:
        Operation[bool]: The delete pin operation.
    """
    return Operation(
        path="pins.delete",
        payload=body(id=id),
        parse=success,
    )
