from outline_client.operations.generic import Operation, body, many, one, success
from outline_client.schemas.models import (
    DataAttribute,
    DataAttributeDataType,
    DataAttributeOptions,
    SortDirection,
)

# -----------------------------------------------------------------------------
# OPERATION: list_data_attributes
# -----------------------------------------------------------------------------


def list_data_attributes(
    *,
    offset: int | None = None,
    limit: int | None = None,
    sort: str | None = None,
    direction: SortDirection | str | None = None,
) -> Operation[list[DataAttribute]]:
    """
    Build the `dataAttributes.list` operation.

    Returns:
        Operation[list[DataAttribute]]: The list data attributes operation.
    """
    return Operation(
        path="dataAttributes.list",
        payload=body(offset=offset, limit=limit, sort=sort, direction=direction),
        parse=many(DataAttribute),
    )


# -----------------------------------------------------------------------------
# OPERATION: get_data_attribute
# -----------------------------------------------------------------------------


def get_data_attribute(id: str) -> Operation[DataAttribute]:
    """
    Build the `dataAttributes.info` operation.

    Returns:
        Operation[DataAttribute]: The get data attribute operation.
    """
    return Operation(
        path="dataAttributes.info",
        payload=body(id=id),
        parse=one(DataAttribute),
    )


# -----------------------------------------------------------------------------
# OPERATION: create_data_attribute
# -----------------------------------------------------------------------------


def create_data_attribute(
    name: str,
    data_type: DataAttributeDataType | str,
    *,
    description: str | None = None,
    options: DataAttributeOptions | None = None,
    pinned: bool | None = None,
) -> Operation[DataAttribute]:
    """
    Build the `dataAttributes.create` operation.

    Returns:
        Operation[DataAttribute]: The create data attribute operation.
    """
    return Operation(
        path="dataAttributes.create",
        payload=body(
            name=name,
            dataType=data_type,
            description=description,
            options=options,
            pinned=pinned,
        ),
        parse=one(DataAttribute),
    )


# -----------------------------------------------------------------------------
# OPERATION: update_data_attribute
# -----------------------------------------------------------------------------


def update_data_attribute(
    id: str,
    name: str,
    *,
    description: str | None = None,
    options: DataAttributeOptions | None = None,
    pinned: bool | None = None,
) -> Operation[DataAttribute]:
    """
    Build the `dataAttributes.update` operation.

    Returns:
        Operation[DataAttribute]: The update data attribute operation.
    """
    return Operation(
        path="dataAttributes.update",
        payload=body(
            id=id,
            name=name,
            description=description,
            options=options,
            pinned=pinned,
        ),
        parse=one(DataAttribute),
    )


# -----------------------------------------------------------------------------
# OPERATION: delete_data_attribute
# -----------------------------------------------------------------------------


def delete_data_attribute(id: str) -> Operation[bool]:
    """
    Build the `dataAttributes.delete` operation.

    Returns:
        Operation[bool]: The delete data attribute operation.
    """
    return Operation(
        path="dataAttributes.delete",
        payload=body(id=id),
        parse=success,
    )
