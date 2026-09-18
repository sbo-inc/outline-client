from outline_client.operations.generic import Operation, body, one, success
from outline_client.schemas.models import Group, SortDirection
from outline_client.schemas.results import GroupMembershipsResult

# -----------------------------------------------------------------------------
# OPERATION: list_groups
# -----------------------------------------------------------------------------


def list_groups(
    *,
    user_id: str | None = None,
    external_id: str | None = None,
    query: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[GroupMembershipsResult]:
    """
    Build the `groups.list` operation.

    Returns:
        Operation[GroupMembershipsResult]: The list groups operation.
    """
    return Operation(
        path="groups.list",
        payload=body(
            userId=user_id,
            externalId=external_id,
            query=query,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=one(GroupMembershipsResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_group
# -----------------------------------------------------------------------------


def get_group(id: str) -> Operation[Group]:
    """
    Build the `groups.info` operation.

    Returns:
        Operation[Group]: The get group operation.
    """
    return Operation(
        path="groups.info",
        payload=body(id=id),
        parse=one(Group),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_group
# -----------------------------------------------------------------------------


def create_group(name: str) -> Operation[Group]:
    """
    Build the `groups.create` operation.

    Returns:
        Operation[Group]: The create group operation.
    """
    return Operation(
        path="groups.create",
        payload=body(name=name),
        parse=one(Group),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_group
# -----------------------------------------------------------------------------


def update_group(id: str, name: str) -> Operation[Group]:
    """
    Build the `groups.update` operation.

    Returns:
        Operation[Group]: The update group operation.
    """
    return Operation(
        path="groups.update",
        payload=body(id=id, name=name),
        parse=one(Group),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_group
# -----------------------------------------------------------------------------


def delete_group(id: str) -> Operation[bool]:
    """
    Build the `groups.delete` operation.

    Returns:
        Operation[bool]: The delete group operation.
    """
    return Operation(
        path="groups.delete",
        payload=body(id=id),
        parse=success,
    )


# -----------------------------------------------------------------------------
# OPERATION: list_group_users
# -----------------------------------------------------------------------------


def list_group_users(
    id: str,
    *,
    query: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> Operation[GroupMembershipsResult]:
    """
    Build the `groups.memberships` operation.

    Returns:
        Operation[GroupMembershipsResult]: The list group users operation.
    """
    return Operation(
        path="groups.memberships",
        payload=body(id=id, query=query, offset=offset, limit=limit),
        parse=one(GroupMembershipsResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: add_group_user
# -----------------------------------------------------------------------------


def add_group_user(id: str, user_id: str) -> Operation[GroupMembershipsResult]:
    """
    Build the `groups.add_user` operation.

    Returns:
        Operation[GroupMembershipsResult]: The add group user operation.
    """
    return Operation(
        path="groups.add_user",
        payload=body(id=id, userId=user_id),
        parse=one(GroupMembershipsResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_group_user
# -----------------------------------------------------------------------------


def update_group_user(
    id: str,
    user_id: str,
    permission: str,
) -> Operation[GroupMembershipsResult]:
    """
    Build the `groups.update_user` operation.

    Returns:
        Operation[GroupMembershipsResult]: The update group user operation.
    """
    return Operation(
        path="groups.update_user",
        payload=body(id=id, userId=user_id, permission=permission),
        parse=one(GroupMembershipsResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: remove_group_user
# -----------------------------------------------------------------------------


def remove_group_user(id: str, user_id: str) -> Operation[GroupMembershipsResult]:
    """
    Build the `groups.remove_user` operation.

    Returns:
        Operation[GroupMembershipsResult]: The remove group user operation.
    """
    return Operation(
        path="groups.remove_user",
        payload=body(id=id, userId=user_id),
        parse=one(GroupMembershipsResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_group_memberships
# -----------------------------------------------------------------------------


def list_group_memberships(
    *,
    group_id: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> Operation[GroupMembershipsResult]:
    """
    Build the `groupMemberships.list` operation.

    Returns:
        Operation[GroupMembershipsResult]: The list group memberships operation.
    """
    return Operation(
        path="groupMemberships.list",
        payload=body(groupId=group_id, offset=offset, limit=limit),
        parse=one(GroupMembershipsResult),
    )
