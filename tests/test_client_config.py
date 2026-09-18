"""
Configuration, and the checks that happen before a request is built.
"""

from collections.abc import Callable

import httpx
import pytest
from conftest import TOKEN, URL, ok

from outline_client.client import OutlineClient
from outline_client.errors import OutlineConfigurationError
from outline_client.transport import DEFAULT_URL, normalize_url

AUTH_INFO = {"user": {"name": "Ada"}, "team": {"name": "Example"}}


# =============================================================================
# TESTS: URL normalization
# =============================================================================


class TestNormalizeUrl:
    def test_appends_the_api_prefix_to_a_workspace_url(self) -> None:
        assert (
            normalize_url("https://wiki.example.com") == "https://wiki.example.com/api"
        )

    def test_leaves_an_api_url_alone(self) -> None:
        assert (
            normalize_url("https://wiki.example.com/api")
            == "https://wiki.example.com/api"
        )

    def test_ignores_a_trailing_slash(self) -> None:
        assert (
            normalize_url("https://wiki.example.com/") == "https://wiki.example.com/api"
        )
        assert (
            normalize_url("https://wiki.example.com/api/")
            == "https://wiki.example.com/api"
        )

    def test_trusts_any_other_path_as_given(self) -> None:
        # An installation behind a proxy that remounts the API is not
        # second-guessed.
        assert (
            normalize_url("https://example.com/wiki/api")
            == "https://example.com/wiki/api"
        )

    def test_drops_a_query_string(self) -> None:
        assert (
            normalize_url("https://wiki.example.com/api?x=1")
            == "https://wiki.example.com/api"
        )

    @pytest.mark.parametrize("value", ["", "wiki.example.com", "/api", "not a url"])
    def test_rejects_a_url_that_is_not_absolute(self, value: str) -> None:
        with pytest.raises(OutlineConfigurationError):
            normalize_url(value)


# =============================================================================
# TESTS: Configuration
# =============================================================================


class TestConfiguration:
    def test_defaults_to_the_cloud_host(self) -> None:
        assert OutlineClient().url == DEFAULT_URL

    def test_reads_the_environment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OUTLINE_API_URL", "https://wiki.example.com")
        monkeypatch.setenv("OUTLINE_API_TOKEN", TOKEN)

        client = OutlineClient()

        assert client.url == "https://wiki.example.com"
        assert client.token == TOKEN

    def test_arguments_win_over_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OUTLINE_API_TOKEN", "from-environment")

        assert OutlineClient(token=TOKEN).token == TOKEN

    def test_a_missing_token_is_reported_on_use_not_on_construction(self) -> None:
        # Building a client to read its defaults must not fail; the check
        # belongs at the point the credential is actually needed.
        client = OutlineClient(url=URL)

        with pytest.raises(OutlineConfigurationError, match="token"):
            client.get_auth_info()

    def test_an_empty_token_is_taken_as_deliberate(self) -> None:
        # Outline serves public shares unauthenticated, so `token=""` opts out
        # of the Authorization header rather than being rejected as unset.
        client = OutlineClient(url=URL, token="")

        assert "Authorization" not in client._headers()

    def test_builds_the_endpoint_for_a_method(self) -> None:
        client = OutlineClient(url="https://wiki.example.com", token=TOKEN)

        assert client._endpoint("documents.info") == (
            "https://wiki.example.com/api/documents.info"
        )


# =============================================================================
# TESTS: Timeouts
# =============================================================================


class TestRequestTimeout:
    def test_translates_a_connect_read_pair(self) -> None:
        timeout = OutlineClient(timeout=(1.0, 2.0))._request_timeout()

        assert timeout is not None
        assert timeout.connect == 1.0
        assert timeout.read == 2.0
        # The write and pool stages have no budget of their own here, so they
        # inherit the read and connect budgets respectively.
        assert timeout.write == 2.0
        assert timeout.pool == 1.0

    def test_translates_a_single_value(self) -> None:
        timeout = OutlineClient(timeout=5.0)._request_timeout()

        assert timeout is not None
        assert timeout.read == 5.0

    def test_none_disables_the_timeout(self) -> None:
        assert OutlineClient(timeout=None)._request_timeout() is None


# =============================================================================
# TESTS: Headers and lifecycle
# =============================================================================


class TestHeaders:
    def test_sends_the_token_as_a_bearer_credential(
        self, make_client: Callable[..., OutlineClient]
    ) -> None:
        seen: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(request.headers)
            return ok(AUTH_INFO)

        make_client(handler).get_auth_info()

        assert seen["authorization"] == f"Bearer {TOKEN}"
        assert seen["accept"] == "application/json"
        # httpx derives the content type from the body, which is what lets the
        # one multipart method work without fighting a client-wide default.
        assert seen["content-type"] == "application/json"

    def test_extra_headers_are_merged(
        self, make_client: Callable[..., OutlineClient]
    ) -> None:
        seen: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(request.headers)
            return ok(AUTH_INFO)

        make_client(handler, headers={"X-Proxy": "yes"}).get_auth_info()

        assert seen["x-proxy"] == "yes"


class TestContextManager:
    def test_closes_the_transport_on_exit(
        self, make_client: Callable[..., OutlineClient]
    ) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return ok(AUTH_INFO)

        with make_client(handler) as client:
            client.get_auth_info()

        assert client.http.is_closed
