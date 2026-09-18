from datetime import datetime

from outline_client.operations.generic import Operation, body, many, one, success
from outline_client.schemas.models import ApiKey, SortDirection

# -----------------------------------------------------------------------------
# OPERATION: list_api_keys
# -----------------------------------------------------------------------------


def list_api_keys(
    *,
    user_id: str | None = None,
    query: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[ApiKey]]:
    """
    Build the `apiKeys.list` operation.

    Returns:
        Operation[list[ApiKey]]: The list API keys operation.
    """
    return Operation(
        path="apiKeys.list",
        payload=body(
            userId=user_id,
            query=query,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(ApiKey),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_api_key
# -----------------------------------------------------------------------------


def create_api_key(
    name: str,
    *,
    expires_at: datetime | str | None = None,
    scope: list[str] | None = None,
) -> Operation[ApiKey]:
    """
    Build the `apiKeys.create` operation.

    Returns:
        Operation[ApiKey]: The create API key operation.
    """
    return Operation(
        path="apiKeys.create",
        payload=body(name=name, expiresAt=expires_at, scope=scope),
        parse=one(ApiKey),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_api_key
# -----------------------------------------------------------------------------


def delete_api_key(id: str) -> Operation[bool]:
    """
    Build the `apiKeys.delete` operation.

    Returns:
        Operation[bool]: The delete API key operation.
    """
    return Operation(
        path="apiKeys.delete",
        payload=body(id=id),
        parse=success,
    )
