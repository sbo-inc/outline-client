"""
Shared helpers for the unit tests.

Both clients are driven through `httpx.MockTransport`, so one handler function
can stand in for the API on either surface and the sync and async paths are
asserted against the same fixture data.
"""

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from outline_client.async_client import AsyncOutlineClient
from outline_client.client import OutlineClient

URL = "https://outline.example.test/api"
TOKEN = "ol_api_" + "x" * 38

Handler = Callable[[httpx.Request], httpx.Response]

# A UUID the fixtures reuse wherever the API would return one, so an assertion
# can name it rather than reaching into the response it came from.
DOCUMENT_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"


# =============================================================================
# FUNCTIONS: Response helpers
# =============================================================================


def body(request: httpx.Request) -> dict[str, Any]:
    """
    Decode the JSON body a client sent.

    Returns:
        dict[str, Any]: The decoded request body.
    """
    return json.loads(request.content)


def ok(data: Any = None, **extra: Any) -> httpx.Response:
    """
    Build an HTTP 200 carrying a successful Outline response.

    Returns:
        httpx.Response: The mocked response.
    """
    return httpx.Response(200, json={"data": data, "status": 200, "ok": True, **extra})


def failure(
    status: int = 400,
    error: str = "validation_error",
    message: str = "Boom",
) -> httpx.Response:
    """
    Build a failed Outline response, in the shape the API reports errors in.

    Returns:
        httpx.Response: The mocked response.
    """
    return httpx.Response(
        status,
        json={"ok": False, "error": error, "message": message, "status": status},
    )


def route(**responses: httpx.Response) -> Handler:
    """
    Build a handler that answers each API method with a prepared response.

    Keys are method paths with the dot replaced by an underscore, since they
    arrive as keyword arguments - `documents_info` answers `/documents.info`.

    Returns:
        Handler: The handler.
    """

    def handle(request: httpx.Request) -> httpx.Response:
        method = request.url.path.removeprefix("/api/")
        response = responses.get(method.replace(".", "_"))
        if response is None:
            raise AssertionError(f"unexpected call to {method}")

        return response

    return handle


# =============================================================================
# FIXTURES: Environment isolation
# =============================================================================


OUTLINE_ENV_VARS = (
    "OUTLINE_API_URL",
    "OUTLINE_API_TOKEN",
    "OUTLINE_API_HEADERS",
    "OUTLINE_API_TIMEOUT",
    "OUTLINE_API_RETRIES",
    "OUTLINE_CLI_DISABLE",
)


@pytest.fixture(autouse=True)
def isolate_environment(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Clear the `OUTLINE_API_*` variables so unit tests never read the real shell.

    Without this a developer with a token exported sees different behaviour
    from CI, which has none: configuration falls back to the environment, so
    whether a call fails on the missing token or reaches a real workspace
    depends on who is running the suite. Integration tests are exempt - the
    live environment is the point.
    """
    if request.node.get_closest_marker("integration"):
        return

    for name in OUTLINE_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


# =============================================================================
# FIXTURES: Mock-transport clients
# =============================================================================


@pytest.fixture
def make_client() -> Callable[..., OutlineClient]:
    """
    Return a factory building an `OutlineClient` backed by a handler.

    Returns:
        Callable[..., OutlineClient]: The client factory.
    """

    def factory(handler: Handler, **kwargs: Any) -> OutlineClient:
        client = OutlineClient(url=URL, token=TOKEN, **kwargs)
        headers = client.http.headers
        client.close()
        client._http = httpx.Client(
            headers=headers, transport=httpx.MockTransport(handler)
        )
        return client

    return factory


@pytest.fixture
def make_async_client() -> Callable[..., AsyncOutlineClient]:
    """
    Return a factory building an `AsyncOutlineClient` backed by a handler.

    Returns:
        Callable[..., AsyncOutlineClient]: The client factory.
    """

    def factory(handler: Handler, **kwargs: Any) -> AsyncOutlineClient:
        client = AsyncOutlineClient(url=URL, token=TOKEN, **kwargs)
        headers = client.http.headers
        client._http = httpx.AsyncClient(
            headers=headers, transport=httpx.MockTransport(handler)
        )
        return client

    return factory
