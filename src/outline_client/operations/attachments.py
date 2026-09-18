from outline_client.operations.generic import Operation, body, many, one, success
from outline_client.schemas.models import Attachment, SortDirection
from outline_client.schemas.results import AttachmentUpload

# -----------------------------------------------------------------------------
# OPERATION: list_attachments
# -----------------------------------------------------------------------------


def list_attachments(
    *,
    document_id: str | None = None,
    user_id: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[Attachment]]:
    """
    Build the `attachments.list` operation.

    Returns:
        Operation[list[Attachment]]: The list attachments operation.
    """
    return Operation(
        path="attachments.list",
        payload=body(
            documentId=document_id,
            userId=user_id,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(Attachment),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_attachment
# -----------------------------------------------------------------------------


def create_attachment(
    name: str,
    content_type: str,
    size: int,
    *,
    document_id: str | None = None,
) -> Operation[AttachmentUpload]:
    """
    Build the `attachments.create` operation.

    Returns:
        Operation[AttachmentUpload]: The create attachment operation.
    """
    return Operation(
        path="attachments.create",
        payload=body(
            name=name,
            contentType=content_type,
            size=size,
            documentId=document_id,
        ),
        parse=one(AttachmentUpload),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_attachment_from_url
# -----------------------------------------------------------------------------


def create_attachment_from_url(
    url: str,
    *,
    document_id: str | None = None,
    id: str | None = None,
) -> Operation[Attachment]:
    """
    Build the `attachments.createFromUrl` operation.

    Returns:
        Operation[Attachment]: The create attachment from URL operation.
    """
    return Operation(
        path="attachments.createFromUrl",
        payload=body(url=url, documentId=document_id, id=id),
        parse=one(Attachment),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_attachment
# -----------------------------------------------------------------------------


def delete_attachment(id: str) -> Operation[bool]:
    """
    Build the `attachments.delete` operation.

    Returns:
        Operation[bool]: The delete attachment operation.
    """
    return Operation(
        path="attachments.delete",
        payload=body(id=id),
        parse=success,
    )
