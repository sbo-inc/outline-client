"""
How a failed call is reported.

Outline signals failure with the HTTP status and describes it in the body, so
the status picks the exception class and the body fills it in.
"""

from collections.abc import Callable

import httpx
import pytest
from conftest import failure, ok

from outline_client.client import OutlineClient
from outline_client.errors import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    OutlineAPIError,
    PaymentRequiredError,
    RateLimitError,
    ServerError,
    ValidationError,
)

type ClientFactory = Callable[..., OutlineClient]


def responding(response: httpx.Response) -> Callable[[httpx.Request], httpx.Response]:
    """
    Build a handler that answers every call with the same response.

    Returns:
        Callable[[httpx.Request], httpx.Response]: The handler.
    """
    return lambda request: response


# =============================================================================
# TESTS: Status to exception
# =============================================================================


class TestStatusMapping:
    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (400, ValidationError),
            (401, AuthenticationError),
            (402, PaymentRequiredError),
            (403, AuthorizationError),
            (404, NotFoundError),
            (429, RateLimitError),
            (500, ServerError),
            (503, ServerError),
        ],
    )
    def test_each_documented_status_raises_its_own_class(
        self, make_client: ClientFactory, status: int, expected: type[OutlineAPIError]
    ) -> None:
        client = make_client(responding(failure(status=status)))

        with pytest.raises(expected):
            client.get_auth_info()

    def test_an_undocumented_status_falls_back_to_the_base_class(
        self, make_client: ClientFactory
    ) -> None:
        client = make_client(responding(failure(status=418)))

        with pytest.raises(OutlineAPIError) as caught:
            client.get_auth_info()

        assert type(caught.value) is OutlineAPIError
        assert caught.value.status == 418


# =============================================================================
# TESTS: Error detail
# =============================================================================


class TestErrorDetail:
    def test_carries_outlines_own_description_of_the_failure(
        self, make_client: ClientFactory
    ) -> None:
        client = make_client(
            responding(
                failure(status=404, error="not_found", message="Resource not found")
            )
        )

        with pytest.raises(NotFoundError) as caught:
            client.get_document("missing")

        assert caught.value.status == 404
        assert caught.value.error == "not_found"
        assert caught.value.message == "Resource not found"
        assert "Resource not found" in str(caught.value)

    def test_survives_a_body_that_is_not_outlines(
        self, make_client: ClientFactory
    ) -> None:
        # A proxy in front of Outline can answer with HTML; the status is still
        # the useful half, so the call must fail the same way.
        client = make_client(
            responding(httpx.Response(502, text="<h1>Bad gateway</h1>"))
        )

        with pytest.raises(ServerError) as caught:
            client.get_auth_info()

        assert caught.value.status == 502
        assert caught.value.error is None

    def test_a_success_that_is_not_json_is_reported_rather_than_parsed(
        self, make_client: ClientFactory
    ) -> None:
        client = make_client(responding(httpx.Response(200, text="not json")))

        with pytest.raises(OutlineAPIError, match="JSON"):
            client.get_auth_info()


# =============================================================================
# TESTS: Rate limiting
# =============================================================================


class TestRateLimit:
    def test_reports_the_wait_outline_asks_for(
        self, make_client: ClientFactory
    ) -> None:
        response = httpx.Response(
            429,
            json={"ok": False, "error": "rate_limit_exceeded", "status": 429},
            headers={"Retry-After": "30"},
        )
        client = make_client(responding(response))

        with pytest.raises(RateLimitError) as caught:
            client.get_auth_info()

        assert caught.value.retry_after == 30.0

    def test_has_no_wait_when_outline_does_not_send_one(
        self, make_client: ClientFactory
    ) -> None:
        client = make_client(responding(failure(status=429)))

        with pytest.raises(RateLimitError) as caught:
            client.get_auth_info()

        assert caught.value.retry_after is None

    def test_has_no_wait_when_the_header_is_a_date(
        self, make_client: ClientFactory
    ) -> None:
        # `Retry-After` may also be an HTTP date, which is not a delay this
        # client converts; the caller can read the header off the response.
        response = httpx.Response(
            429,
            json={"ok": False, "error": "rate_limit_exceeded"},
            headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"},
        )
        client = make_client(responding(response))

        with pytest.raises(RateLimitError) as caught:
            client.get_auth_info()

        assert caught.value.retry_after is None
        assert caught.value.response is not None


# =============================================================================
# TESTS: Success
# =============================================================================


class TestSuccess:
    def test_a_2xx_is_decoded_rather_than_raised(
        self, make_client: ClientFactory
    ) -> None:
        client = make_client(responding(ok({"user": {"name": "Ada"}, "team": {}})))

        assert client.get_auth_info().user.name == "Ada"
