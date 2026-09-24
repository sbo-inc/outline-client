"""
Unit coverage of the share lookup, on both clients.

`shares.info` answers with a bundle - the shares found, and on a public-link
load the content they expose - rather than the single share the specification
describes, and with an empty 204 when a document has no share at all.
"""

from collections.abc import Callable
from typing import Any

import httpx
from conftest import DOCUMENT_ID, body, ok

from outline_client.async_client import AsyncOutlineClient
from outline_client.client import OutlineClient

type ClientFactory = Callable[..., OutlineClient]
type AsyncClientFactory = Callable[..., AsyncOutlineClient]

SHARE_ID = "9884b98e-3c7b-4a8a-964d-c64ce9002d21"
PARENT_SHARE_ID = "7c9e6679-7425-40de-944b-e07fc1f90ae7"


class TestGetShare:
    def test_reads_the_public_link_bundle(self, make_client: ClientFactory) -> None:
        seen: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(body(request))
            return ok(
                {
                    "shares": [{"id": SHARE_ID, "title": "Public", "published": True}],
                    "sharedTree": {"id": DOCUMENT_ID, "title": "Onboarding"},
                    "team": {"name": "Integration Tests"},
                    "collection": None,
                    "document": {"id": DOCUMENT_ID, "title": "Onboarding"},
                }
            )

        result = make_client(handler).get_share(SHARE_ID)

        assert seen == {"id": SHARE_ID}
        assert str(result.shares[0].id) == SHARE_ID
        assert result.shares[0].title == "Public"
        assert result.document is not None
        assert result.document.title == "Onboarding"
        assert result.team is not None
        assert result.team.name == "Integration Tests"
        assert result.shared_tree is not None
        assert result.collection is None

    async def test_reads_a_documents_share_and_the_parent_share(
        self, make_async_client: AsyncClientFactory
    ) -> None:
        seen: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(body(request))
            return ok({"shares": [{"id": SHARE_ID}, {"id": PARENT_SHARE_ID}]})

        async with make_async_client(handler) as client:
            result = await client.get_share(document_id=DOCUMENT_ID)

        assert seen == {"documentId": DOCUMENT_ID}
        assert [str(share.id) for share in result.shares] == [SHARE_ID, PARENT_SHARE_ID]
        assert result.document is None

    def test_reads_a_204_as_no_shares(self, make_client: ClientFactory) -> None:
        # Outline answers 204 with no body when the resource has no share.
        result = make_client(lambda request: httpx.Response(204)).get_share(
            collection_id=DOCUMENT_ID
        )

        assert result.shares == []
