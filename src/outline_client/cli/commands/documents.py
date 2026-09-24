from pathlib import Path
from typing import IO

import click

from outline_client.cli.context import ClientContext
from outline_client.cli.group import CommonClickGroup
from outline_client.cli.options import (
    clear_option,
    clearable,
    pagination_options,
    parse_json,
    permission_option,
    sorting_options,
)
from outline_client.cli.output import render, write_bytes


@click.group(name="documents", cls=CommonClickGroup)
def group() -> None:
    """
    Read, write, search, and share documents.
    """


@group.command(name="list")
@click.option("--filters", default=None, help="Filter expression, as JSON.")
@click.option("--collection-id", default=None, help="Limit to one collection.")
@click.option(
    "--parent-document-id", default=None, help="Limit to one parent's children."
)
@click.option("--user-id", default=None, help="Limit to one author.")
@click.option(
    "--backlink-document-id",
    default=None,
    help="Limit to documents linking to this one.",
)
@pagination_options
@sorting_options
@click.pass_obj
def list_(
    ctx: ClientContext,
    filters: str | None,
    collection_id: str | None,
    parent_document_id: str | None,
    user_id: str | None,
    backlink_document_id: str | None,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List the published documents and your own drafts.
    """
    render(
        ctx.client.list_documents(
            filters=parse_json(filters),
            collection_id=collection_id,
            parent_document_id=parent_document_id,
            user_id=user_id,
            backlink_document_id=backlink_document_id,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        )
    )


@group.command(name="get")
@click.argument("document_id", required=False)
@click.option(
    "--share-id", default=None, help="Read a publicly shared document instead."
)
@click.pass_obj
def get(ctx: ClientContext, document_id: str | None, share_id: str | None) -> None:
    """
    Show one document, by id, url id, or share id.
    """
    render(ctx.client.get_document(document_id, share_id=share_id))


@group.command(name="structure")
@click.argument("document_id")
@click.pass_obj
def structure(ctx: ClientContext, document_id: str) -> None:
    """
    Show a document and its nested children as a tree.
    """
    render(ctx.client.get_document_structure(document_id))


@group.command(name="create")
@click.option("--title", default=None, help="Document title.")
@click.option("--text", default=None, help="Body, as markdown.")
@click.option(
    "--text-file",
    type=click.File("r"),
    default=None,
    help="Read the body from a file, or from - for stdin.",
)
@click.option("--collection-id", default=None, help="Collection to publish into.")
@click.option("--parent-document-id", default=None, help="Document to nest under.")
@click.option("--template-id", default=None, help="Template to prefill the body from.")
@click.option("--icon", default=None, help="Icon name or emoji.")
@click.option("--color", default=None, help="Hex color for the icon.")
@click.option("--publish", is_flag=True, help="Publish rather than leave a draft.")
@click.option("--full-width", is_flag=True, help="Render edge to edge.")
@click.pass_obj
def create(
    ctx: ClientContext,
    title: str | None,
    text: str | None,
    text_file: IO[str] | None,
    collection_id: str | None,
    parent_document_id: str | None,
    template_id: str | None,
    icon: str | None,
    color: str | None,
    publish: bool,
    full_width: bool,
) -> None:
    """
    Create a document.

    A document is a draft unless --publish is given, and publishing needs a
    collection - either --collection-id or --parent-document-id.
    """
    if text and text_file:
        raise click.BadParameter("pass --text or --text-file, not both")

    render(
        ctx.client.create_document(
            title=title,
            text=text_file.read() if text_file else text,
            collection_id=collection_id,
            parent_document_id=parent_document_id,
            template_id=template_id,
            icon=icon,
            color=color,
            publish=publish or None,
            full_width=full_width or None,
        )
    )


@group.command(name="update")
@click.argument("document_id")
@click.option("--title", default=None, help="New title.")
@click.option("--text", default=None, help="New body, as markdown.")
@click.option(
    "--text-file",
    type=click.File("r"),
    default=None,
    help="Read the new body from a file, or from - for stdin.",
)
@click.option(
    "--edit-mode",
    type=click.Choice(["replace", "append", "prepend", "patch"]),
    default=None,
    help="How to apply the new body. Defaults to replacing it.",
)
@click.option(
    "--find-text", default=None, help="Text to replace, required by --edit-mode patch."
)
@click.option("--icon", default=None, help="New icon name or emoji.")
@click.option("--color", default=None, help="New hex color.")
@click.option("--collection-id", default=None, help="Collection to publish into.")
@click.option("--template-id", default=None, help="Template to apply.")
@click.option("--publish", is_flag=True, help="Publish the document.")
@click.option("--full-width/--no-full-width", default=None, help="Render edge to edge.")
@click.option(
    "--last-revision",
    type=int,
    default=None,
    help="Reject the write if the document has changed since this revision.",
)
@clear_option("icon", "color", "collection-id", "template-id")
@click.pass_obj
def update(
    ctx: ClientContext,
    document_id: str,
    title: str | None,
    text: str | None,
    text_file: IO[str] | None,
    edit_mode: str | None,
    find_text: str | None,
    icon: str | None,
    color: str | None,
    collection_id: str | None,
    template_id: str | None,
    publish: bool,
    full_width: bool | None,
    last_revision: int | None,
    clear: tuple[str, ...],
) -> None:
    """
    Update a document, leaving the options you omit as they are.
    """
    if text and text_file:
        raise click.BadParameter("pass --text or --text-file, not both")

    render(
        ctx.client.update_document(
            document_id,
            title=title,
            text=text_file.read() if text_file else text,
            edit_mode=edit_mode,
            find_text=find_text,
            icon=clearable(icon, "icon", clear),
            color=clearable(color, "color", clear),
            collection_id=clearable(collection_id, "collection-id", clear),
            template_id=clearable(template_id, "template-id", clear),
            publish=publish or None,
            full_width=full_width,
            last_revision=last_revision,
        )
    )


@group.command(name="delete")
@click.argument("document_id")
@click.option(
    "--permanent", is_flag=True, help="Delete outright rather than to the trash."
)
@click.pass_obj
def delete(ctx: ClientContext, document_id: str, permanent: bool) -> None:
    """
    Move a document to the trash, or delete it outright.
    """
    render(ctx.client.delete_document(document_id, permanent=permanent or None))


@group.command(name="move")
@click.argument("document_id")
@click.option("--collection-id", default=None, help="Collection to move into.")
@click.option("--parent-document-id", default=None, help="Document to nest under.")
@click.option("--index", type=float, default=None, help="Position among its siblings.")
@clear_option("collection-id", "parent-document-id")
@click.pass_obj
def move(
    ctx: ClientContext,
    document_id: str,
    collection_id: str | None,
    parent_document_id: str | None,
    index: float | None,
    clear: tuple[str, ...],
) -> None:
    """
    Move a document to another collection or under another parent.
    """
    render(
        ctx.client.move_document(
            document_id,
            collection_id=clearable(collection_id, "collection-id", clear),
            parent_document_id=clearable(
                parent_document_id, "parent-document-id", clear
            ),
            index=index,
        )
    )


@group.command(name="duplicate")
@click.argument("document_id")
@click.option("--title", default=None, help="Title for the copy.")
@click.option("--recursive", is_flag=True, help="Copy the children too.")
@click.option("--publish", is_flag=True, help="Publish the copy.")
@click.option("--collection-id", default=None, help="Collection to copy into.")
@click.option(
    "--parent-document-id", default=None, help="Document to nest the copy under."
)
@click.pass_obj
def duplicate(
    ctx: ClientContext,
    document_id: str,
    title: str | None,
    recursive: bool,
    publish: bool,
    collection_id: str | None,
    parent_document_id: str | None,
) -> None:
    """
    Copy a document, optionally with its children.
    """
    render(
        ctx.client.duplicate_document(
            document_id,
            title=title,
            recursive=recursive or None,
            publish=publish or None,
            collection_id=collection_id,
            parent_document_id=parent_document_id,
        )
    )


@group.command(name="archive")
@click.argument("document_id")
@click.pass_obj
def archive(ctx: ClientContext, document_id: str) -> None:
    """
    Archive a document.
    """
    render(ctx.client.archive_document(document_id))


@group.command(name="restore")
@click.argument("document_id")
@click.option("--collection-id", default=None, help="Collection to restore into.")
@click.option(
    "--revision-id", default=None, help="Roll the contents back to this revision."
)
@click.pass_obj
def restore(
    ctx: ClientContext,
    document_id: str,
    collection_id: str | None,
    revision_id: str | None,
) -> None:
    """
    Restore a document from the archive or the trash.
    """
    render(
        ctx.client.restore_document(
            document_id, collection_id=collection_id, revision_id=revision_id
        )
    )


@group.command(name="unpublish")
@click.argument("document_id")
@click.option("--detach", is_flag=True, help="Detach from its collection as well.")
@click.pass_obj
def unpublish(ctx: ClientContext, document_id: str, detach: bool) -> None:
    """
    Return a published document to the draft state.
    """
    render(ctx.client.unpublish_document(document_id, detach=detach or None))


@group.command(name="templatize")
@click.argument("document_id")
@click.option(
    "--collection-id", default=None, help="Collection to create the template in."
)
@click.option(
    "--publish/--draft", default=True, show_default=True, help="Publish the template."
)
@click.pass_obj
def templatize(
    ctx: ClientContext, document_id: str, collection_id: str | None, publish: bool
) -> None:
    """
    Create a template from a document's contents.
    """
    render(
        ctx.client.templatize_document(
            document_id, publish, collection_id=collection_id
        )
    )


@group.command(name="empty-trash")
@click.confirmation_option(prompt="Permanently delete every document in the trash?")
@click.pass_obj
def empty_trash(ctx: ClientContext) -> None:
    """
    Permanently delete every document in the trash.
    """
    render(ctx.client.empty_trash())


@group.command(name="archived")
@click.option("--collection-id", default=None, help="Limit to one collection.")
@pagination_options
@sorting_options
@click.pass_obj
def archived(
    ctx: ClientContext,
    collection_id: str | None,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List the archived documents.
    """
    render(
        ctx.client.list_archived_documents(
            collection_id=collection_id,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        )
    )


@group.command(name="deleted")
@click.option("--filters", default=None, help="Filter expression, as JSON.")
@pagination_options
@sorting_options
@click.pass_obj
def deleted(
    ctx: ClientContext,
    filters: str | None,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List the documents in the trash.
    """
    render(
        ctx.client.list_deleted_documents(
            filters=parse_json(filters),
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        )
    )


@group.command(name="drafts")
@click.option("--collection-id", default=None, help="Limit to one collection.")
@click.option(
    "--date-filter", default=None, help="Limit to a period, e.g. week or month."
)
@pagination_options
@sorting_options
@click.pass_obj
def drafts(
    ctx: ClientContext,
    collection_id: str | None,
    date_filter: str | None,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List your unpublished drafts.
    """
    render(
        ctx.client.list_draft_documents(
            collection_id=collection_id,
            date_filter=date_filter,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        )
    )


@group.command(name="viewed")
@pagination_options
@sorting_options
@click.pass_obj
def viewed(
    ctx: ClientContext,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    List the documents you viewed most recently.
    """
    render(
        ctx.client.list_viewed_documents(
            offset=offset, limit=limit, sort=sort, direction=direction
        )
    )


@group.command(name="search")
@click.argument("query", required=False)
@click.option("--filters", default=None, help="Filter expression, as JSON.")
@click.option("--collection-id", default=None, help="Limit to one collection.")
@click.option(
    "--document-id", default=None, help="Limit to one document and its children."
)
@click.option("--user-id", default=None, help="Limit to one author.")
@click.option(
    "--date-filter", default=None, help="Limit to a period, e.g. week or month."
)
@click.option(
    "--share-id", default=None, help="Search within a publicly shared document."
)
@pagination_options
@sorting_options
@click.pass_obj
def search(
    ctx: ClientContext,
    query: str | None,
    filters: str | None,
    collection_id: str | None,
    document_id: str | None,
    user_id: str | None,
    date_filter: str | None,
    share_id: str | None,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    Search documents by their full contents.
    """
    render(
        ctx.client.search_documents(
            query,
            filters=parse_json(filters),
            collection_id=collection_id,
            document_id=document_id,
            user_id=user_id,
            date_filter=date_filter,
            share_id=share_id,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        )
    )


@group.command(name="search-titles")
@click.argument("query")
@click.option("--filters", default=None, help="Filter expression, as JSON.")
@click.option("--collection-id", default=None, help="Limit to one collection.")
@click.option(
    "--document-id", default=None, help="Limit to one document and its children."
)
@click.option("--user-id", default=None, help="Limit to one author.")
@pagination_options
@sorting_options
@click.pass_obj
def search_titles(
    ctx: ClientContext,
    query: str,
    filters: str | None,
    collection_id: str | None,
    document_id: str | None,
    user_id: str | None,
    offset: int | None,
    limit: int | None,
    sort: str | None,
    direction: str | None,
) -> None:
    """
    Search documents by title alone.
    """
    render(
        ctx.client.search_document_titles(
            query,
            filters=parse_json(filters),
            collection_id=collection_id,
            document_id=document_id,
            user_id=user_id,
            offset=offset,
            limit=limit,
            sort=sort,
            direction=direction,
        )
    )


@group.command(name="ask")
@click.argument("query")
@click.option("--collection-id", default=None, help="Limit to one collection.")
@click.option(
    "--document-id", default=None, help="Limit to one document and its children."
)
@click.option("--user-id", default=None, help="Limit to one author.")
@click.pass_obj
def ask(
    ctx: ClientContext,
    query: str,
    collection_id: str | None,
    document_id: str | None,
    user_id: str | None,
) -> None:
    """
    Ask a natural-language question of the workspace's documents.

    Only available on installations with the AI answers feature enabled.
    """
    render(
        ctx.client.answer_question(
            query,
            collection_id=collection_id,
            document_id=document_id,
            user_id=user_id,
        )
    )


@group.command(name="export")
@click.argument("document_id")
@click.option("--children", is_flag=True, help="Include nested documents, as a zip.")
@click.option(
    "--accept",
    default=None,
    help="Ask for another format, e.g. text/html or application/pdf. Writes bytes.",
)
@click.option(
    "--output", "-o", default=None, help="Write to this path instead of stdout."
)
@click.option(
    "--signed-urls",
    type=int,
    default=None,
    help="How long, in seconds, attachment links stay valid.",
)
@click.option("--paper-size", default=None, help="Page size for a PDF export.")
@click.pass_obj
def export(
    ctx: ClientContext,
    document_id: str,
    children: bool,
    accept: str | None,
    output: str | None,
    signed_urls: int | None,
    paper_size: str | None,
) -> None:
    """
    Export a document.

    Markdown is written as text; --accept and --children both produce a binary
    file, which goes to --output or to stdout.
    """
    if accept or children:
        write_bytes(
            ctx.client.download_document(
                document_id,
                accept=accept or "application/x-textbundle",
                include_child_documents=children or None,
                signed_urls=signed_urls,
                paper_size=paper_size,
            ),
            output,
        )
        return

    markdown = ctx.client.export_document(
        document_id, signed_urls=signed_urls, paper_size=paper_size
    )
    if output:
        write_bytes(markdown.encode(), output)
        return

    render(markdown)


@group.command(name="import")
@click.argument("path", type=click.File("rb"))
@click.option(
    "--filename",
    default=None,
    help="Name to upload under. Defaults to the file's own name, whose "
    "extension is what Outline uses to decide how to parse it.",
)
@click.option("--collection-id", default=None, help="Collection to import into.")
@click.option("--parent-document-id", default=None, help="Document to import under.")
@click.option("--publish", is_flag=True, help="Publish rather than leave a draft.")
@click.option(
    "--content-type", default=None, help="MIME type, if the extension is not enough."
)
@click.pass_obj
def import_(
    ctx: ClientContext,
    path: IO[bytes],
    filename: str | None,
    collection_id: str | None,
    parent_document_id: str | None,
    publish: bool,
    content_type: str | None,
) -> None:
    """
    Create a document by uploading a file.

    One of --collection-id or --parent-document-id is required.
    """
    render(
        ctx.client.import_document(
            path,
            filename=filename or Path(path.name).name,
            content_type=content_type,
            collection_id=collection_id,
            parent_document_id=parent_document_id,
            publish=publish or None,
        )
    )


@group.command(name="insights")
@click.argument("document_id")
@click.option(
    "--start-date", default=None, help="Earliest period to include (YYYY-MM-DD)."
)
@click.option("--end-date", default=None, help="Latest period to include (YYYY-MM-DD).")
@click.pass_obj
def insights(
    ctx: ClientContext,
    document_id: str,
    start_date: str | None,
    end_date: str | None,
) -> None:
    """
    Show the activity rollups for a document.
    """
    render(
        ctx.client.list_document_insights(
            document_id, start_date=start_date, end_date=end_date
        )
    )


@group.command(name="views")
@click.argument("document_id")
@click.option("--include-suspended", is_flag=True, help="Include suspended users.")
@click.pass_obj
def views(ctx: ClientContext, document_id: str, include_suspended: bool) -> None:
    """
    Show who has read a document, and how often.
    """
    render(
        ctx.client.list_views(document_id, include_suspended=include_suspended or None)
    )


@group.command(name="users")
@click.argument("document_id")
@click.option("--query", default=None, help="Match user names against this text.")
@click.option("--user-id", default=None, help="Check one user in particular.")
@click.pass_obj
def users(
    ctx: ClientContext, document_id: str, query: str | None, user_id: str | None
) -> None:
    """
    List the users who can access a document, however they got access.
    """
    render(ctx.client.list_document_users(document_id, query=query, user_id=user_id))


@group.command(name="memberships")
@click.argument("document_id")
@click.option("--query", default=None, help="Match member names against this text.")
@permission_option
@click.pass_obj
def memberships(
    ctx: ClientContext, document_id: str, query: str | None, permission: str | None
) -> None:
    """
    List the users given access to a document individually.
    """
    render(
        ctx.client.list_document_memberships(
            document_id, query=query, permission=permission
        )
    )


@group.command(name="add-user")
@click.argument("document_id")
@click.argument("user_id")
@permission_option
@click.pass_obj
def add_user(
    ctx: ClientContext, document_id: str, user_id: str, permission: str | None
) -> None:
    """
    Give one user access to a document.
    """
    render(ctx.client.add_document_user(document_id, user_id, permission=permission))


@group.command(name="remove-user")
@click.argument("document_id")
@click.argument("user_id")
@click.pass_obj
def remove_user(ctx: ClientContext, document_id: str, user_id: str) -> None:
    """
    Take away one user's individual access to a document.
    """
    render(ctx.client.remove_document_user(document_id, user_id))


@group.command(name="group-memberships")
@click.argument("document_id")
@click.option("--query", default=None, help="Match group names against this text.")
@permission_option
@pagination_options
@click.pass_obj
def group_memberships(
    ctx: ClientContext,
    document_id: str,
    query: str | None,
    permission: str | None,
    offset: int | None,
    limit: int | None,
) -> None:
    """
    List the groups given access to a document.
    """
    render(
        ctx.client.list_document_group_memberships(
            document_id,
            query=query,
            permission=permission,
            offset=offset,
            limit=limit,
        )
    )


@group.command(name="add-group")
@click.argument("document_id")
@click.argument("group_id")
@permission_option
@click.pass_obj
def add_group(
    ctx: ClientContext, document_id: str, group_id: str, permission: str | None
) -> None:
    """
    Give a group access to a document.
    """
    render(ctx.client.add_document_group(document_id, group_id, permission=permission))


@group.command(name="remove-group")
@click.argument("document_id")
@click.argument("group_id")
@click.pass_obj
def remove_group(ctx: ClientContext, document_id: str, group_id: str) -> None:
    """
    Take away a group's access to a document.
    """
    render(ctx.client.remove_document_group(document_id, group_id))
