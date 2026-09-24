import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import clear_option, clearable, pagination_options
from outline_client.cli.output import render


@click.group(name="oauth", cls=CommonClickGroup)
def group() -> None:
    """
    Manage OAuth applications and the grants users have given them.
    """


@group.command(name="list")
@pagination_options
@click.pass_obj
def list_(ctx: ClientContext, offset: int | None, limit: int | None) -> None:
    """
    List the OAuth applications registered in the workspace.
    """
    render(ctx.client.list_oauth_clients(offset=offset, limit=limit))


@group.command(name="get")
@click.argument("oauth_client_id", required=False)
@click.option("--client-id", default=None, help="Look up by OAuth client id instead.")
@click.pass_obj
def get(ctx: ClientContext, oauth_client_id: str | None, client_id: str | None) -> None:
    """
    Show one OAuth application.
    """
    render(ctx.client.get_oauth_client(oauth_client_id, client_id=client_id))


@group.command(name="create")
@click.argument("name")
@click.option(
    "--redirect-uri", required=True, multiple=True, help="Redirect URI (repeatable)."
)
@click.option("--description", default=None, help="What the application does.")
@click.option("--developer-name", default=None, help="Who publishes it.")
@click.option("--developer-url", default=None, help="Where to find out more.")
@click.option("--avatar-url", default=None, help="Icon for the application.")
@click.option("--published", is_flag=True, help="List it for the whole workspace.")
@click.pass_obj
def create(
    ctx: ClientContext,
    name: str,
    redirect_uri: tuple[str, ...],
    description: str | None,
    developer_name: str | None,
    developer_url: str | None,
    avatar_url: str | None,
    published: bool,
) -> None:
    """
    Register an OAuth application.

    This is the only time the client secret is shown in full.
    """
    render(
        ctx.client.create_oauth_client(
            name,
            list(redirect_uri),
            description=description,
            developer_name=developer_name,
            developer_url=developer_url,
            avatar_url=avatar_url,
            published=published or None,
        )
    )


@group.command(name="update")
@click.argument("oauth_client_id")
@click.option("--name", default=None, help="New name.")
@click.option(
    "--redirect-uri", multiple=True, help="Replacement redirect URIs (repeatable)."
)
@click.option("--description", default=None, help="New description.")
@click.option("--developer-name", default=None, help="New publisher name.")
@click.option("--developer-url", default=None, help="New publisher URL.")
@click.option("--avatar-url", default=None, help="New icon.")
@click.option(
    "--published/--unpublished", default=None, help="List it for the workspace."
)
@clear_option("description", "developer-name", "developer-url", "avatar-url")
@click.pass_obj
def update(
    ctx: ClientContext,
    oauth_client_id: str,
    name: str | None,
    redirect_uri: tuple[str, ...],
    description: str | None,
    developer_name: str | None,
    developer_url: str | None,
    avatar_url: str | None,
    published: bool | None,
    clear: tuple[str, ...],
) -> None:
    """
    Update an OAuth application.
    """
    render(
        ctx.client.update_oauth_client(
            oauth_client_id,
            name=name,
            redirect_uris=list(redirect_uri) or None,
            description=clearable(description, "description", clear),
            developer_name=clearable(developer_name, "developer-name", clear),
            developer_url=clearable(developer_url, "developer-url", clear),
            avatar_url=clearable(avatar_url, "avatar-url", clear),
            published=published,
        )
    )


@group.command(name="rotate-secret")
@click.argument("oauth_client_id")
@click.confirmation_option(prompt="Issue a new secret, invalidating the old one?")
@click.pass_obj
def rotate_secret(ctx: ClientContext, oauth_client_id: str) -> None:
    """
    Issue a new secret for an OAuth application.
    """
    render(ctx.client.rotate_oauth_client_secret(oauth_client_id))


@group.command(name="delete")
@click.argument("oauth_client_id")
@click.confirmation_option(prompt="Delete this application and revoke its grants?")
@click.pass_obj
def delete(ctx: ClientContext, oauth_client_id: str) -> None:
    """
    Delete an OAuth application and revoke the grants it holds.
    """
    render(ctx.client.delete_oauth_client(oauth_client_id))


@group.command(name="authentications")
@pagination_options
@click.pass_obj
def authentications(ctx: ClientContext, offset: int | None, limit: int | None) -> None:
    """
    List the OAuth applications you have authorized.
    """
    render(ctx.client.list_oauth_authentications(offset=offset, limit=limit))


@group.command(name="revoke")
@click.argument("oauth_client_id")
@click.option("--scope", multiple=True, help="Revoke only these scopes (repeatable).")
@click.pass_obj
def revoke(ctx: ClientContext, oauth_client_id: str, scope: tuple[str, ...]) -> None:
    """
    Revoke an OAuth application's access, in whole or by scope.
    """
    render(
        ctx.client.delete_oauth_authentication(
            oauth_client_id, scope=list(scope) or None
        )
    )
