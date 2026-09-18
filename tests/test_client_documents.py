"""
Unit coverage of the document surface, on both clients.

Documents exercise every request and response shape the client has: a bare
object, an array, a bag of related records, a plain string, an acknowledgement,
a multipart upload, and a binary download. Asserting them here means the rest
of the surface is the same three lines of delegation repeated.
"""

from collections.abc import Callable
from typing import Any

import httpx
import pytest
from conftest import DOCUMENT_ID, body, ok

from outline_client.async_client import AsyncOutlineClient
from outline_client.client import OutlineClient
from outline_client.errors import PaymentRequiredError
from outline_client.schemas.models import DocumentFilterCondition

type ClientFactory = Callable[..., OutlineClient]
type AsyncClientFactory = Callable[..., AsyncOutlineClient]

DOCUMENT: dict[str, Any] = {
    "id": DOCUMENT_ID,
    "title": "Onboarding",
    "text": "# Welcome",
    "urlId": "hDYep1TPAM",
    "url": "/doc/onboarding-hDYep1TPAM",
    "collectionId": "9884b98e-3c7b-4a8a-964d-c64ce9002d21",
}


def capturing(response: httpx.Response) -> tuple[dict[str, Any], Callable[..., Any]]:
    """
    Build a handler that records the request it was sent.

    Returns:
        tuple[dict[str, Any], Callable[..., Any]]: The record and the handler.
    """
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["body"] = body(request)
        return response

    return seen, handler


# =============================================================================
# TESTS: Requests
# =============================================================================


class TestRequestBuilding:
    def test_sends_only_the_arguments_that_were_given(
        self, make_client: ClientFactory
    ) -> None:
        # Omitting a field and sending it as null mean different things to
        # Outline, so an unset argument must not appear in the payload at all.
        seen, handler = capturing(ok(DOCUMENT))

        make_client(handler).create_document(title="Onboarding", publish=True)

        assert seen["path"] == "/api/documents.create"
        assert seen["body"] == {"title": "Onboarding", "publish": True}

    def test_translates_snake_case_arguments_to_the_wire_spelling(
        self, make_client: ClientFactory
    ) -> None:
        seen, handler = capturing(ok(DOCUMENT))

        make_client(handler).create_document(
            title="Onboarding",
            collection_id="9884b98e-3c7b-4a8a-964d-c64ce9002d21",
            parent_document_id=None,
            full_width=True,
        )

        assert seen["body"] == {
            "title": "Onboarding",
            "collectionId": "9884b98e-3c7b-4a8a-964d-c64ce9002d21",
            "fullWidth": True,
        }

    def test_serializes_a_model_argument(self, make_client: ClientFactory) -> None:
        seen, handler = capturing(ok([DOCUMENT]))

        make_client(handler).list_documents(
            filters=[
                DocumentFilterCondition(
                    field="title", operator="contains", value="board"
                )
            ]
        )

        assert seen["body"] == {
            "filters": [{"field": "title", "operator": "contains", "value": "board"}]
        }

    def test_passes_pagination_through_unchanged(
        self, make_client: ClientFactory
    ) -> None:
        seen, handler = capturing(ok([DOCUMENT]))

        make_client(handler).list_documents(
            offset=25, limit=50, sort="updatedAt", direction="DESC"
        )

        assert seen["body"] == {
            "offset": 25,
            "limit": 50,
            "sort": "updatedAt",
            "direction": "DESC",
        }


# =============================================================================
# TESTS: Responses
# =============================================================================


class TestResponseParsing:
    def test_parses_a_single_object(self, make_client: ClientFactory) -> None:
        document = make_client(lambda request: ok(DOCUMENT)).get_document(DOCUMENT_ID)

        assert document.title == "Onboarding"
        # The document's url is a path, not an absolute URL, which is why the
        # generated `format: uri` fields are widened back to plain strings.
        assert document.url == "/doc/onboarding-hDYep1TPAM"

    def test_parses_an_array(self, make_client: ClientFactory) -> None:
        documents = make_client(
            lambda request: ok([DOCUMENT, DOCUMENT])
        ).list_documents()

        assert [document.title for document in documents] == [
            "Onboarding",
            "Onboarding",
        ]

    def test_parses_a_bag_of_related_records(self, make_client: ClientFactory) -> None:
        response = ok({"documents": [DOCUMENT], "collections": [{"name": "Handbook"}]})

        result = make_client(lambda request: response).move_document(DOCUMENT_ID)

        assert result.documents[0].title == "Onboarding"
        assert result.collections[0].name == "Handbook"

    def test_a_missing_bag_member_reads_as_empty_not_as_none(
        self, make_client: ClientFactory
    ) -> None:
        # Outline omits a member it has nothing to report for; a caller
        # iterating the result should not have to tell absent from empty.
        result = make_client(lambda request: ok({})).move_document(DOCUMENT_ID)

        assert result.documents == []
        assert result.collections == []

    def test_parses_a_bare_string(self, make_client: ClientFactory) -> None:
        markdown = make_client(lambda request: ok("# Welcome")).export_document(
            DOCUMENT_ID
        )

        assert markdown == "# Welcome"

    def test_parses_an_acknowledgement(self, make_client: ClientFactory) -> None:
        response = httpx.Response(200, json={"success": True, "ok": True})

        assert (
            make_client(lambda request: response).delete_document(DOCUMENT_ID) is True
        )

    def test_keeps_fields_the_models_do_not_know_about(
        self, make_client: ClientFactory
    ) -> None:
        # Outline ships new response fields regularly and the generated models
        # are only ever as current as the spec; dropping them would lose data
        # a caller can still reach.
        response = ok({**DOCUMENT, "somethingNew": 42})

        document = make_client(lambda request: response).get_document(DOCUMENT_ID)

        assert document.__pydantic_extra__ == {"somethingNew": 42}


# =============================================================================
# TESTS: The methods that are not plain JSON
# =============================================================================


class TestBinaryAndMultipart:
    def test_import_uploads_the_file_as_multipart(
        self, make_client: ClientFactory
    ) -> None:
        seen: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["content_type"] = request.headers["content-type"]
            seen["content"] = request.content
            return ok(DOCUMENT)

        make_client(handler).import_document(
            b"# Welcome",
            filename="welcome.md",
            collection_id="9884b98e-3c7b-4a8a-964d-c64ce9002d21",
            publish=True,
        )

        assert seen["content_type"].startswith("multipart/form-data")
        assert b'filename="welcome.md"' in seen["content"]
        assert b"# Welcome" in seen["content"]
        # A multipart part carries no type, so a boolean has to be spelled the
        # way JSON spells it rather than the way Python does.
        assert b"true" in seen["content"]
        assert b"True" not in seen["content"]

    def test_download_asks_for_the_requested_representation(
        self, make_client: ClientFactory
    ) -> None:
        seen: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(request.headers)
            return httpx.Response(200, content=b"%PDF-1.4")

        content = make_client(handler).download_document(
            DOCUMENT_ID, accept="application/pdf"
        )

        assert seen["accept"] == "application/pdf"
        assert content == b"%PDF-1.4"

    def test_download_raises_on_a_failure_rather_than_returning_the_body(
        self, make_client: ClientFactory
    ) -> None:
        response = httpx.Response(
            402,
            json={
                "ok": False,
                "error": "incorrect_edition",
                "message": "Not available",
            },
        )

        with pytest.raises(PaymentRequiredError):
            make_client(lambda request: response).download_document(DOCUMENT_ID)

    def test_attachment_url_reads_the_redirect_rather_than_following_it(
        self, make_client: ClientFactory
    ) -> None:
        # Following it would hand the signed storage URL's host a request this
        # client has no reason to make - the caller wants the address, not the
        # bytes.
        response = httpx.Response(
            302, headers={"Location": "https://storage.test/signed"}
        )

        url = make_client(lambda request: response).get_attachment_url(DOCUMENT_ID)

        assert url == "https://storage.test/signed"

    def test_attachment_url_falls_back_to_the_method_when_bytes_come_inline(
        self, make_client: ClientFactory
    ) -> None:
        # A local-storage backend streams the file instead of redirecting, in
        # which case the method's own URL is the only address it has.
        url = make_client(
            lambda request: httpx.Response(200, content=b"bytes")
        ).get_attachment_url(DOCUMENT_ID)

        assert url.endswith("/api/attachments.redirect")


# =============================================================================
# TESTS: Pagination
# =============================================================================


class TestPaginate:
    def test_requests_each_page_at_the_next_offset(
        self, make_client: ClientFactory
    ) -> None:
        pages = [[DOCUMENT, DOCUMENT], [DOCUMENT, DOCUMENT], [DOCUMENT]]
        calls: list[dict[str, Any]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(body(request))
            return ok(pages[len(calls) - 1])

        client = make_client(handler)
        documents = list(client.paginate(client.list_documents, limit=2))

        assert len(documents) == 5
        assert [call["offset"] for call in calls] == [0, 2, 4]
        assert {call["limit"] for call in calls} == {2}

    def test_stops_after_one_call_when_the_first_page_is_short(
        self, make_client: ClientFactory
    ) -> None:
        calls: list[dict[str, Any]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(body(request))
            return ok([DOCUMENT])

        client = make_client(handler)
        documents = list(client.paginate(client.list_documents, limit=50))

        assert len(documents) == 1
        assert len(calls) == 1

    def test_forwards_the_filters_to_every_page(
        self, make_client: ClientFactory
    ) -> None:
        calls: list[dict[str, Any]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(body(request))
            return ok([DOCUMENT] if len(calls) == 1 else [])

        client = make_client(handler)
        list(client.paginate(client.list_documents, limit=1, collection_id="abc"))

        assert all(call["collectionId"] == "abc" for call in calls)


# =============================================================================
# TESTS: The async surface
# =============================================================================


class TestAsyncSurface:
    async def test_takes_the_same_arguments_and_returns_the_same_models(
        self,
        make_client: ClientFactory,
        make_async_client: AsyncClientFactory,
    ) -> None:
        sync_seen, sync_handler = capturing(ok(DOCUMENT))
        async_seen, async_handler = capturing(ok(DOCUMENT))

        expected = make_client(sync_handler).create_document(
            title="Onboarding", collection_id="abc", publish=True
        )
        async with make_async_client(async_handler) as client:
            actual = await client.create_document(
                title="Onboarding", collection_id="abc", publish=True
            )

        assert sync_seen == async_seen
        assert actual == expected

    async def test_paginates_as_an_async_iterator(
        self, make_async_client: AsyncClientFactory
    ) -> None:
        pages = [[DOCUMENT, DOCUMENT], [DOCUMENT]]
        calls: list[dict[str, Any]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(body(request))
            return ok(pages[len(calls) - 1])

        async with make_async_client(handler) as client:
            documents = [
                document
                async for document in client.paginate(client.list_documents, limit=2)
            ]

        assert len(documents) == 3
        assert [call["offset"] for call in calls] == [0, 2]

    async def test_closes_the_transport_on_exit(
        self, make_async_client: AsyncClientFactory
    ) -> None:
        async with make_async_client(lambda request: ok(DOCUMENT)) as client:
            await client.get_document(DOCUMENT_ID)

        assert client.http.is_closed
