"""
Sending an explicit null, on the fields Outline accepts one for.

Omitting a field and sending it as null mean different things to Outline: a
document's icon is left alone in the first case and cleared in the second. The
nullable arguments default to `NOT_GIVEN` so that `None` can mean the second.
"""

from collections.abc import Callable
from typing import Any

import httpx
from conftest import DOCUMENT_ID, body, ok

from outline_client import NOT_GIVEN, NotGiven
from outline_client.client import OutlineClient
from outline_client.operations.generic import body as build_body
from outline_client.operations.generic import nullable

type ClientFactory = Callable[..., OutlineClient]

COLLECTION_ID = "9884b98e-3c7b-4a8a-964d-c64ce9002d21"


def capture(make_client: ClientFactory, data: Any) -> tuple[list[Any], OutlineClient]:
    """
    Build a client that records the body of every request it sends.

    Returns:
        tuple[list[Any], OutlineClient]: The recorded bodies and the client.
    """
    seen: list[Any] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(body(request))
        return ok(data)

    return seen, make_client(handler)


# =============================================================================
# TESTS: The payload builders
# =============================================================================


class TestPayloadBuilders:
    def test_nullable_drops_not_given_and_sends_none_as_null(self) -> None:
        assert nullable(icon=None, color=NOT_GIVEN, title="x") == {
            "icon": None,
            "title": "x",
        }

    def test_body_drops_both(self) -> None:
        # Every other argument keeps `None` as omit, because Outline rejects
        # a null there.
        assert build_body(id="x", title=None, icon=NOT_GIVEN) == {"id": "x"}

    def test_not_given_is_falsy_and_says_what_it_is(self) -> None:
        assert not NOT_GIVEN
        assert repr(NOT_GIVEN) == "NOT_GIVEN"
        assert isinstance(NOT_GIVEN, NotGiven)


# =============================================================================
# TESTS: The client methods
# =============================================================================


class TestClearingAField:
    def test_update_document_sends_a_null_icon(
        self, make_client: ClientFactory
    ) -> None:
        seen, client = capture(make_client, {"id": DOCUMENT_ID})

        client.update_document(DOCUMENT_ID, icon=None)
        client.update_document(DOCUMENT_ID, title="Renamed")

        assert seen == [
            {"id": DOCUMENT_ID, "icon": None},
            {"id": DOCUMENT_ID, "title": "Renamed"},
        ]

    def test_update_collection_sends_a_null_icon(
        self, make_client: ClientFactory
    ) -> None:
        seen, client = capture(make_client, {"id": COLLECTION_ID})

        client.update_collection(COLLECTION_ID, icon=None)

        assert seen == [{"id": COLLECTION_ID, "icon": None}]

    def test_update_template_sends_a_null_icon(
        self, make_client: ClientFactory
    ) -> None:
        seen, client = capture(make_client, {"id": DOCUMENT_ID})

        client.update_template(DOCUMENT_ID, icon=None)

        assert seen == [{"id": DOCUMENT_ID, "icon": None}]

    def test_move_document_leaves_out_a_parent_it_was_not_given(
        self, make_client: ClientFactory
    ) -> None:
        seen, client = capture(make_client, {})

        client.move_document(DOCUMENT_ID, collection_id=COLLECTION_ID)

        assert seen == [{"id": DOCUMENT_ID, "collectionId": COLLECTION_ID}]
