from typing import Any

from outline_client.operations.generic import Operation, body, many, one, success
from outline_client.schemas.models import (
    Collection,
    CollectionFilterCondition,
    CollectionFilterGroup,
    CollectionStatus,
    NavigationNode,
    Permission,
    SortDirection,
)
from outline_client.schemas.results import (
    CollectionGroupMembershipsResult,
    CollectionIndex,
    FileOperationResult,
    MembershipsResult,
)

# -----------------------------------------------------------------------------
# OPERATION: list_collections
# -----------------------------------------------------------------------------


def list_collections(
    *,
    filters: list[CollectionFilterCondition | CollectionFilterGroup] | None = None,
    query: str | None = None,
    status_filter: list[CollectionStatus | str] | None = None,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[Collection]]:
    """
    Build the `collections.list` operation.

    Returns:
        Operation[list[Collection]]: The list collections operation.
    """
    return Operation(
        path="collections.list",
        payload=body(
            filters=filters,
            query=query,
            statusFilter=status_filter,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(Collection),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_collection
# -----------------------------------------------------------------------------


def get_collection(id: str) -> Operation[Collection]:
    """
    Build the `collections.info` operation.

    Returns:
        Operation[Collection]: The get collection operation.
    """
    return Operation(
        path="collections.info",
        payload=body(id=id),
        parse=one(Collection),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_collection_structure
# -----------------------------------------------------------------------------


def get_collection_structure(id: str) -> Operation[list[NavigationNode]]:
    """
    Build the `collections.documents` operation.

    Returns:
        Operation[list[NavigationNode]]: The get collection structure operation.
    """
    return Operation(
        path="collections.documents",
        payload=body(id=id),
        parse=many(NavigationNode),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_collection
# -----------------------------------------------------------------------------


def create_collection(
    name: str,
    *,
    description: str | None = None,
    data: dict[str, Any] | None = None,
    permission: Permission | str | None = None,
    icon: str | None = None,
    color: str | None = None,
    sharing: bool | None = None,
) -> Operation[Collection]:
    """
    Build the `collections.create` operation.

    Returns:
        Operation[Collection]: The create collection operation.
    """
    return Operation(
        path="collections.create",
        payload=body(
            name=name,
            description=description,
            data=data,
            permission=permission,
            icon=icon,
            color=color,
            sharing=sharing,
        ),
        parse=one(Collection),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_collection
# -----------------------------------------------------------------------------


def update_collection(
    id: str,
    *,
    name: str | None = None,
    description: str | None = None,
    data: dict[str, Any] | None = None,
    permission: Permission | str | None = None,
    icon: str | None = None,
    color: str | None = None,
    sharing: bool | None = None,
) -> Operation[Collection]:
    """
    Build the `collections.update` operation.

    Returns:
        Operation[Collection]: The update collection operation.
    """
    return Operation(
        path="collections.update",
        payload=body(
            id=id,
            name=name,
            description=description,
            data=data,
            permission=permission,
            icon=icon,
            color=color,
            sharing=sharing,
        ),
        parse=one(Collection),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_collection
# -----------------------------------------------------------------------------


def delete_collection(id: str) -> Operation[bool]:
    """
    Build the `collections.delete` operation.

    Returns:
        Operation[bool]: The delete collection operation.
    """
    return Operation(
        path="collections.delete",
        payload=body(id=id),
        parse=success,
    )


# -----------------------------------------------------------------------------
# OPERATION: duplicate_collection
# -----------------------------------------------------------------------------


def duplicate_collection(
    id: str,
    *,
    name: str | None = None,
) -> Operation[Collection]:
    """
    Build the `collections.duplicate` operation.

    Returns:
        Operation[Collection]: The duplicate collection operation.
    """
    return Operation(
        path="collections.duplicate",
        payload=body(id=id, name=name),
        parse=one(Collection),
    )


# -----------------------------------------------------------------------------
# OPERATION: archive_collection
# -----------------------------------------------------------------------------


def archive_collection(id: str) -> Operation[Collection]:
    """
    Build the `collections.archive` operation.

    Returns:
        Operation[Collection]: The archive collection operation.
    """
    return Operation(
        path="collections.archive",
        payload=body(id=id),
        parse=one(Collection),
    )


# -----------------------------------------------------------------------------
# OPERATION: restore_collection
# -----------------------------------------------------------------------------


def restore_collection(id: str) -> Operation[Collection]:
    """
    Build the `collections.restore` operation.

    Returns:
        Operation[Collection]: The restore collection operation.
    """
    return Operation(
        path="collections.restore",
        payload=body(id=id),
        parse=one(Collection),
    )


# -----------------------------------------------------------------------------
# OPERATION: move_collection
# -----------------------------------------------------------------------------


def move_collection(id: str, index: str) -> Operation[CollectionIndex]:
    """
    Build the `collections.move` operation.

    Returns:
        Operation[CollectionIndex]: The move collection operation.
    """
    return Operation(
        path="collections.move",
        payload=body(id=id, index=index),
        parse=one(CollectionIndex),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_collection_memberships
# -----------------------------------------------------------------------------


def list_collection_memberships(
    id: str,
    *,
    query: str | None = None,
    permission: Permission | str | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> Operation[MembershipsResult]:
    """
    Build the `collections.memberships` operation.

    Returns:
        Operation[MembershipsResult]: The list collection memberships operation.
    """
    return Operation(
        path="collections.memberships",
        payload=body(
            id=id,
            query=query,
            permission=permission,
            offset=offset,
            limit=limit,
        ),
        parse=one(MembershipsResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: add_collection_user
# -----------------------------------------------------------------------------


def add_collection_user(
    id: str,
    user_id: str,
    *,
    permission: Permission | str | None = None,
) -> Operation[MembershipsResult]:
    """
    Build the `collections.add_user` operation.

    Returns:
        Operation[MembershipsResult]: The add collection user operation.
    """
    return Operation(
        path="collections.add_user",
        payload=body(id=id, userId=user_id, permission=permission),
        parse=one(MembershipsResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: remove_collection_user
# -----------------------------------------------------------------------------


def remove_collection_user(id: str, user_id: str) -> Operation[bool]:
    """
    Build the `collections.remove_user` operation.

    Returns:
        Operation[bool]: The remove collection user operation.
    """
    return Operation(
        path="collections.remove_user",
        payload=body(id=id, userId=user_id),
        parse=success,
    )


# -----------------------------------------------------------------------------
# OPERATION: list_collection_group_memberships
# -----------------------------------------------------------------------------


def list_collection_group_memberships(
    id: str,
    *,
    query: str | None = None,
    permission: Permission | str | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> Operation[CollectionGroupMembershipsResult]:
    """
    Build the `collections.group_memberships` operation.

    Returns:
        Operation[CollectionGroupMembershipsResult]: The list collection group
            memberships operation.
    """
    return Operation(
        path="collections.group_memberships",
        payload=body(
            id=id,
            query=query,
            permission=permission,
            offset=offset,
            limit=limit,
        ),
        parse=one(CollectionGroupMembershipsResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: add_collection_group
# -----------------------------------------------------------------------------


def add_collection_group(
    id: str,
    group_id: str,
    *,
    permission: Permission | str | None = None,
) -> Operation[CollectionGroupMembershipsResult]:
    """
    Build the `collections.add_group` operation.

    Returns:
        Operation[CollectionGroupMembershipsResult]: The add collection group
            operation.
    """
    return Operation(
        path="collections.add_group",
        payload=body(id=id, groupId=group_id, permission=permission),
        parse=one(CollectionGroupMembershipsResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: remove_collection_group
# -----------------------------------------------------------------------------


def remove_collection_group(id: str, group_id: str) -> Operation[bool]:
    """
    Build the `collections.remove_group` operation.

    Returns:
        Operation[bool]: The remove collection group operation.
    """
    return Operation(
        path="collections.remove_group",
        payload=body(id=id, groupId=group_id),
        parse=success,
    )


# -----------------------------------------------------------------------------
# OPERATION: export_collection
# -----------------------------------------------------------------------------


def export_collection(
    id: str,
    *,
    format: str | None = None,
) -> Operation[FileOperationResult]:
    """
    Build the `collections.export` operation.

    Returns:
        Operation[FileOperationResult]: The export collection operation.
    """
    return Operation(
        path="collections.export",
        payload=body(id=id, format=format),
        parse=one(FileOperationResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: export_all_collections
# -----------------------------------------------------------------------------


def export_all_collections(
    *,
    format: str | None = None,
    include_attachments: bool | None = None,
    include_private: bool | None = None,
) -> Operation[FileOperationResult]:
    """
    Build the `collections.export_all` operation.

    Returns:
        Operation[FileOperationResult]: The export all collections operation.
    """
    return Operation(
        path="collections.export_all",
        payload=body(
            format=format,
            includeAttachments=include_attachments,
            includePrivate=include_private,
        ),
        parse=one(FileOperationResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: import_collection
# -----------------------------------------------------------------------------


def import_collection(
    attachment_id: str,
    *,
    format: str | None = None,
    permission: Permission | str | None = None,
) -> Operation[FileOperationResult]:
    """
    Build the `collections.import` operation.

    Returns:
        Operation[FileOperationResult]: The import collection operation.
    """
    return Operation(
        path="collections.import",
        payload=body(
            attachmentId=attachment_id,
            format=format,
            permission=permission,
        ),
        parse=one(FileOperationResult),
    )
