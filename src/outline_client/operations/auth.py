from outline_client.operations.generic import Operation, body, one, success
from outline_client.schemas.models import Auth
from outline_client.schemas.results import AuthConfig

# -----------------------------------------------------------------------------
# OPERATION: get_auth_info
# -----------------------------------------------------------------------------


def get_auth_info() -> Operation[Auth]:
    """
    Build the `auth.info` operation.

    Returns:
        Operation[Auth]: The get auth info operation.
    """
    return Operation(
        path="auth.info",
        payload=body(),
        parse=one(Auth),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_auth_config
# -----------------------------------------------------------------------------


def get_auth_config() -> Operation[AuthConfig]:
    """
    Build the `auth.config` operation.

    Returns:
        Operation[AuthConfig]: The get auth config operation.
    """
    return Operation(
        path="auth.config",
        payload=body(),
        parse=one(AuthConfig),
    )


# -----------------------------------------------------------------------------
# OPERATION: sign_out
# -----------------------------------------------------------------------------


def sign_out() -> Operation[bool]:
    """
    Build the `auth.delete` operation.

    Returns:
        Operation[bool]: The sign out operation.
    """
    return Operation(
        path="auth.delete",
        payload=body(),
        parse=success,
    )
