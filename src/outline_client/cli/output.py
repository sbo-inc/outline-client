import json
import sys
from collections.abc import Sequence
from typing import Any

import click
from pydantic import BaseModel

type Renderable = BaseModel | Sequence[BaseModel] | dict[str, Any] | str | bool | None

# =============================================================================
# FUNCTION: render
# =============================================================================


def render(value: Renderable, *, exclude: set[str] | None = None) -> None:
    """
    Print a command's result to stdout.

    Models and lists of models are serialized as indented JSON, so the output
    pipes into `jq` unchanged. A bare string - a document export, an attachment
    URL - is echoed as-is, because wrapping it in quotes would only get in the
    way of redirecting it to a file.

    `exclude` drops the named top-level fields, which is how a newly created
    API key's secret is kept out of a log.
    """
    if value is None:
        return
    if isinstance(value, str):
        click.echo(value)
        return
    if isinstance(value, bool):
        click.echo("ok" if value else "failed")
        return

    payload: object
    if isinstance(value, BaseModel):
        payload = value.model_dump(mode="json", exclude=exclude)
    elif isinstance(value, dict):
        payload = value
    else:
        payload = [item.model_dump(mode="json", exclude=exclude) for item in value]

    click.echo(json.dumps(payload, indent=2, default=str))


# =============================================================================
# FUNCTION: write_bytes
# =============================================================================


def write_bytes(content: bytes, output: str | None) -> None:
    """
    Write a downloaded file to a path, or to stdout when none is given.

    Stdout is written through the buffer rather than `click.echo` so that a
    PDF or a zip survives being redirected.
    """
    if output:
        with open(output, "wb") as handle:
            handle.write(content)
        click.echo(f"Wrote {len(content)} bytes to {output}", err=True)
        return

    sys.stdout.buffer.write(content)
