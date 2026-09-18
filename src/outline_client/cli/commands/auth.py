import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.output import render


@click.group(name="auth", cls=CommonClickGroup)
def group() -> None:
    """
    Inspect the credentials the CLI is using.
    """


@group.command(name="info")
@click.pass_obj
def info(ctx: ClientContext) -> None:
    """
    Show the user and workspace the API token belongs to.
    """
    render(ctx.client.get_auth_info())


@group.command(name="config")
@click.pass_obj
def config(ctx: ClientContext) -> None:
    """
    Show the workspace's sign-in configuration.
    """
    render(ctx.client.get_auth_config())


@group.command(name="sign-out")
@click.confirmation_option(prompt="Sign out, invalidating the current session?")
@click.pass_obj
def sign_out(ctx: ClientContext) -> None:
    """
    Sign out, invalidating the session behind the current credentials.
    """
    render(ctx.client.sign_out())
