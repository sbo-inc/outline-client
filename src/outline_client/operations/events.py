from outline_client.operations.generic import Operation, body, many
from outline_client.schemas.models import Event, SortDirection

# -----------------------------------------------------------------------------
# OPERATION: list_events
# -----------------------------------------------------------------------------


def list_events(
    *,
    name: str | None = None,
    actor_id: str | None = None,
    document_id: str | None = None,
    collection_id: str | None = None,
    audit_log: bool | None = None,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[Event]]:
    """
    Build the `events.list` operation.

    Returns:
        Operation[list[Event]]: The list events operation.
    """
    return Operation(
        path="events.list",
        payload=body(
            name=name,
            actorId=actor_id,
            documentId=document_id,
            collectionId=collection_id,
            auditLog=audit_log,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(Event),
    )
