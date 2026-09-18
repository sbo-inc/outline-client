from outline_client.operations.generic import Operation, body, one
from outline_client.schemas.models import AccessRequest, Permission

# -----------------------------------------------------------------------------
# OPERATION: create_access_request
# -----------------------------------------------------------------------------


def create_access_request(document_id: str) -> Operation[AccessRequest]:
    """
    Build the `accessRequests.create` operation.

    Returns:
        Operation[AccessRequest]: The create access request operation.
    """
    return Operation(
        path="accessRequests.create",
        payload=body(documentId=document_id),
        parse=one(AccessRequest),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_access_request
# -----------------------------------------------------------------------------


def get_access_request(
    id: str | None = None,
    *,
    document_id: str | None = None,
) -> Operation[AccessRequest]:
    """
    Build the `accessRequests.info` operation.

    Returns:
        Operation[AccessRequest]: The get access request operation.
    """
    return Operation(
        path="accessRequests.info",
        payload=body(id=id, documentId=document_id),
        parse=one(AccessRequest),
    )


# -----------------------------------------------------------------------------
# OPERATION: approve_access_request
# -----------------------------------------------------------------------------


def approve_access_request(
    id: str,
    *,
    permission: Permission | str | None = None,
) -> Operation[AccessRequest]:
    """
    Build the `accessRequests.approve` operation.

    Returns:
        Operation[AccessRequest]: The approve access request operation.
    """
    return Operation(
        path="accessRequests.approve",
        payload=body(id=id, permission=permission),
        parse=one(AccessRequest),
    )


# -----------------------------------------------------------------------------
# OPERATION: dismiss_access_request
# -----------------------------------------------------------------------------


def dismiss_access_request(id: str) -> Operation[AccessRequest]:
    """
    Build the `accessRequests.dismiss` operation.

    Returns:
        Operation[AccessRequest]: The dismiss access request operation.
    """
    return Operation(
        path="accessRequests.dismiss",
        payload=body(id=id),
        parse=one(AccessRequest),
    )
