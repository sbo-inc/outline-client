"""
The CLI's client construction, which is where the environment is read.
"""

import pytest

from outline_client.cli.context import ClientContext


class TestClientContext:
    def test_builds_the_client_only_when_it_is_first_used(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # `outline --help` must not need a token.
        context = ClientContext()

        assert context._client is None

    def test_reuses_the_client_across_calls(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        context = ClientContext()

        assert context.client is context.client

    def test_reads_extra_headers_from_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OUTLINE_API_HEADERS", '{"X-Proxy": "yes"}')

        assert context_headers() == "yes"

    def test_reads_the_timeout_and_retry_count(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OUTLINE_API_TIMEOUT", "2.5")
        monkeypatch.setenv("OUTLINE_API_RETRIES", "3")

        client = ClientContext().client

        assert client.timeout == 2.5


def context_headers() -> str | None:
    """
    Build a client through the context and read one of its headers back.

    Returns:
        str | None: The value of the proxy header, if it was applied.
    """
    return ClientContext().client.http.headers.get("X-Proxy")
