import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import pagination_options, parse_json, sorting_options
from outline_client.cli.output import render


@click.group(name="comments", cls=CommonClickGroup)
def group() -> None:
    """
    Read and write comments and their reactions.
    """


@group.command(name="list")
@click.option("--document-id", default=None, help="Limit to one document.")
@click.option("--collection-id", default=None, help="Limit to one collection.")
@click.option("--anchor-text", is_flag=True, help="Include the anchored passages.")
@pagination_options
@sorting_options
@click.pass_obj
def list_(
    ctx: ClientContext,
    document_id: str | None,
    collection_id: str | None,
    anchor_text: bool,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List comments on a document or across a collection.
    """
    render(
        ctx.client.list_comments(
            document_id=document_id,
            collection_id=collection_id,
            include_anchor_text=anchor_text or None,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        )
    )


@group.command(name="get")
@click.argument("comment_id")
@click.option("--anchor-text", is_flag=True, help="Include the anchored passage.")
@click.pass_obj
def get(ctx: ClientContext, comment_id: str, anchor_text: bool) -> None:
    """
    Show one comment.
    """
    render(ctx.client.get_comment(comment_id, include_anchor_text=anchor_text or None))


@group.command(name="create")
@click.argument("document_id")
@click.option("--text", default=None, help="Comment body, as markdown.")
@click.option(
    "--data", default=None, help="Comment body as a rich-text document, as JSON."
)
@click.option("--parent-comment-id", default=None, help="Reply to this comment.")
@click.option("--anchor-text", default=None, help="Passage to attach the comment to.")
@click.pass_obj
def create(
    ctx: ClientContext,
    document_id: str,
    text: str | None,
    data: str | None,
    parent_comment_id: str | None,
    anchor_text: str | None,
) -> None:
    """
    Comment on a document, or reply to an existing comment.
    """
    render(
        ctx.client.create_comment(
            document_id,
            text=text,
            data=parse_json(data),
            parent_comment_id=parent_comment_id,
            anchor_text=anchor_text,
        )
    )


@group.command(name="update")
@click.argument("comment_id")
@click.argument("data")
@click.pass_obj
def update(ctx: ClientContext, comment_id: str, data: str) -> None:
    """
    Replace a comment's body, given as a rich-text JSON document.
    """
    render(ctx.client.update_comment(comment_id, parse_json(data)))


@group.command(name="delete")
@click.argument("comment_id")
@click.confirmation_option(prompt="Delete this comment and its replies?")
@click.pass_obj
def delete(ctx: ClientContext, comment_id: str) -> None:
    """
    Delete a comment and its replies.
    """
    render(ctx.client.delete_comment(comment_id))


@group.command(name="resolve")
@click.argument("comment_id")
@click.pass_obj
def resolve(ctx: ClientContext, comment_id: str) -> None:
    """
    Mark a comment thread resolved.
    """
    render(ctx.client.resolve_comment(comment_id))


@group.command(name="unresolve")
@click.argument("comment_id")
@click.pass_obj
def unresolve(ctx: ClientContext, comment_id: str) -> None:
    """
    Reopen a resolved comment thread.
    """
    render(ctx.client.unresolve_comment(comment_id))


@group.command(name="react")
@click.argument("comment_id")
@click.argument("emoji")
@click.pass_obj
def react(ctx: ClientContext, comment_id: str, emoji: str) -> None:
    """
    React to a comment with an emoji.
    """
    render(ctx.client.add_comment_reaction(comment_id, emoji))


@group.command(name="unreact")
@click.argument("comment_id")
@click.argument("emoji")
@click.pass_obj
def unreact(ctx: ClientContext, comment_id: str, emoji: str) -> None:
    """
    Take back an emoji reaction on a comment.
    """
    render(ctx.client.remove_comment_reaction(comment_id, emoji))


@group.command(name="reactions")
@click.argument("comment_id")
@pagination_options
@click.pass_obj
def reactions(
    ctx: ClientContext, comment_id: str, offset: int | None, limit: int | None
) -> None:
    """
    List the emoji reactions on a comment.
    """
    render(ctx.client.list_reactions(comment_id, offset=offset, limit=limit))
