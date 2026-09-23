import json
import logging
import os
from typing import Any, NoReturn
from urllib.parse import urlsplit, urlunsplit

import httpx

from outline_client.errors import (
    OutlineConfigurationError,
    error_for_status,
)

logger = logging.getLogger("outline_client")
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("outline: %(message)s"))
logger.addHandler(console_handler)

# The cloud installation. Self-hosted callers pass their own workspace URL, but
# the cloud host is the one every caller who does not is trying to reach.
DEFAULT_URL = "https://app.getoutline.com/api"

# Outline mounts its whole API under this prefix. A caller who configures the
# workspace URL rather than the API URL has it appended for them.
API_PREFIX = "/api"

# Default (connect, read) timeout in seconds applied to every request. Without
# one, a stalled connection or an unresponsive server would block the caller
# indefinitely. The read budget is generous because search and export are slow
# on a large workspace.
DEFAULT_TIMEOUT: tuple[float, float] = (5.0, 60.0)


# =============================================================================
# FUNCTION: normalize_url
# =============================================================================


def normalize_url(url: str) -> str:
    """
    Resolve a configured URL to the API root every method hangs off.

    A workspace URL and an API URL are both accepted, because both are things a
    caller reasonably has to hand: `https://outline.example.com` gains the `/api`
    prefix, `https://outline.example.com/api` is already there and is left alone.
    A URL with any other path is trusted as given, so an installation behind a
    reverse proxy that remounts the API is not second-guessed.

    Returns:
        str: The API root, without a trailing slash.
    """
    parts = urlsplit(url.strip())
    if not parts.scheme or not parts.netloc:
        raise OutlineConfigurationError(
            f"Invalid Outline URL {url!r}; expected an absolute URL such as "
            "'https://app.getoutline.com/api'"
        )

    path = parts.path.rstrip("/")
    if not path:
        path = API_PREFIX

    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


# =============================================================================
# CLASS: BaseOutlineClient
# =============================================================================


class BaseOutlineClient:
    """
    Transport-agnostic half of the Outline clients.

    Holds everything that does not depend on whether the underlying HTTP call
    is awaited: configuration and its environment fallbacks, the request
    headers, and the decoding of a response into either a payload or a typed
    exception. `OutlineClient` and `AsyncOutlineClient` add only the transport.
    """

    url: str | None
    token: str | None
    timeout: float | tuple[float, float] | None

    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
        log: bool = False,
        timeout: float | tuple[float, float] | None = DEFAULT_TIMEOUT,
    ) -> None:
        """
        Resolve configuration, falling back to the `OUTLINE_API_*` environment.

        Args:
            url: The base URL of the API. A workspace URL is accepted and has
                `/api` appended. (Environment: `OUTLINE_API_URL`, default
                `https://app.getoutline.com/api`)
            token: The API token to authenticate with. Outline calls these
                API keys and they begin with `ol_api_`.
                (Environment: `OUTLINE_API_TOKEN`)
            log: Enables request logging at INFO level.
            timeout: Per-request timeout in seconds applied to every call.
        """
        if log:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.CRITICAL)

        self.url = url or os.environ.get("OUTLINE_API_URL") or DEFAULT_URL

        # An empty token is meaningful - it is how a caller says "send no
        # credential", for the methods Outline serves publicly - so only `None`
        # falls back to the environment.
        self.token = token if token is not None else os.environ.get("OUTLINE_API_TOKEN")
        self.timeout = timeout

    # -------------------------------------------------------------------------
    # METHOD: _endpoint
    # -------------------------------------------------------------------------

    def _endpoint(self, path: str) -> str:
        """
        Build the absolute URL for one API method.

        Returns:
            str: The URL to POST to, e.g. `https://…/api/documents.info`.
        """
        if not self.url:
            raise OutlineConfigurationError(
                "No Outline URL configured; pass url= or set OUTLINE_API_URL"
            )

        return f"{normalize_url(self.url)}/{path.lstrip('/')}"

    # -------------------------------------------------------------------------
    # METHOD: _headers
    # -------------------------------------------------------------------------

    def _headers(self, accept: str = "application/json") -> dict[str, str]:
        """
        Build the per-request headers, raising if no token was configured.

        The token is validated here rather than at construction so that a
        caller reading a public share, which Outline serves unauthenticated,
        is the only one who can opt out - by passing `token=""` deliberately.

        Returns:
            dict[str, str]: The headers for one request.
        """
        if self.token is None:
            raise OutlineConfigurationError(
                "No Outline API token configured; pass token= or set OUTLINE_API_TOKEN"
            )

        headers = {"Accept": accept}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        return headers

    # -------------------------------------------------------------------------
    # METHOD: _request_timeout
    # -------------------------------------------------------------------------

    def _request_timeout(self) -> httpx.Timeout | None:
        """
        Translate the configured timeout into the httpx representation.

        A `(connect, read)` pair carries over from the `requests` convention;
        the write and pool stages inherit the read and connect budgets
        respectively, since neither has a meaningful budget of its own here.

        Returns:
            httpx.Timeout | None: The per-request timeout, or None to disable.
        """
        timeout = self.timeout
        if timeout is None:
            return None
        if isinstance(timeout, tuple):
            connect, read = timeout
            return httpx.Timeout(connect=connect, read=read, write=read, pool=connect)

        return httpx.Timeout(timeout)

    # -------------------------------------------------------------------------
    # METHOD: _decode
    # -------------------------------------------------------------------------

    def _decode(self, response: httpx.Response) -> dict[str, Any]:
        """
        Raise on a failed call, and decode the JSON body of a successful one.

        Outline reports failure with the HTTP status, so unlike an envelope API
        the status alone settles it. The body is still read on failure: it
        carries the machine-readable `error` identifier and any validation
        detail, which is the part a caller can act on.

        Returns:
            dict[str, Any]: The decoded JSON response body.
        """
        if response.is_success:
            return self._decode_json(response)

        self._raise_for_status(response)

    # -------------------------------------------------------------------------
    # METHOD: _decode_json
    # -------------------------------------------------------------------------

    def _decode_json(self, response: httpx.Response) -> dict[str, Any]:
        """
        Decode a successful response body, which is always a JSON object.

        Returns:
            dict[str, Any]: The decoded JSON response body.
        """
        try:
            data: Any = json.loads(response.text)
        except ValueError as exc:
            raise error_for_status(response.status_code)(
                f"Expected a JSON response, got {response.text[:200]!r}",
                status=response.status_code,
                response=response,
            ) from exc

        if not isinstance(data, dict):
            raise error_for_status(response.status_code)(
                f"Expected a JSON object, got {type(data).__name__}",
                status=response.status_code,
                response=response,
            )

        return data

    # -------------------------------------------------------------------------
    # METHOD: _raise_for_status
    # -------------------------------------------------------------------------

    def _raise_for_status(self, response: httpx.Response) -> NoReturn:
        """
        Raise the exception that represents a failed response.

        Annotated `NoReturn`, so a caller that ends in this call is understood
        to end there and needs no unreachable return of its own.
        """
        payload: dict[str, Any] = {}
        try:
            decoded: Any = json.loads(response.text)
            if isinstance(decoded, dict):
                payload = decoded
        except ValueError:
            # An error from a proxy or load balancer in front of Outline may
            # not be JSON at all; the status still tells the caller what
            # happened, so the undecodable body is reported as the message.
            payload = {}

        message = payload.get("message") or payload.get("error") or response.text[:200]

        raise error_for_status(response.status_code)(
            str(message) or response.reason_phrase,
            status=response.status_code,
            error=payload.get("error"),
            data=payload.get("data"),
            response=response,
        )
