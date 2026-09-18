from outline_client.operations.generic import Operation, body, many, one, success
from outline_client.schemas.models import SortDirection, WebhookSubscription

# -----------------------------------------------------------------------------
# OPERATION: list_webhook_subscriptions
# -----------------------------------------------------------------------------


def list_webhook_subscriptions(
    *,
    query: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[WebhookSubscription]]:
    """
    Build the `webhookSubscriptions.list` operation.

    Returns:
        Operation[list[WebhookSubscription]]: The list webhook subscriptions
            operation.
    """
    return Operation(
        path="webhookSubscriptions.list",
        payload=body(
            query=query,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(WebhookSubscription),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_webhook_subscription
# -----------------------------------------------------------------------------


def create_webhook_subscription(
    name: str,
    url: str,
    events: list[str],
    *,
    secret: str | None = None,
) -> Operation[WebhookSubscription]:
    """
    Build the `webhookSubscriptions.create` operation.

    Returns:
        Operation[WebhookSubscription]: The create webhook subscription operation.
    """
    return Operation(
        path="webhookSubscriptions.create",
        payload=body(name=name, url=url, events=events, secret=secret),
        parse=one(WebhookSubscription),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_webhook_subscription
# -----------------------------------------------------------------------------


def update_webhook_subscription(
    id: str,
    name: str,
    url: str,
    events: list[str],
    *,
    secret: str | None = None,
) -> Operation[WebhookSubscription]:
    """
    Build the `webhookSubscriptions.update` operation.

    Returns:
        Operation[WebhookSubscription]: The update webhook subscription operation.
    """
    return Operation(
        path="webhookSubscriptions.update",
        payload=body(id=id, name=name, url=url, events=events, secret=secret),
        parse=one(WebhookSubscription),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_webhook_subscription
# -----------------------------------------------------------------------------


def delete_webhook_subscription(id: str) -> Operation[bool]:
    """
    Build the `webhookSubscriptions.delete` operation.

    Returns:
        Operation[bool]: The delete webhook subscription operation.
    """
    return Operation(
        path="webhookSubscriptions.delete",
        payload=body(id=id),
        parse=success,
    )
