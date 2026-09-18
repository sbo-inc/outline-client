from datetime import datetime

from outline_client.operations.generic import Operation, body, nested, one, success
from outline_client.schemas.models import Notification

# -----------------------------------------------------------------------------
# OPERATION: list_notifications
# -----------------------------------------------------------------------------


def list_notifications(
    *,
    event_type: str | None = None,
    archived: bool | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> Operation[list[Notification]]:
    """
    Build the `notifications.list` operation.

    Returns:
        Operation[list[Notification]]: The list notifications operation.
    """
    return Operation(
        path="notifications.list",
        payload=body(
            eventType=event_type,
            archived=archived,
            offset=offset,
            limit=limit,
        ),
        parse=nested("notifications", Notification),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_notification
# -----------------------------------------------------------------------------


def update_notification(
    id: str,
    *,
    viewed_at: datetime | str | None = None,
    archived_at: datetime | str | None = None,
) -> Operation[Notification]:
    """
    Build the `notifications.update` operation.

    Returns:
        Operation[Notification]: The update notification operation.
    """
    return Operation(
        path="notifications.update",
        payload=body(id=id, viewedAt=viewed_at, archivedAt=archived_at),
        parse=one(Notification),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_all_notifications
# -----------------------------------------------------------------------------


def update_all_notifications(
    *,
    viewed_at: datetime | str | None = None,
    archived_at: datetime | str | None = None,
) -> Operation[bool]:
    """
    Build the `notifications.update_all` operation.

    Returns:
        Operation[bool]: The update all notifications operation.
    """
    return Operation(
        path="notifications.update_all",
        payload=body(viewedAt=viewed_at, archivedAt=archived_at),
        parse=success,
    )
