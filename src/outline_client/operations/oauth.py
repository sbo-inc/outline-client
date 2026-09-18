"""
Operations for the OAuth application surface.

Covers both `oauthClients.*`, which registers and manages the applications a
workspace publishes, and `oauthAuthentications.*`, which lists and revokes the
grants users have given those applications. They are one module because the
two halves are only meaningful together.
"""

from outline_client.operations.generic import Operation, body, many, one, success
from outline_client.schemas.models import OAuthAuthentication, OAuthClient

# -----------------------------------------------------------------------------
# OPERATION: list_oauth_clients
# -----------------------------------------------------------------------------


def list_oauth_clients(
    *,
    offset: int | None = None,
    limit: int | None = None,
) -> Operation[list[OAuthClient]]:
    """
    Build the `oauthClients.list` operation.

    Returns:
        Operation[list[OAuthClient]]: The list OAuth clients operation.
    """
    return Operation(
        path="oauthClients.list",
        payload=body(offset=offset, limit=limit),
        parse=many(OAuthClient),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_oauth_client
# -----------------------------------------------------------------------------


def get_oauth_client(
    id: str | None = None,
    *,
    client_id: str | None = None,
) -> Operation[OAuthClient]:
    """
    Build the `oauthClients.info` operation.

    Returns:
        Operation[OAuthClient]: The get OAuth client operation.
    """
    return Operation(
        path="oauthClients.info",
        payload=body(id=id, clientId=client_id),
        parse=one(OAuthClient),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_oauth_client
# -----------------------------------------------------------------------------


def create_oauth_client(
    name: str,
    redirect_uris: list[str],
    *,
    description: str | None = None,
    developer_name: str | None = None,
    developer_url: str | None = None,
    avatar_url: str | None = None,
    published: bool | None = None,
) -> Operation[OAuthClient]:
    """
    Build the `oauthClients.create` operation.

    Returns:
        Operation[OAuthClient]: The create OAuth client operation.
    """
    return Operation(
        path="oauthClients.create",
        payload=body(
            name=name,
            redirectUris=redirect_uris,
            description=description,
            developerName=developer_name,
            developerUrl=developer_url,
            avatarUrl=avatar_url,
            published=published,
        ),
        parse=one(OAuthClient),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_oauth_client
# -----------------------------------------------------------------------------


def update_oauth_client(
    id: str,
    *,
    name: str | None = None,
    description: str | None = None,
    developer_name: str | None = None,
    developer_url: str | None = None,
    avatar_url: str | None = None,
    redirect_uris: list[str] | None = None,
    published: bool | None = None,
) -> Operation[OAuthClient]:
    """
    Build the `oauthClients.update` operation.

    Returns:
        Operation[OAuthClient]: The update OAuth client operation.
    """
    return Operation(
        path="oauthClients.update",
        payload=body(
            id=id,
            name=name,
            description=description,
            developerName=developer_name,
            developerUrl=developer_url,
            avatarUrl=avatar_url,
            redirectUris=redirect_uris,
            published=published,
        ),
        parse=one(OAuthClient),
    )


# -----------------------------------------------------------------------------
# OPERATION: rotate_oauth_client_secret
# -----------------------------------------------------------------------------


def rotate_oauth_client_secret(id: str) -> Operation[OAuthClient]:
    """
    Build the `oauthClients.rotate_secret` operation.

    Returns:
        Operation[OAuthClient]: The rotate OAuth client secret operation.
    """
    return Operation(
        path="oauthClients.rotate_secret",
        payload=body(id=id),
        parse=one(OAuthClient),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_oauth_client
# -----------------------------------------------------------------------------


def delete_oauth_client(id: str) -> Operation[bool]:
    """
    Build the `oauthClients.delete` operation.

    Returns:
        Operation[bool]: The delete OAuth client operation.
    """
    return Operation(
        path="oauthClients.delete",
        payload=body(id=id),
        parse=success,
    )


# -----------------------------------------------------------------------------
# OPERATION: list_oauth_authentications
# -----------------------------------------------------------------------------


def list_oauth_authentications(
    *,
    offset: int | None = None,
    limit: int | None = None,
) -> Operation[list[OAuthAuthentication]]:
    """
    Build the `oauthAuthentications.list` operation.

    Returns:
        Operation[list[OAuthAuthentication]]: The list OAuth authentications
            operation.
    """
    return Operation(
        path="oauthAuthentications.list",
        payload=body(offset=offset, limit=limit),
        parse=many(OAuthAuthentication),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_oauth_authentication
# -----------------------------------------------------------------------------


def delete_oauth_authentication(
    oauth_client_id: str,
    *,
    scope: list[str] | None = None,
) -> Operation[bool]:
    """
    Build the `oauthAuthentications.delete` operation.

    Returns:
        Operation[bool]: The delete OAuth authentication operation.
    """
    return Operation(
        path="oauthAuthentications.delete",
        payload=body(oauthClientId=oauth_client_id, scope=scope),
        parse=success,
    )
