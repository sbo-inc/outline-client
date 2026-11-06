"""
The package's logging follows the library pattern.

Importing attaches only a NullHandler, building a client never touches levels
or handlers, and only the CLI's `--log` configures output.
"""

import logging
import subprocess
import sys
from collections.abc import Callable, Iterator

import httpx
import pytest
from conftest import ok

from outline_client.async_client import AsyncOutlineClient
from outline_client.cli import LOG_HANDLER_NAME, enable_logging
from outline_client.client import OutlineClient

PACKAGE = logging.getLogger("outline_client")


@pytest.fixture(autouse=True)
def restore_logger() -> Iterator[None]:
    """
    Undo any handler or level a test leaves on the package logger.
    """
    handlers, level = list(PACKAGE.handlers), PACKAGE.level
    yield
    PACKAGE.handlers[:] = handlers
    PACKAGE.setLevel(level)


def test_import_attaches_only_a_null_handler() -> None:
    # A fresh interpreter, so no earlier test has touched the logger.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import logging, outline_client;"
            "logger = logging.getLogger('outline_client');"
            "print([type(h).__name__ for h in logger.handlers], logger.level)",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == "['NullHandler'] 0"


def test_building_clients_leaves_the_logger_alone() -> None:
    PACKAGE.setLevel(logging.DEBUG)
    handlers = list(PACKAGE.handlers)

    OutlineClient(url="https://example.test/api", token="t")
    AsyncOutlineClient(url="https://example.test/api", token="t")

    assert PACKAGE.level == logging.DEBUG
    assert PACKAGE.handlers == handlers


def test_requests_log_at_debug_and_print_nothing_unconfigured(
    make_client: Callable[..., OutlineClient],
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return ok({"user": {}, "team": {}})

    with caplog.at_level(logging.DEBUG, logger="outline_client"):
        make_client(handler).get_auth_info()

    assert [
        r.levelname for r in caplog.records if r.getMessage().startswith("POST ")
    ] == ["DEBUG"]
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_cli_logging_replaces_its_own_handler() -> None:
    enable_logging()
    enable_logging()

    named = [h for h in PACKAGE.handlers if h.get_name() == LOG_HANDLER_NAME]
    assert len(named) == 1
    assert PACKAGE.level == logging.DEBUG
