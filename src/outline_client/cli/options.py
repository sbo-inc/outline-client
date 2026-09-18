"""
Option decorators shared by the command modules.

The API's `list` methods take the same paging and ordering arguments
throughout, so the options for them are declared once here rather than spelled
out on each of the forty-odd commands that accept them.
"""

import json
from collections.abc import Callable
from typing import Any

import click

# =============================================================================
# FUNCTION: pagination_options
# =============================================================================


def pagination_options[F: Callable[..., Any]](func: F) -> F:
    """
    Add the `--offset` and `--limit` options every list method accepts.

    Returns:
        F: The decorated command.
    """
    func = click.option(
        "--limit",
        type=int,
        default=None,
        help="How many records to return.",
    )(func)

    return click.option(
        "--offset",
        type=int,
        default=None,
        help="How many records to skip.",
    )(func)


# =============================================================================
# FUNCTION: sorting_options
# =============================================================================


def sorting_options[F: Callable[..., Any]](func: F) -> F:
    """
    Add the `--sort` and `--direction` options the ordered list methods accept.

    Returns:
        F: The decorated command.
    """
    func = click.option(
        "--direction",
        type=click.Choice(["ASC", "DESC"], case_sensitive=False),
        default=None,
        help="Sort direction.",
    )(func)

    return click.option(
        "--sort",
        type=str,
        default=None,
        help="Field to order by, e.g. updatedAt.",
    )(func)


# =============================================================================
# FUNCTION: permission_option
# =============================================================================


def permission_option[F: Callable[..., Any]](func: F) -> F:
    """
    Add the `--permission` option the membership methods accept.

    Returns:
        F: The decorated command.
    """
    return click.option(
        "--permission",
        type=click.Choice(["read", "read_write", "admin"]),
        default=None,
        help="Access level to grant.",
    )(func)


# =============================================================================
# FUNCTION: parse_json
# =============================================================================


def parse_json(value: str | None) -> Any:
    """
    Decode an option whose value is a JSON document.

    The rich-text bodies and the structured filter expressions have no sensible
    flat spelling on a command line, so they are passed as JSON and decoded
    here. A malformed document is reported as a usage error rather than a
    traceback.

    Returns:
        Any: The decoded value, or None if the option was not given.
    """
    if value is None:
        return None

    try:
        return json.loads(value)
    except ValueError as exc:
        raise click.BadParameter(f"expected a JSON document: {exc}") from exc
