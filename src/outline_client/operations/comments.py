from typing import Any

from outline_client.operations.generic import Operation, body, many, one, success
from outline_client.schemas.enums import CommentStatusFilter
from outline_client.schemas.models import Comment, SortDirection

# -----------------------------------------------------------------------------
# OPERATION: list_comments
# -----------------------------------------------------------------------------


def list_comments(
    *,
    document_id: str | None = None,
    collection_id: str | None = None,
    parent_comment_id: str | None = None,
    status_filter: list[CommentStatusFilter | str] | None = None,
    include_anchor_text: bool | None = None,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[Comment]]:
    """
    Build the `comments.list` operation.

    Returns:
        Operation[list[Comment]]: The list comments operation.
    """
    return Operation(
        path="comments.list",
        payload=body(
            documentId=document_id,
            collectionId=collection_id,
            parentCommentId=parent_comment_id,
            statusFilter=status_filter,
            includeAnchorText=include_anchor_text,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(Comment),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_comment
# -----------------------------------------------------------------------------


def get_comment(
    id: str,
    *,
    include_anchor_text: bool | None = None,
) -> Operation[Comment]:
    """
    Build the `comments.info` operation.

    Returns:
        Operation[Comment]: The get comment operation.
    """
    return Operation(
        path="comments.info",
        payload=body(id=id, includeAnchorText=include_anchor_text),
        parse=one(Comment),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_comment
# -----------------------------------------------------------------------------


def create_comment(
    document_id: str,
    *,
    id: str | None = None,
    parent_comment_id: str | None = None,
    data: dict[str, Any] | None = None,
    text: str | None = None,
    anchor_text: str | None = None,
    anchor_prefix: str | None = None,
    anchor_suffix: str | None = None,
) -> Operation[Comment]:
    """
    Build the `comments.create` operation.

    Returns:
        Operation[Comment]: The create comment operation.
    """
    return Operation(
        path="comments.create",
        payload=body(
            documentId=document_id,
            id=id,
            parentCommentId=parent_comment_id,
            data=data,
            text=text,
            anchorText=anchor_text,
            anchorPrefix=anchor_prefix,
            anchorSuffix=anchor_suffix,
        ),
        parse=one(Comment),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_comment
# -----------------------------------------------------------------------------


def update_comment(
    id: str,
    data: dict[str, Any] | None = None,
    *,
    text: str | None = None,
) -> Operation[Comment]:
    """
    Build the `comments.update` operation.

    Returns:
        Operation[Comment]: The update comment operation.
    """
    return Operation(
        path="comments.update",
        payload=body(id=id, data=data, text=text),
        parse=one(Comment),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_comment
# -----------------------------------------------------------------------------


def delete_comment(id: str) -> Operation[bool]:
    """
    Build the `comments.delete` operation.

    Returns:
        Operation[bool]: The delete comment operation.
    """
    return Operation(
        path="comments.delete",
        payload=body(id=id),
        parse=success,
    )


# -----------------------------------------------------------------------------
# OPERATION: resolve_comment
# -----------------------------------------------------------------------------


def resolve_comment(id: str) -> Operation[Comment]:
    """
    Build the `comments.resolve` operation.

    Returns:
        Operation[Comment]: The resolve comment operation.
    """
    return Operation(
        path="comments.resolve",
        payload=body(id=id),
        parse=one(Comment),
    )


# -----------------------------------------------------------------------------
# OPERATION: unresolve_comment
# -----------------------------------------------------------------------------


def unresolve_comment(id: str) -> Operation[Comment]:
    """
    Build the `comments.unresolve` operation.

    Returns:
        Operation[Comment]: The unresolve comment operation.
    """
    return Operation(
        path="comments.unresolve",
        payload=body(id=id),
        parse=one(Comment),
    )


# -----------------------------------------------------------------------------
# OPERATION: add_comment_reaction
# -----------------------------------------------------------------------------


def add_comment_reaction(id: str, emoji: str) -> Operation[bool]:
    """
    Build the `comments.add_reaction` operation.

    Returns:
        Operation[bool]: The add comment reaction operation.
    """
    return Operation(
        path="comments.add_reaction",
        payload=body(id=id, emoji=emoji),
        parse=success,
    )


# -----------------------------------------------------------------------------
# OPERATION: remove_comment_reaction
# -----------------------------------------------------------------------------


def remove_comment_reaction(id: str, emoji: str) -> Operation[bool]:
    """
    Build the `comments.remove_reaction` operation.

    Returns:
        Operation[bool]: The remove comment reaction operation.
    """
    return Operation(
        path="comments.remove_reaction",
        payload=body(id=id, emoji=emoji),
        parse=success,
    )
