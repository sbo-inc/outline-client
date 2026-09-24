"""
Live coverage against a real Outline instance.

`make outline-up` starts one on http://localhost:8099 and prints the two
environment variables this suite reads. The point of the suite is the things a
mocked transport cannot check: that the payloads this client builds are ones
Outline accepts, and that the models parse what it actually sends back - which
is not always what the published specification says it sends.

The workspace is left as it was found: everything created here is torn down by
the fixtures that created it.

A handful of methods cannot be reached from a community-edition container at
all. They are listed in `UNAVAILABLE` and asserted to fail for that reason
rather than skipped silently, so a method that breaks for some *other* reason
is still caught.
"""

import asyncio
import os
import time
import uuid
from collections.abc import AsyncGenerator, Callable, Generator
from typing import Any

import pytest
import pytest_asyncio

from outline_client.async_client import AsyncOutlineClient
from outline_client.client import OutlineClient
from outline_client.errors import (
    AuthorizationError,
    NotFoundError,
    OutlineAPIError,
    PaymentRequiredError,
)
from outline_client.schemas.enums import CommentStatusFilter
from outline_client.schemas.models import Collection, Document

pytestmark: list[pytest.MarkDecorator] = [pytest.mark.integration]

# One async client is shared across the module, the way a consumer shares it
# across tasks, so its connection pool is reused. That requires one event loop
# for the whole module: a pooled connection belongs to the loop it was opened
# in. The mark goes on the async class rather than the module so the synchronous
# tests are not dressed up as coroutines.
asyncio_module_loop = pytest.mark.asyncio(loop_scope="module")

REQUIRED_ENV_VARS = ("OUTLINE_API_URL", "OUTLINE_API_TOKEN")

# The second account `docker/seed.py` creates. Outline refuses to let a user
# change their own role or invite themselves to a document, so the membership
# methods need somebody else to act on.
MEMBER_ID = "44444444-4444-4444-8444-444444444444"

# The baseline collection `docker/seed.py` writes with SQL rather than through
# the API, so it has only what the seed gives it.
BASELINE_COLLECTION_ID = "55555555-5555-4555-8555-555555555555"

# Methods the community edition does not serve. Each is still called, and each
# is asserted to fail in the way that edition fails - a 404 for a route that
# does not exist, a 402 for one that is gated, a 403 for one an API token is
# not allowed to reach.
UNAVAILABLE: dict[str, type[OutlineAPIError]] = {
    "list_data_attributes": NotFoundError,
    "answer_question": NotFoundError,
    "create_api_key": AuthorizationError,
}


# =============================================================================
# HELPERS
# =============================================================================


def eventually(check: Callable[[], bool], timeout: float = 20.0) -> bool:
    """
    Poll a condition until it holds, or until the timeout runs out.

    Outline caches each user's accessible-collection ids in Redis for ten
    seconds, and the search and list methods filter by that cached set. A
    document created in a brand-new collection is therefore invisible to them
    until the cache expires - which is Outline's behaviour, not this client's,
    but it does mean an assertion about a just-created document cannot be made
    on the first try.

    Returns:
        bool: Whether the condition held before the timeout.
    """
    deadline = time.monotonic() + timeout
    while True:
        if check():
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(1)


def discard(client: OutlineClient, document_id: str) -> None:
    """
    Remove a document completely, leaving nothing in the trash.

    Outline refuses to delete a document outright while it is still live, so
    it is trashed first and then deleted for good.
    """
    client.delete_document(document_id)
    client.delete_document(document_id, permanent=True)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture(scope="module")
def client() -> Generator[OutlineClient]:
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        raise RuntimeError(
            "Outline integration test misconfigured; run `make outline-up` and "
            "export: " + ", ".join(missing)
        )

    with OutlineClient() as outline:
        yield outline


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def async_client() -> AsyncGenerator[AsyncOutlineClient]:
    async with AsyncOutlineClient() as outline:
        yield outline


@pytest.fixture(scope="module")
def collection(client: OutlineClient) -> Generator[Collection]:
    """
    A collection that exists for the length of the module, then is removed.
    """
    created = client.create_collection(
        f"Integration {uuid.uuid4().hex[:8]}",
        description="Created by the outline-client integration suite.",
        permission="read_write",
    )
    try:
        yield created
    finally:
        client.delete_collection(str(created.id))


@pytest.fixture
def document(client: OutlineClient, collection: Collection) -> Generator[Document]:
    """
    A published document, deleted outright at the end of the test.
    """
    created = client.create_document(
        title="Onboarding",
        text="# Welcome\n\nThe first paragraph.",
        collection_id=str(collection.id),
        publish=True,
    )
    try:
        yield created
    finally:
        discard(client, str(created.id))


# =============================================================================
# TESTS: Identity
# =============================================================================


class TestAuth:
    def test_reports_the_token_owner(self, client: OutlineClient) -> None:
        info = client.get_auth_info()

        assert info.user is not None
        assert info.user.email is not None
        assert info.team is not None

    def test_reads_the_sign_in_configuration_without_a_token(self) -> None:
        # `auth.config` is the one method Outline answers unauthenticated, and
        # the cheapest way to check a self-hosted URL is reachable.
        with OutlineClient(token="") as anonymous:
            config = anonymous.get_auth_config()

        assert config.name


# =============================================================================
# TESTS: The document lifecycle
# =============================================================================


class TestDocumentLifecycle:
    def test_creates_reads_updates_and_deletes(
        self, client: OutlineClient, collection: Collection
    ) -> None:
        created = client.create_document(
            title="Lifecycle",
            text="First draft.",
            collection_id=str(collection.id),
            publish=True,
        )
        assert created.title == "Lifecycle"

        fetched = client.get_document(str(created.id))
        assert fetched.id == created.id

        updated = client.update_document(str(created.id), title="Lifecycle, revised")
        assert updated.title == "Lifecycle, revised"

        assert client.delete_document(str(created.id)) is True
        assert any(
            document.id == created.id for document in client.list_deleted_documents()
        )

        restored = client.restore_document(str(created.id))
        assert restored.title == "Lifecycle, revised"

        discard(client, str(created.id))

    def test_appends_to_a_body_rather_than_replacing_it(
        self, client: OutlineClient, document: Document
    ) -> None:
        client.update_document(str(document.id), text="\nAppended.", edit_mode="append")

        markdown = client.export_document(str(document.id))

        assert "The first paragraph." in markdown
        assert "Appended." in markdown

    def test_clears_an_icon_with_an_explicit_null(
        self, client: OutlineClient, document: Document
    ) -> None:
        client.update_document(str(document.id), icon="rocket", color="#FF0000")

        # Left out, the icon is kept; `None` sends the null that clears it.
        kept = client.update_document(str(document.id), title="Renamed")
        assert kept.icon == "rocket"

        cleared = client.update_document(str(document.id), icon=None, color=None)
        assert cleared.icon is None
        assert cleared.color is None

    def test_archives_and_restores(
        self, client: OutlineClient, document: Document
    ) -> None:
        archived = client.archive_document(str(document.id))
        assert archived.archived_at is not None
        assert eventually(
            lambda: any(
                found.id == document.id for found in client.list_archived_documents()
            )
        )

        restored = client.restore_document(str(document.id))
        assert restored.archived_at is None

    def test_duplicates(self, client: OutlineClient, document: Document) -> None:
        result = client.duplicate_document(str(document.id), title="Onboarding copy")

        assert result.documents
        for copy in result.documents:
            discard(client, str(copy.id))

    def test_moves_between_parents(
        self, client: OutlineClient, collection: Collection, document: Document
    ) -> None:
        child = client.create_document(
            title="Child",
            text="Nested.",
            collection_id=str(collection.id),
            publish=True,
        )
        try:
            result = client.move_document(
                str(child.id), parent_document_id=str(document.id)
            )
            assert result.documents

            structure = client.get_document_structure(str(document.id))
            assert structure.children
        finally:
            discard(client, str(child.id))

    def test_imports_a_markdown_file(
        self, client: OutlineClient, collection: Collection
    ) -> None:
        imported = client.import_document(
            b"# Imported\n\nFrom a file.",
            filename="imported.md",
            collection_id=str(collection.id),
            publish=True,
        )
        try:
            assert imported.title == "Imported"
        finally:
            discard(client, str(imported.id))

    def test_exports_in_a_binary_format(
        self, client: OutlineClient, document: Document
    ) -> None:
        html = client.download_document(str(document.id), accept="text/html")

        assert html.startswith(b"<!DOCTYPE html>") or b"<html" in html


# =============================================================================
# TESTS: Search
# =============================================================================


class TestSearch:
    def test_finds_a_document_by_its_contents(
        self, client: OutlineClient, document: Document
    ) -> None:
        assert eventually(
            lambda: any(
                hit.document and hit.document.id == document.id
                for hit in client.search_documents("paragraph")
            )
        )
        assert all(
            hit.context is not None for hit in client.search_documents("paragraph")
        )

    def test_finds_a_document_by_title(
        self, client: OutlineClient, document: Document
    ) -> None:
        assert eventually(
            lambda: any(
                item.id == document.id
                for item in client.search_document_titles("Onboarding")
            )
        )

    def test_filters_structurally(
        self, client: OutlineClient, collection: Collection, document: Document
    ) -> None:
        def in_collection() -> bool:
            return any(
                item.id == document.id
                for item in client.list_documents(
                    filters=[
                        {
                            "field": "collectionId",
                            "operator": "eq",
                            "value": str(collection.id),
                        }
                    ]
                )
            )

        assert eventually(in_collection)


# =============================================================================
# TESTS: Sharing and membership
# =============================================================================


class TestSharing:
    def test_publishes_and_revokes_a_share(
        self, client: OutlineClient, document: Document
    ) -> None:
        share = client.create_share(document_id=str(document.id))
        try:
            published = client.update_share(str(share.id), True, title="Public")
            assert published.published is True
            assert published.url

            # A published share is readable without a token, which is the
            # point of the one method that takes a shareId.
            with OutlineClient(token="") as anonymous:
                assert anonymous.get_document(share_id=str(share.id)).id == document.id
        finally:
            client.revoke_share(str(share.id))

    def test_loads_a_share_of_a_document_in_the_seeded_collection(
        self, client: OutlineClient
    ) -> None:
        # A public load reads the collection's sort, which Outline's model
        # defaults and the seed has to set itself; without it, this is a 500.
        created = client.create_document(
            title="Baseline share",
            text="Shared from the seeded collection.",
            collection_id=BASELINE_COLLECTION_ID,
            publish=True,
        )
        share = client.create_share(document_id=str(created.id))
        try:
            client.update_share(str(share.id), True)

            body = client.request("shares.info", {"id": str(share.id)})
            assert body["data"]["shares"][0]["id"] == str(share.id)
        finally:
            client.revoke_share(str(share.id))
            discard(client, str(created.id))

    def test_grants_and_removes_a_user_membership(
        self, client: OutlineClient, document: Document
    ) -> None:
        result = client.add_document_user(
            str(document.id), MEMBER_ID, permission="read"
        )
        assert result.memberships

        listed = client.list_document_memberships(str(document.id))
        assert any(str(user.id) == MEMBER_ID for user in listed.users)

        assert client.remove_document_user(str(document.id), MEMBER_ID) is True

    def test_grants_and_removes_a_group_membership(
        self, client: OutlineClient, document: Document
    ) -> None:
        group = client.create_group(f"Group {uuid.uuid4().hex[:8]}")
        try:
            added = client.add_group_user(str(group.id), MEMBER_ID)
            # The specification types this as an access level; the server sends
            # a role within the group.
            assert added.group_memberships[0].permission in {"member", "admin"}

            result = client.add_document_group(
                str(document.id), str(group.id), permission="read"
            )
            assert result.group_memberships

            assert client.remove_document_group(str(document.id), str(group.id)) is True
        finally:
            client.delete_group(str(group.id))


# =============================================================================
# TESTS: Comments
# =============================================================================


class TestComments:
    def test_lists_one_thread_and_filters_by_status(
        self, client: OutlineClient, document: Document
    ) -> None:
        # The specification omits both filters; the server honours them.
        thread = client.create_comment(str(document.id), text="Thread")
        reply = client.create_comment(
            str(document.id), text="Reply", parent_comment_id=str(thread.id)
        )
        resolved = client.create_comment(str(document.id), text="Resolved")
        client.resolve_comment(str(resolved.id))

        replies = client.list_comments(
            document_id=str(document.id), parent_comment_id=str(thread.id)
        )
        assert [comment.id for comment in replies] == [reply.id]

        done = client.list_comments(
            document_id=str(document.id),
            status_filter=[CommentStatusFilter.RESOLVED],
        )
        assert [comment.id for comment in done] == [resolved.id]


# =============================================================================
# TESTS: The rest of the read surface
# =============================================================================


class TestReads:
    @pytest.mark.parametrize(
        "method",
        [
            "list_users",
            "list_collections",
            "list_documents",
            "list_templates",
            "list_shares",
            "list_groups",
            "list_stars",
            "list_pins",
            "list_notifications",
            "list_attachments",
            "list_events",
            "list_api_keys",
            "list_oauth_clients",
            "list_oauth_authentications",
            "list_webhook_subscriptions",
            "list_draft_documents",
            "list_viewed_documents",
            "list_archived_documents",
            "list_deleted_documents",
            "list_user_memberships",
            "list_group_memberships",
            "get_auth_info",
        ],
    )
    def test_every_argumentless_read_parses(
        self, client: OutlineClient, method: str
    ) -> None:
        # The models are only as current as the specification they were
        # generated from, and the specification is not always right; a parse
        # failure here is the thing this suite exists to catch.
        getattr(client, method)()

    def test_pagination_walks_the_whole_list(self, client: OutlineClient) -> None:
        one_at_a_time = list(client.paginate(client.list_users, limit=1))
        in_one_page = client.list_users(limit=100)

        assert len(one_at_a_time) == len(in_one_page)

    def test_reads_a_documents_history_and_readers(
        self, client: OutlineClient, document: Document
    ) -> None:
        client.get_document(str(document.id))

        assert client.list_revisions(str(document.id)) is not None
        assert client.list_views(str(document.id)) is not None
        assert client.list_document_users(str(document.id))
        assert client.list_document_insights(str(document.id)) is not None


# =============================================================================
# TESTS: Background jobs and files
# =============================================================================


class TestFileOperations:
    def test_exports_a_collection_and_downloads_the_result(
        self, client: OutlineClient, collection: Collection
    ) -> None:
        queued = client.export_collection(str(collection.id))
        assert queued.file_operation is not None
        operation_id = str(queued.file_operation.id)

        try:
            state = _await_completion(client, operation_id)
            assert state == "complete"

            archive = client.download_file_operation(operation_id)
            # The export is a zip, whatever the requested format.
            assert archive[:2] == b"PK"
        finally:
            client.delete_file_operation(operation_id)

    def test_reserves_an_attachment_and_resolves_its_url(
        self, client: OutlineClient, document: Document
    ) -> None:
        upload = client.create_attachment(
            "note.txt", "text/plain", 5, document_id=str(document.id)
        )
        assert upload.upload_url
        assert upload.attachment is not None

        # Outline hands back a relative path here, which is why the generated
        # URL types are widened to plain strings.
        assert upload.attachment.url is not None
        assert client.get_attachment_url(str(upload.attachment.id))

        client.delete_attachment(str(upload.attachment.id))

    def test_uploads_an_attachment_and_downloads_it_by_name(
        self, client: OutlineClient, document: Document
    ) -> None:
        # The container uses local file storage, so the upload is a multipart
        # POST to the relative `/api/files.create`, authorized by the form's
        # signature rather than the token.
        attachment = client.upload_attachment(
            b"# Notes\n", name="notes.md", document_id=str(document.id)
        )
        try:
            assert attachment.url == f"/api/attachments.redirect?id={attachment.id}"

            download = client.download_attachment(str(attachment.id))
            assert download.content == b"# Notes\n"
            assert download.name == "notes.md"
            assert download.content_type == "text/markdown"
        finally:
            client.delete_attachment(str(attachment.id))


# =============================================================================
# TESTS: What this edition does not serve
# =============================================================================


class TestUnavailableMethods:
    @pytest.mark.parametrize("method", sorted(UNAVAILABLE))
    def test_fails_for_the_expected_reason(
        self, client: OutlineClient, method: str
    ) -> None:
        # Called rather than skipped, so a method that starts failing for some
        # other reason is still caught.
        expected = UNAVAILABLE[method]
        arguments = {"create_api_key": ("scratch",), "answer_question": ("What?",)}

        with pytest.raises((expected, PaymentRequiredError)):
            getattr(client, method)(*arguments.get(method, ()))


# =============================================================================
# TESTS: The async surface
# =============================================================================


@asyncio_module_loop
class TestAsyncSurface:
    async def test_agrees_with_the_sync_surface(
        self,
        client: OutlineClient,
        async_client: AsyncOutlineClient,
        document: Document,
    ) -> None:
        assert await async_client.get_document(str(document.id)) == client.get_document(
            str(document.id)
        )
        assert await async_client.list_collections() == client.list_collections()

    async def test_writes_through_the_async_surface(
        self, async_client: AsyncOutlineClient, collection: Collection
    ) -> None:
        created = await async_client.create_document(
            title="Async lifecycle",
            text="Written by the async client.",
            collection_id=str(collection.id),
            publish=True,
        )
        try:
            updated = await async_client.update_document(
                str(created.id), title="Async lifecycle, revised"
            )
            assert updated.title == "Async lifecycle, revised"
        finally:
            await async_client.delete_document(str(created.id))
            await async_client.delete_document(str(created.id), permanent=True)

    async def test_runs_reads_concurrently(
        self, async_client: AsyncOutlineClient
    ) -> None:
        results: list[Any] = await asyncio.gather(
            async_client.list_users(),
            async_client.list_collections(),
            async_client.list_documents(),
        )

        assert len(results) == 3


# =============================================================================
# HELPERS
# =============================================================================


def _await_completion(
    client: OutlineClient, operation_id: str, attempts: int = 60
) -> str | None:
    """
    Poll a file operation until it stops being in progress.

    Returns:
        str | None: The state it settled on.
    """
    for _ in range(attempts):
        state = client.get_file_operation(operation_id).state
        if state not in {"creating", "uploading"}:
            return state
        time.sleep(1)

    return None
