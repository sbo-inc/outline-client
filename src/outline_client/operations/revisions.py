from outline_client.operations.generic import Operation, body, many, one, success
from outline_client.schemas.models import Revision, RevisionDetail, SortDirection
from outline_client.schemas.results import FileOperationResult

# -----------------------------------------------------------------------------
# OPERATION: list_revisions
# -----------------------------------------------------------------------------


def list_revisions(
    document_id: str,
    *,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[Revision]]:
    """
    Build the `revisions.list` operation.

    Returns:
        Operation[list[Revision]]: The list revisions operation.
    """
    return Operation(
        path="revisions.list",
        payload=body(
            documentId=document_id,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(Revision),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_revision
# -----------------------------------------------------------------------------


def get_revision(id: str) -> Operation[RevisionDetail]:
    """
    Build the `revisions.info` operation.

    Returns:
        Operation[RevisionDetail]: The get revision operation.
    """
    return Operation(
        path="revisions.info",
        payload=body(id=id),
        parse=one(RevisionDetail),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_revision
# -----------------------------------------------------------------------------


def update_revision(id: str, name: str) -> Operation[Revision]:
    """
    Build the `revisions.update` operation.

    Returns:
        Operation[Revision]: The update revision operation.
    """
    return Operation(
        path="revisions.update",
        payload=body(id=id, name=name),
        parse=one(Revision),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_revision
# -----------------------------------------------------------------------------


def delete_revision(id: str) -> Operation[bool]:
    """
    Build the `revisions.delete` operation.

    Returns:
        Operation[bool]: The delete revision operation.
    """
    return Operation(
        path="revisions.delete",
        payload=body(id=id),
        parse=success,
    )


# -----------------------------------------------------------------------------
# OPERATION: export_revision
# -----------------------------------------------------------------------------


def export_revision(id: str) -> Operation[FileOperationResult]:
    """
    Build the `revisions.export` operation.

    Returns:
        Operation[FileOperationResult]: The export revision operation.
    """
    return Operation(
        path="revisions.export",
        payload=body(id=id),
        parse=one(FileOperationResult),
    )
