from typing import Any

from outline_client.operations.generic import Operation, body, many, one, success
from outline_client.schemas.models import SortDirection, Template

# -----------------------------------------------------------------------------
# OPERATION: list_templates
# -----------------------------------------------------------------------------


def list_templates(
    *,
    collection_id: str | None = None,
    query: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[Template]]:
    """
    Build the `templates.list` operation.

    Returns:
        Operation[list[Template]]: The list templates operation.
    """
    return Operation(
        path="templates.list",
        payload=body(
            collectionId=collection_id,
            query=query,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        ),
        parse=many(Template),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_template
# -----------------------------------------------------------------------------


def get_template(id: str) -> Operation[Template]:
    """
    Build the `templates.info` operation.

    Returns:
        Operation[Template]: The get template operation.
    """
    return Operation(
        path="templates.info",
        payload=body(id=id),
        parse=one(Template),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_template
# -----------------------------------------------------------------------------


def create_template(
    *,
    id: str | None = None,
    title: str | None = None,
    data: dict[str, Any] | None = None,
    icon: str | None = None,
    color: str | None = None,
    collection_id: str | None = None,
    publish: bool | None = None,
) -> Operation[Template]:
    """
    Build the `templates.create` operation.

    Returns:
        Operation[Template]: The create template operation.
    """
    return Operation(
        path="templates.create",
        payload=body(
            id=id,
            title=title,
            data=data,
            icon=icon,
            color=color,
            collectionId=collection_id,
            publish=publish,
        ),
        parse=one(Template),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_template
# -----------------------------------------------------------------------------


def update_template(
    id: str,
    *,
    title: str | None = None,
    data: dict[str, Any] | None = None,
    icon: str | None = None,
    color: str | None = None,
    full_width: bool | None = None,
    collection_id: str | None = None,
    publish: bool | None = None,
) -> Operation[Template]:
    """
    Build the `templates.update` operation.

    Returns:
        Operation[Template]: The update template operation.
    """
    return Operation(
        path="templates.update",
        payload=body(
            id=id,
            title=title,
            data=data,
            icon=icon,
            color=color,
            fullWidth=full_width,
            collectionId=collection_id,
            publish=publish,
        ),
        parse=one(Template),
    )


# -----------------------------------------------------------------------------
# OPERATION: duplicate_template
# -----------------------------------------------------------------------------


def duplicate_template(
    id: str,
    *,
    title: str | None = None,
    collection_id: str | None = None,
) -> Operation[Template]:
    """
    Build the `templates.duplicate` operation.

    Returns:
        Operation[Template]: The duplicate template operation.
    """
    return Operation(
        path="templates.duplicate",
        payload=body(id=id, title=title, collectionId=collection_id),
        parse=one(Template),
    )


# -----------------------------------------------------------------------------
# OPERATION: restore_template
# -----------------------------------------------------------------------------


def restore_template(id: str) -> Operation[Template]:
    """
    Build the `templates.restore` operation.

    Returns:
        Operation[Template]: The restore template operation.
    """
    return Operation(
        path="templates.restore",
        payload=body(id=id),
        parse=one(Template),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_template
# -----------------------------------------------------------------------------


def delete_template(id: str) -> Operation[bool]:
    """
    Build the `templates.delete` operation.

    Returns:
        Operation[bool]: The delete template operation.
    """
    return Operation(
        path="templates.delete",
        payload=body(id=id),
        parse=success,
    )
