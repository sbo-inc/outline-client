"""
The exceptions this client raises.

Every failed API call raises an `OutlineAPIError` carrying the status code and
the decoded error body. Subclasses exist for the statuses Outline documents, so
a caller can catch the one case it knows how to handle - a missing record, a
revoked key, a rate limit - without matching on a number.
"""

from typing import Any

import httpx

# =============================================================================
# CLASS: OutlineError
# =============================================================================


class OutlineError(Exception):
    """
    Base class for every error raised by this package.
    """


# =============================================================================
# CLASS: OutlineConfigurationError
# =============================================================================


class OutlineConfigurationError(OutlineError):
    """
    Raised when the client is missing the URL or token it needs to make a call.

    Configuration is checked on use rather than on construction, so building a
    client to read its defaults never fails.
    """


# =============================================================================
# CLASS: OutlineAPIError
# =============================================================================


class OutlineAPIError(OutlineError):
    """
    Raised when Outline answers a call with an error status.

    The message is Outline's own, which is written for a person; `error` is its
    machine-readable counterpart (`authentication_required`, `not_found`) and
    is the stable thing to branch on when the subclass is not specific enough.
    """

    def __init__(
        self,
        message: str,
        *,
        status: int,
        error: str | None = None,
        data: dict[str, Any] | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        """
        Build the error from Outline's response.

        Args:
            message: Outline's human-readable description of the failure.
            status: The HTTP status code the call was answered with.
            error: Outline's machine-readable error identifier, if it sent one.
            data: Any structured detail accompanying the error.
            response: The response itself, for headers such as `Retry-After`.
        """
        super().__init__(f"{status} {error or 'error'}: {message}")

        self.message = message
        self.status = status
        self.error = error
        self.data = data or {}
        self.response = response


# =============================================================================
# CLASS: ValidationError
# =============================================================================


class ValidationError(OutlineAPIError):
    """
    Raised on HTTP 400: the request failed one or more of Outline's validations.
    """


# =============================================================================
# CLASS: AuthenticationError
# =============================================================================


class AuthenticationError(OutlineAPIError):
    """
    Raised on HTTP 401: the API token is missing, malformed, or revoked.
    """


# =============================================================================
# CLASS: PaymentRequiredError
# =============================================================================


class PaymentRequiredError(OutlineAPIError):
    """
    Raised on HTTP 402: the feature is not available on this installation.

    Outline gates parts of the API by edition - PDF export and the AI answer
    methods among them - and reports the gate with this status rather than by
    hiding the method.
    """


# =============================================================================
# CLASS: AuthorizationError
# =============================================================================


class AuthorizationError(OutlineAPIError):
    """
    Raised on HTTP 403: the token is valid but not permitted this action.

    A token scoped to `read` hitting a write method lands here, as does a user
    acting outside the permissions their workspace role grants.
    """


# =============================================================================
# CLASS: NotFoundError
# =============================================================================


class NotFoundError(OutlineAPIError):
    """
    Raised on HTTP 404: the requested record does not exist, or is not visible.

    Outline does not distinguish the two - a document the caller may not read
    is reported as absent rather than forbidden, so that the API does not
    confirm its existence.
    """


# =============================================================================
# CLASS: RateLimitError
# =============================================================================


class RateLimitError(OutlineAPIError):
    """
    Raised on HTTP 429: too many requests were made in the rate-limit window.

    `retry_after` is the number of seconds Outline asks the caller to wait,
    taken from the `Retry-After` header. It is `None` if the header was absent.
    """

    @property
    def retry_after(self) -> float | None:
        """
        The wait Outline asks for before the call is retried, in seconds.

        Returns:
            float | None: The retry delay, or None if it was not reported.
        """
        if self.response is None:
            return None

        header = self.response.headers.get("Retry-After")
        if not header:
            return None

        try:
            return float(header)
        except ValueError:
            # The header may also be an HTTP date, which is not a wait this
            # client is prepared to convert; the caller can read the header.
            return None


# =============================================================================
# CLASS: ServerError
# =============================================================================


class ServerError(OutlineAPIError):
    """
    Raised on HTTP 5xx: the request failed inside Outline rather than at its edge.
    """


# =============================================================================
# CLASS: StorageError
# =============================================================================


class StorageError(OutlineAPIError):
    """
    Raised when the file store refuses an attachment's upload.

    The bytes go to the file store directly rather than through Outline's API:
    to S3 or a compatible service, or to Outline itself with local storage. A
    failure there is not one of the API's own, so it has this one class, and
    `status` is the store's status code rather than Outline's.
    """


# =============================================================================
# CONSTANT: STATUS_ERRORS
# =============================================================================
#
# Statuses the specification documents, mapped to the exception each raises.
# Anything else falls back to `OutlineAPIError`, or `ServerError` for 5xx.

STATUS_ERRORS: dict[int, type[OutlineAPIError]] = {
    400: ValidationError,
    401: AuthenticationError,
    402: PaymentRequiredError,
    403: AuthorizationError,
    404: NotFoundError,
    429: RateLimitError,
}


# =============================================================================
# FUNCTION: error_for_status
# =============================================================================


def error_for_status(status: int) -> type[OutlineAPIError]:
    """
    Select the exception class that represents a status code.

    Returns:
        type[OutlineAPIError]: The exception class to raise.
    """
    if status in STATUS_ERRORS:
        return STATUS_ERRORS[status]
    if status >= 500:
        return ServerError

    return OutlineAPIError
