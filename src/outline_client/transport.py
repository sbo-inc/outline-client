import json
import logging
import mimetypes
import os
import re
from email.message import Message
from email.utils import collapse_rfc2231_value
from pathlib import PurePosixPath
from typing import Any, NoReturn
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

import httpx

from outline_client.errors import (
    OutlineAPIError,
    OutlineConfigurationError,
    StorageError,
    error_for_status,
)
from outline_client.operations.generic import form_fields
from outline_client.schemas.models import Attachment
from outline_client.schemas.results import AttachmentDownload, AttachmentUpload

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
# FUNCTION: guess_content_type
# =============================================================================


def guess_content_type(name: str) -> str:
    """
    Guess a file's MIME type from its name.

    Returns:
        str: The type, or `application/octet-stream` if the name says nothing.
    """
    return mimetypes.guess_type(name)[0] or "application/octet-stream"


# =============================================================================
# FUNCTION: filename
# =============================================================================


def filename(disposition: str) -> str | None:
    """
    Read the file name from a `Content-Disposition` header.

    RFC 6266 has a recipient prefer `filename*`, which carries the name in
    full, over the ASCII fallback in `filename`; the standard library's own
    `get_filename` does the opposite, so the encoded parameter is looked for
    first.

    Returns:
        str | None: The file name, or None if the header does not give one.
    """
    message = Message()
    message["Content-Disposition"] = disposition
    for key, value in message.get_params(header="content-disposition") or []:
        if key == "filename" and isinstance(value, tuple):
            return collapse_rfc2231_value(value)

    return message.get_filename()


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
    # METHOD: _absolute
    # -------------------------------------------------------------------------

    def _absolute(self, url: str) -> str:
        """
        Resolve a URL Outline sent against the origin of the API.

        An absolute URL is returned as it is. A relative one is a path on
        Outline itself: with local file storage, an attachment's upload URL
        is `/api/files.create`.

        Returns:
            str: The absolute URL.
        """
        return urljoin(self._endpoint(""), url)

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

        A 204 has no body at all, and reads as an empty one: `shares.info`
        answers that way for a document that has no share.

        Returns:
            dict[str, Any]: The decoded JSON response body.
        """
        if response.status_code == httpx.codes.NO_CONTENT:
            return {}

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

    def _raise_for_status(
        self,
        response: httpx.Response,
        error: type[OutlineAPIError] | None = None,
    ) -> NoReturn:
        """
        Raise the exception that represents a failed response.

        `error` overrides the class chosen from the status, which is how a
        file store's refusal is raised as a `StorageError`.

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

        if not payload:
            # S3 and the services compatible with it answer in XML, with a
            # machine-readable code and a message of their own.
            code = re.search(r"<Code>(.*?)</Code>", response.text)
            if code:
                payload["error"] = code[1]
            text = re.search(r"<Message>(.*?)</Message>", response.text)
            if text:
                payload["message"] = text[1]

        message = payload.get("message") or payload.get("error") or response.text[:200]

        raise (error or error_for_status(response.status_code))(
            str(message) or response.reason_phrase,
            status=response.status_code,
            error=payload.get("error"),
            data=payload.get("data"),
            response=response,
        )

    # -------------------------------------------------------------------------
    # METHOD: _storage_request
    # -------------------------------------------------------------------------

    def _storage_request(
        self,
        upload: AttachmentUpload,
        content: bytes,
        *,
        name: str,
        content_type: str,
    ) -> dict[str, Any]:
        """
        Describe the request that sends an attachment's bytes to its file store.

        `put` mode is a PUT of the bytes to the presigned `url`, with the
        headers the signature covers. `post` mode, and any reply that predates
        the modes, is a multipart form to `upload_url`, the file last because
        S3 ignores any field after it.

        No API token is added: the store is a different origin, and the reply
        authorizes the upload on its own - by the presigned URL, the policy in
        the form, or with local storage a signature among the form fields.

        Returns:
            dict[str, Any]: The arguments for the HTTP client's `request`.
        """
        if upload.mode == "put":
            headers = {str(key): str(value) for key, value in upload.headers.items()}
            if not any(key.lower() == "content-type" for key in headers):
                headers["Content-Type"] = content_type
            return {
                "method": "PUT",
                "url": self._absolute(upload.url or ""),
                "content": content,
                "headers": headers,
                "timeout": self._request_timeout(),
            }

        return {
            "method": "POST",
            "url": self._absolute(upload.upload_url or ""),
            "data": form_fields(upload.form),
            "files": {"file": (name, content, content_type)},
            "timeout": self._request_timeout(),
        }

    # -------------------------------------------------------------------------
    # METHOD: _uploaded
    # -------------------------------------------------------------------------

    def _uploaded(
        self, upload: AttachmentUpload, response: httpx.Response
    ) -> Attachment:
        """
        Check the file store's answer to an upload, and return the attachment.

        Returns:
            Attachment: The attachment the upload slot was reserved for.
        """
        if not response.is_success:
            self._raise_for_status(response, StorageError)
        if upload.attachment is None:
            raise OutlineAPIError(
                "attachments.create answered without an attachment", status=200
            )

        return upload.attachment

    # -------------------------------------------------------------------------
    # METHOD: _attachment_download
    # -------------------------------------------------------------------------

    def _attachment_download(self, response: httpx.Response) -> AttachmentDownload:
        """
        Read an attachment's contents, name, and type from the store's response.

        The name comes from `Content-Disposition` when the store sends one,
        and otherwise from the last path segment of the URL the redirect led
        to, which is where S3 keeps an object's file name.

        Returns:
            AttachmentDownload: The contents with their name and type.
        """
        name = filename(response.headers.get("Content-Disposition", "")) or unquote(
            PurePosixPath(response.url.path).name
        )
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip()

        return AttachmentDownload(
            content=response.content,
            name=name or None,
            content_type=content_type or None,
        )
