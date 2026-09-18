"""
The command group, and the switch that hides commands from an embedded runtime.
"""

import click
import pytest
from click.testing import CliRunner

from outline_client.cli import cli


class TestCommandOrder:
    def test_lists_commands_in_registration_order(self) -> None:
        # Alphabetical order would bury `documents` in the middle; the help is
        # more useful with the common resources first.
        output = CliRunner().invoke(cli, ["--help"]).output
        names = [
            line.split()[0]
            for line in output.splitlines()
            if line.startswith("  ") and line.strip()
        ]

        assert names.index("documents") < names.index("collections")
        assert names.index("collections") < names.index("events")


class TestDisableSwitch:
    def test_hides_a_disabled_command_from_the_help(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OUTLINE_CLI_DISABLE", "documents.empty-trash")

        output = CliRunner().invoke(cli, ["documents", "--help"]).output

        assert "empty-trash" not in output

    def test_rejects_a_disabled_command_at_dispatch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OUTLINE_CLI_DISABLE", "documents.empty-trash")

        result = CliRunner().invoke(
            cli, ["documents", "empty-trash"], standalone_mode=False
        )

        assert result.exit_code != 0
        assert isinstance(result.exception, click.UsageError)

    def test_hides_a_whole_group(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OUTLINE_CLI_DISABLE", "api-keys")

        output = CliRunner().invoke(cli, ["--help"]).output

        assert "api-keys" not in output

    def test_leaves_everything_reachable_when_unset(self) -> None:
        output = CliRunner().invoke(cli, ["documents", "--help"]).output

        assert "empty-trash" in output
