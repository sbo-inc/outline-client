"""
The pieces every operation module is built from.

An `Operation` is one API call described without performing it: the method
path, the request payload, and the function that turns the decoded response
into a result. Both clients build the same operations and differ only in how
they put them on the wire, which is what keeps payload construction and
response reshaping written once rather than once per surface.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel
from pydantic_core import to_jsonable_python

from outline_client.schemas.envelopes import Response, SuccessResponse

# =============================================================================
# CLASS: Operation
# =============================================================================


@dataclass(frozen=True)
class Operation[T]:
    """
    One API call, described without performing it.
    """

    path: str
    """
    The API method to POST to, e.g. `documents.info`.
    """
    payload: dict[str, Any]
    """
    The JSON request body, already stripped of unset arguments.
    """
    parse: Callable[[dict[str, Any]], T]
    """
    Turns the decoded response body into the operation's result.
    """


# =============================================================================
# FUNCTION: body
# =============================================================================


def body(**fields: Any) -> dict[str, Any]:
    """
    Build a request payload from the arguments a caller actually supplied.

    Arguments left at `None` are dropped rather than sent as JSON `null`,
    because the two mean different things to Outline: omitting `parentDocumentId`
    leaves a document where it is, while sending it as `null` moves it to the
    collection root. A client method exposes only the first, so a caller who
    needs the second reaches for `OutlineClient.request`.

    Enums, UUIDs, datetimes, and nested models are converted to their JSON
    forms here, so an operation can pass a `DocumentFilter` straight through.

    Returns:
        dict[str, Any]: The request payload.
    """
    return {
        key: to_jsonable_python(value, by_alias=True, exclude_none=True)
        for key, value in fields.items()
        if value is not None
    }


# =============================================================================
# FUNCTIONS: Response parsers
# =============================================================================
#
# Outline answers in a small number of recurring shapes. Each builder below
# returns the `parse` callable for one of them, so an operation names its shape
# instead of respelling the reshaping.


# -----------------------------------------------------------------------------
# FUNCTION: one
# -----------------------------------------------------------------------------


def one[T: BaseModel](model: type[T]) -> Callable[[dict[str, Any]], T]:
    """
    Parse a `data` that is a single object.

    The payload is validated directly rather than through `Response`: the model
    is only known at run time, and `Response[model]` would be a generic alias
    rather than a concrete model. `Response` still describes the shape for
    anyone reading the whole envelope through `OutlineClient.request`.

    Returns:
        Callable[[dict[str, Any]], T]: The parser for this response.
    """

    def parse(data: dict[str, Any]) -> T:
        return model.model_validate(data.get("data"))

    return parse


# -----------------------------------------------------------------------------
# FUNCTION: many
# -----------------------------------------------------------------------------


def many[T: BaseModel](model: type[T]) -> Callable[[dict[str, Any]], list[T]]:
    """
    Parse a `data` that is an array of objects.

    Returns:
        Callable[[dict[str, Any]], list[T]]: The parser for this response.
    """

    def parse(data: dict[str, Any]) -> list[T]:
        records: list[Any] = data.get("data") or []
        return [model.model_validate(record) for record in records]

    return parse


# -----------------------------------------------------------------------------
# FUNCTION: nested
# -----------------------------------------------------------------------------


def nested[T: BaseModel](
    key: str, model: type[T]
) -> Callable[[dict[str, Any]], list[T]]:
    """
    Parse an array that arrives wrapped in an object rather than as `data`.

    `notifications.list` is documented as answering with `data` as an array but
    in fact answers with `{"notifications": [...], "unseen": 0}`. Both shapes
    are accepted here, so the client keeps working either way; the count beside
    the array is reachable through `OutlineClient.request`.

    Returns:
        Callable[[dict[str, Any]], list[T]]: The parser for this response.
    """

    def parse(data: dict[str, Any]) -> list[T]:
        payload: Any = data.get("data") or []
        records: list[Any] = (
            payload if isinstance(payload, list) else payload.get(key, [])
        )
        return [model.model_validate(record) for record in records]

    return parse


# -----------------------------------------------------------------------------
# FUNCTION: whole
# -----------------------------------------------------------------------------


def whole[T: BaseModel](model: type[T]) -> Callable[[dict[str, Any]], T]:
    """
    Parse a response whose payload is the body itself, with no `data` wrapper.

    Only `documents.answerQuestion` is shaped this way.

    Returns:
        Callable[[dict[str, Any]], T]: The parser for this response.
    """

    def parse(data: dict[str, Any]) -> T:
        return model.model_validate(data)

    return parse


# -----------------------------------------------------------------------------
# FUNCTION: success
# -----------------------------------------------------------------------------


def success(data: dict[str, Any]) -> bool:
    """
    Parse a response that only acknowledges the call.

    Returns:
        bool: Whether the call succeeded, which is always True in practice -
            a failure is raised by the transport before this is reached.
    """
    return SuccessResponse.model_validate(data).success


# -----------------------------------------------------------------------------
# FUNCTION: text
# -----------------------------------------------------------------------------


def text(data: dict[str, Any]) -> str:
    """
    Parse a `data` that is a bare string, as document exports are.

    Returns:
        str: The string payload.
    """
    return Response[str].model_validate(data).data


# -----------------------------------------------------------------------------
# FUNCTION: raw
# -----------------------------------------------------------------------------


def raw(data: dict[str, Any]) -> dict[str, Any]:
    """
    Return the decoded body unparsed.

    Returns:
        dict[str, Any]: The response body as decoded.
    """
    return data


# -----------------------------------------------------------------------------
# FUNCTION: form_fields
# -----------------------------------------------------------------------------


def form_fields(payload: dict[str, Any]) -> dict[str, str]:
    """
    Render a JSON payload as the text fields of a multipart form.

    A multipart part has no type of its own, so every value travels as text and
    the server parses it back. Python's `str(True)` is `"True"`, which Outline
    does not read as a boolean, so booleans are spelled the way JSON spells
    them; everything else is already a string, a number, or an identifier.

    Returns:
        dict[str, str]: The payload as form fields.
    """
    fields: dict[str, str] = {}
    for key, value in payload.items():
        if isinstance(value, bool):
            fields[key] = "true" if value else "false"
        else:
            fields[key] = str(value)

    return fields
