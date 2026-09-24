"""
The CLI, driven through Click's runner against a mocked transport.

The commands are thin, so what is worth asserting is the translation either
side of them: options into client arguments, and results into stdout.
"""

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from click.testing import CliRunner
from conftest import DOCUMENT_ID, TOKEN, URL, body, ok

from outline_client.cli import cli
from outline_client.cli.context import ClientContext

DOCUMENT: dict[str, Any] = {
    "id": DOCUMENT_ID,
    "title": "Onboarding",
    "url": "/doc/onboarding-hDYep1TPAM",
}

type Handler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture
def run(
    monkeypatch: pytest.MonkeyPatch, make_client: Callable[..., Any]
) -> Callable[..., Any]:
    """
    Return a runner that invokes the CLI against a mocked transport.

    Returns:
        Callable[..., Any]: The runner.
    """

    def invoke(handler: Handler, args: list[str], **kwargs: Any) -> Any:
        monkeypatch.setenv("OUTLINE_API_URL", URL)
        monkeypatch.setenv("OUTLINE_API_TOKEN", TOKEN)
        monkeypatch.setattr(
            ClientContext, "client", property(lambda self: make_client(handler))
        )

        return CliRunner().invoke(cli, args, standalone_mode=False, **kwargs)

    return invoke


# =============================================================================
# TESTS: Options to arguments
# =============================================================================


class TestOptionTranslation:
    def test_passes_only_the_options_that_were_given(
        self, run: Callable[..., Any]
    ) -> None:
        seen: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(body(request))
            return ok(DOCUMENT)

        result = run(
            handler, ["documents", "create", "--title", "Onboarding", "--publish"]
        )

        assert result.exit_code == 0
        assert seen == {"title": "Onboarding", "publish": True}

    def test_a_flag_left_off_is_omitted_rather_than_sent_as_false(
        self, run: Callable[..., Any]
    ) -> None:
        # Sending `publish: false` would be a different request from not
        # mentioning publishing at all.
        seen: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(body(request))
            return ok(DOCUMENT)

        run(handler, ["documents", "create", "--title", "Onboarding"])

        assert "publish" not in seen

    def test_decodes_a_json_option(self, run: Callable[..., Any]) -> None:
        seen: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(body(request))
            return ok([DOCUMENT])

        filters = '[{"field": "title", "operator": "contains", "value": "board"}]'
        result = run(handler, ["documents", "list", "--filters", filters])

        assert result.exit_code == 0
        assert seen["filters"] == json.loads(filters)

    def test_rejects_a_malformed_json_option_as_a_usage_error(
        self, run: Callable[..., Any]
    ) -> None:
        result = run(
            lambda request: ok([]), ["documents", "list", "--filters", "{oops"]
        )

        assert result.exit_code != 0
        assert "JSON" in str(result.exception)

    def test_reads_the_body_from_a_file(
        self, run: Callable[..., Any], tmp_path: Any
    ) -> None:
        source = tmp_path / "body.md"
        source.write_text("# Welcome")
        seen: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(body(request))
            return ok(DOCUMENT)

        run(
            handler, ["documents", "create", "--title", "X", "--text-file", str(source)]
        )

        assert seen["text"] == "# Welcome"

    def test_refuses_both_text_and_a_file(self, run: Callable[..., Any]) -> None:
        result = run(
            lambda request: ok(DOCUMENT),
            ["documents", "create", "--text", "x", "--text-file", "-"],
        )

        assert result.exit_code != 0


# =============================================================================
# TESTS: Results to stdout
# =============================================================================


class TestOutput:
    def test_prints_a_model_as_indented_json(self, run: Callable[..., Any]) -> None:
        result = run(lambda request: ok(DOCUMENT), ["documents", "get", DOCUMENT_ID])

        assert result.exit_code == 0
        assert json.loads(result.output)["title"] == "Onboarding"

    def test_prints_a_list_as_json(self, run: Callable[..., Any]) -> None:
        result = run(lambda request: ok([DOCUMENT, DOCUMENT]), ["documents", "list"])

        assert len(json.loads(result.output)) == 2

    def test_echoes_a_string_result_verbatim(self, run: Callable[..., Any]) -> None:
        # An export is redirected to a file far more often than it is read, so
        # quoting it as JSON would only get in the way.
        result = run(
            lambda request: ok("# Welcome"), ["documents", "export", DOCUMENT_ID]
        )

        assert result.output == "# Welcome\n"

    def test_reports_an_acknowledgement_in_words(self, run: Callable[..., Any]) -> None:
        response = httpx.Response(200, json={"success": True, "ok": True})

        result = run(lambda request: response, ["documents", "delete", DOCUMENT_ID])

        assert result.output.strip() == "ok"

    def test_writes_a_download_to_a_path(
        self, run: Callable[..., Any], tmp_path: Any
    ) -> None:
        target = tmp_path / "out.html"
        response = httpx.Response(200, content=b"<html></html>")

        result = run(
            lambda request: response,
            [
                "documents",
                "export",
                DOCUMENT_ID,
                "--accept",
                "text/html",
                "-o",
                str(target),
            ],
        )

        assert result.exit_code == 0
        assert target.read_bytes() == b"<html></html>"


# =============================================================================
# TESTS: Clearing a field
# =============================================================================


class TestClear:
    def test_an_option_left_off_is_not_sent_as_null(
        self, run: Callable[..., Any]
    ) -> None:
        # The client sends `None` as null on these fields, so the CLI must
        # not hand it an unset option as `None`.
        seen: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(body(request))
            return ok(DOCUMENT)

        run(handler, ["documents", "update", DOCUMENT_ID, "--title", "Renamed"])

        assert seen == {"id": DOCUMENT_ID, "title": "Renamed"}

    def test_clear_sends_the_field_as_null(self, run: Callable[..., Any]) -> None:
        seen: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(body(request))
            return ok(DOCUMENT)

        result = run(
            handler,
            ["documents", "update", DOCUMENT_ID, "--clear", "icon", "--clear", "color"],
        )

        assert result.exit_code == 0
        assert seen == {"id": DOCUMENT_ID, "icon": None, "color": None}

    def test_refuses_a_value_and_a_clear_for_one_field(
        self, run: Callable[..., Any]
    ) -> None:
        result = run(
            lambda request: ok(DOCUMENT),
            ["documents", "update", DOCUMENT_ID, "--icon", "x", "--clear", "icon"],
        )

        assert result.exit_code != 0
