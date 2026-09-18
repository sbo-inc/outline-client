from typing import Any

from outline_client.operations.generic import Operation, body, many, one, success
from outline_client.schemas.models import (
    Invite,
    Membership,
    SortDirection,
    User,
    UserFilterCondition,
    UserFilterGroup,
    UserRole,
)
from outline_client.schemas.results import InvitesResult, UserMembershipsResult

# -----------------------------------------------------------------------------
# OPERATION: list_users
# -----------------------------------------------------------------------------


def list_users(
    *,
    query: str | None = None,
    filters: list[UserFilterCondition | UserFilterGroup] | None = None,
    emails: list[str] | None = None,
    filter: str | None = None,
    role: UserRole | str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[User]]:
    """
    Build the `users.list` operation.

    Returns:
        Operation[list[User]]: The list users operation.
    """
    return Operation(
        path="users.list",
        payload=body(
            query=query,
            filters=filters,
            emails=emails,
            filter=filter,
            role=role,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(User),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_user
# -----------------------------------------------------------------------------


def get_user(id: str) -> Operation[User]:
    """
    Build the `users.info` operation.

    Returns:
        Operation[User]: The get user operation.
    """
    return Operation(
        path="users.info",
        payload=body(id=id),
        parse=one(User),
    )


# -----------------------------------------------------------------------------
# OPERATION: invite_users
# -----------------------------------------------------------------------------


def invite_users(
    invites: list[Invite],
    *,
    suppress_email: bool | None = None,
) -> Operation[InvitesResult]:
    """
    Build the `users.invite` operation.

    Returns:
        Operation[InvitesResult]: The invite users operation.
    """
    return Operation(
        path="users.invite",
        payload=body(invites=invites, suppressEmail=suppress_email),
        parse=one(InvitesResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: resend_invite
# -----------------------------------------------------------------------------


def resend_invite(id: str) -> Operation[bool]:
    """
    Build the `users.resendInvite` operation.

    Returns:
        Operation[bool]: The resend invite operation.
    """
    return Operation(
        path="users.resendInvite",
        payload=body(id=id),
        parse=success,
    )


# -----------------------------------------------------------------------------
# OPERATION: update_user
# -----------------------------------------------------------------------------


def update_user(
    *,
    name: str | None = None,
    language: str | None = None,
    avatar_url: str | None = None,
    preferences: dict[str, Any] | None = None,
) -> Operation[User]:
    """
    Build the `users.update` operation.

    Returns:
        Operation[User]: The update user operation.
    """
    return Operation(
        path="users.update",
        payload=body(
            name=name,
            language=language,
            avatarUrl=avatar_url,
            preferences=preferences,
        ),
        parse=one(User),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_user_email
# -----------------------------------------------------------------------------


def update_user_email(
    email: str,
    *,
    id: str | None = None,
) -> Operation[bool]:
    """
    Build the `users.updateEmail` operation.

    Returns:
        Operation[bool]: The update user email operation.
    """
    return Operation(
        path="users.updateEmail",
        payload=body(email=email, id=id),
        parse=success,
    )


# -----------------------------------------------------------------------------
# OPERATION: update_user_role
# -----------------------------------------------------------------------------


def update_user_role(id: str, role: UserRole | str) -> Operation[User]:
    """
    Build the `users.update_role` operation.

    Returns:
        Operation[User]: The update user role operation.
    """
    return Operation(
        path="users.update_role",
        payload=body(id=id, role=role),
        parse=one(User),
    )


# -----------------------------------------------------------------------------
# OPERATION: suspend_user
# -----------------------------------------------------------------------------


def suspend_user(id: str) -> Operation[User]:
    """
    Build the `users.suspend` operation.

    Returns:
        Operation[User]: The suspend user operation.
    """
    return Operation(
        path="users.suspend",
        payload=body(id=id),
        parse=one(User),
    )


# -----------------------------------------------------------------------------
# OPERATION: activate_user
# -----------------------------------------------------------------------------


def activate_user(id: str) -> Operation[User]:
    """
    Build the `users.activate` operation.

    Returns:
        Operation[User]: The activate user operation.
    """
    return Operation(
        path="users.activate",
        payload=body(id=id),
        parse=one(User),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_user
# -----------------------------------------------------------------------------


def delete_user(id: str) -> Operation[bool]:
    """
    Build the `users.delete` operation.

    Returns:
        Operation[bool]: The delete user operation.
    """
    return Operation(
        path="users.delete",
        payload=body(id=id),
        parse=success,
    )


# -----------------------------------------------------------------------------
# OPERATION: subscribe_to_notifications
# -----------------------------------------------------------------------------


def subscribe_to_notifications(event_type: str) -> Operation[User]:
    """
    Build the `users.notificationsSubscribe` operation.

    Returns:
        Operation[User]: The subscribe to notifications operation.
    """
    return Operation(
        path="users.notificationsSubscribe",
        payload=body(eventType=event_type),
        parse=one(User),
    )


# -----------------------------------------------------------------------------
# OPERATION: unsubscribe_from_notifications
# -----------------------------------------------------------------------------


def unsubscribe_from_notifications(event_type: str) -> Operation[User]:
    """
    Build the `users.notificationsUnsubscribe` operation.

    Returns:
        Operation[User]: The unsubscribe from notifications operation.
    """
    return Operation(
        path="users.notificationsUnsubscribe",
        payload=body(eventType=event_type),
        parse=one(User),
    )


# -----------------------------------------------------------------------------
# OPERATION: list_user_memberships
# -----------------------------------------------------------------------------


def list_user_memberships(
    *,
    offset: int | None = None,
    limit: int | None = None,
) -> Operation[UserMembershipsResult]:
    """
    Build the `userMemberships.list` operation.

    Returns:
        Operation[UserMembershipsResult]: The list user memberships operation.
    """
    return Operation(
        path="userMemberships.list",
        payload=body(offset=offset, limit=limit),
        parse=one(UserMembershipsResult),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_user_membership
# -----------------------------------------------------------------------------


def update_user_membership(id: str, index: str) -> Operation[Membership]:
    """
    Build the `userMemberships.update` operation.

    Returns:
        Operation[Membership]: The update user membership operation.
    """
    return Operation(
        path="userMemberships.update",
        payload=body(id=id, index=index),
        parse=one(Membership),
    )
