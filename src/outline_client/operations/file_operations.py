from outline_client.operations.generic import Operation, body, many, one, success
from outline_client.schemas.models import (
    FileOperation,
    FileOperationType,
    SortDirection,
)

# -----------------------------------------------------------------------------
# OPERATION: list_file_operations
# -----------------------------------------------------------------------------


def list_file_operations(
    type: FileOperationType | str,
    *,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[FileOperation]]:
    """
    Build the `fileOperations.list` operation.

    Returns:
        Operation[list[FileOperation]]: The list file operations operation.
    """
    return Operation(
        path="fileOperations.list",
        payload=body(
            type=type,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(FileOperation),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_file_operation
# -----------------------------------------------------------------------------


def get_file_operation(id: str) -> Operation[FileOperation]:
    """
    Build the `fileOperations.info` operation.

    Returns:
        Operation[FileOperation]: The get file operation operation.
    """
    return Operation(
        path="fileOperations.info",
        payload=body(id=id),
        parse=one(FileOperation),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_file_operation
# -----------------------------------------------------------------------------


def delete_file_operation(id: str) -> Operation[bool]:
    """
    Build the `fileOperations.delete` operation.

    Returns:
        Operation[bool]: The delete file operation operation.
    """
    return Operation(
        path="fileOperations.delete",
        payload=body(id=id),
        parse=success,
    )
