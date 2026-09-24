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

from outline_client.not_given import NOT_GIVEN, NotGiven

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


# =============================================================================
# FUNCTION: clear_option
# =============================================================================


def clear_option[F: Callable[..., Any]](*fields: str) -> Callable[[F], F]:
    """
    Add the `--clear` option for the fields a command can send as null.

    Outline clears a field sent as JSON null, which no other option can spell:
    an option left off is not sent at all. `--clear icon` sends the null, and
    the option repeats.

    Returns:
        Callable[[F], F]: The decorator.
    """

    def decorate(func: F) -> F:
        return click.option(
            "--clear",
            multiple=True,
            type=click.Choice(fields),
            help="Clear a field, sending it as null. Repeatable.",
        )(func)

    return decorate


# =============================================================================
# FUNCTION: clearable
# =============================================================================


def clearable[T](
    value: T | None, field: str, clear: tuple[str, ...]
) -> T | None | NotGiven:
    """
    Resolve a nullable option to the argument its client method takes.

    A value given is passed on. A field named by `--clear` becomes `None`,
    which the client sends as null, and an option left off becomes
    `NOT_GIVEN`, which the client leaves out. Giving a field a value and
    clearing it too is a usage error.

    Returns:
        T | None | NotGiven: The argument to pass.
    """
    if field in clear:
        if value is not None:
            raise click.UsageError(f"pass --{field} or --clear {field}, not both")
        return None

    return NOT_GIVEN if value is None else value
