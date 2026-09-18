from pydantic import Field

from outline_client.schemas.base import OutlineBaseModel
from outline_client.schemas.models import Pagination, Policy

# =============================================================================
# CLASS: Response
# =============================================================================


class Response[T](OutlineBaseModel):
    """
    The envelope every Outline method that returns one object answers with.

    `policies` accompanies most reads and describes what the caller may do with
    the record. Client methods return `data` alone; a caller who needs the
    policies reads the envelope through `OutlineClient.request`.
    """

    data: T
    policies: list[Policy] = Field(default_factory=list)


# =============================================================================
# CLASS: ListResponse
# =============================================================================


class ListResponse[T](OutlineBaseModel):
    """
    The envelope every Outline `list`-style method answers with.

    `pagination` echoes the `offset` and `limit` that produced the page rather
    than reporting a total, so the only way to know whether more records exist
    is to ask for another page. `OutlineClient.paginate` does exactly that.
    """

    data: list[T] = Field(default_factory=list)
    pagination: Pagination | None = None
    policies: list[Policy] = Field(default_factory=list)


# =============================================================================
# CLASS: SuccessResponse
# =============================================================================


class SuccessResponse(OutlineBaseModel):
    """
    The envelope returned by methods that delete or acknowledge rather than read.

    A failed call never reaches this model: Outline reports failure with a 4xx
    status and an `Error` body, which the transport raises on. `success` is
    therefore always `True` in practice, and is modelled only so the wire shape
    round-trips.
    """

    success: bool = False
