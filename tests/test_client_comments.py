"""
Unit coverage of the comment surface, on both clients.
"""

from collections.abc import Callable
from typing import Any

import httpx
from conftest import DOCUMENT_ID, body, ok

from outline_client.async_client import AsyncOutlineClient
from outline_client.client import OutlineClient
from outline_client.schemas.enums import CommentStatusFilter

type ClientFactory = Callable[..., OutlineClient]
type AsyncClientFactory = Callable[..., AsyncOutlineClient]

THREAD_ID = "9884b98e-3c7b-4a8a-964d-c64ce9002d21"


# =============================================================================
# TESTS: list_comments
# =============================================================================


class TestListComments:
    async def test_sends_the_thread_and_status_filters_in_the_wire_spelling(
        self,
        make_client: ClientFactory,
        make_async_client: AsyncClientFactory,
    ) -> None:
        # The specification omits both fields, so nothing but this test holds
        # the client to the spelling Outline's `CommentsListSchema` reads.
        seen: list[dict[str, Any]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(body(request))
            return ok([])

        arguments: dict[str, Any] = {
            "document_id": DOCUMENT_ID,
            "parent_comment_id": THREAD_ID,
            "status_filter": [CommentStatusFilter.UNRESOLVED],
        }
        make_client(handler).list_comments(**arguments)
        async with make_async_client(handler) as client:
            await client.list_comments(**arguments)

        expected = {
            "documentId": DOCUMENT_ID,
            "parentCommentId": THREAD_ID,
            "statusFilter": ["unresolved"],
        }
        assert seen == [expected, expected]
