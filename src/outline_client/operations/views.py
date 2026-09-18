from outline_client.operations.generic import Operation, body, many
from outline_client.schemas.models import View

# -----------------------------------------------------------------------------
# OPERATION: list_views
# -----------------------------------------------------------------------------


def list_views(
    document_id: str,
    *,
    include_suspended: bool | None = None,
) -> Operation[list[View]]:
    """
    Build the `views.list` operation.

    Returns:
        Operation[list[View]]: The list views operation.
    """
    return Operation(
        path="views.list",
        payload=body(documentId=document_id, includeSuspended=include_suspended),
        parse=many(View),
    )
