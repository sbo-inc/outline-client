from outline_client.operations.generic import Operation, body, many
from outline_client.schemas.models import Reaction

# -----------------------------------------------------------------------------
# OPERATION: list_reactions
# -----------------------------------------------------------------------------


def list_reactions(
    comment_id: str,
    *,
    offset: int | None = None,
    limit: int | None = None,
) -> Operation[list[Reaction]]:
    """
    Build the `reactions.list` operation.

    Returns:
        Operation[list[Reaction]]: The list reactions operation.
    """
    return Operation(
        path="reactions.list",
        payload=body(commentId=comment_id, offset=offset, limit=limit),
        parse=many(Reaction),
    )
