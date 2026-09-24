"""
Unit coverage of attachment uploads and downloads, on both clients.

An attachment's bytes do not travel through Outline's API: `attachments.create`
answers with where and how to send them, and `attachments.redirect` answers
with where to fetch them from. The handler here stands in for both Outline and
the file store, told apart by host.
"""

from collections.abc import Callable
from typing import Any

import httpx
import pytest
from conftest import DOCUMENT_ID, body, ok

from outline_client.async_client import AsyncOutlineClient
from outline_client.client import OutlineClient
from outline_client.errors import StorageError

type ClientFactory = Callable[..., OutlineClient]
type AsyncClientFactory = Callable[..., AsyncOutlineClient]

ATTACHMENT_ID = "9884b98e-3c7b-4a8a-964d-c64ce9002d21"

ATTACHMENT: dict[str, Any] = {
    "id": ATTACHMENT_ID,
    "name": "site-plan.png",
    "contentType": "image/png",
    "size": "4",
    "url": f"/api/attachments.redirect?id={ATTACHMENT_ID}",
    "documentId": DOCUMENT_ID,
}

PUT_SLOT: dict[str, Any] = {
    "mode": "put",
    "url": "https://storage.test/bucket/uploads/site-plan.png?X-Amz-Signature=abc",
    "headers": {"Content-Type": "image/png", "Cache-Control": "max-age=31557600"},
    "attachment": ATTACHMENT,
}


def storage(
    slot: dict[str, Any], status: int = 200, text: str = ""
) -> tuple[list[httpx.Request], Callable[[httpx.Request], httpx.Response]]:
    """
    Build a handler that answers `attachments.create` and records the rest.

    The store answers every request it is sent with `status` and `text`.

    Returns:
        tuple[list[httpx.Request], Callable[..., httpx.Response]]: The
            requests sent to storage, and the handler.
    """
    sent: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/attachments.create":
            return ok(slot)
        sent.append(request)
        return httpx.Response(status, text=text)

    return sent, handler


# =============================================================================
# TESTS: upload_attachment
# =============================================================================


class TestUploadAttachment:
    def test_put_sends_the_bytes_to_the_presigned_url_without_the_token(
        self, make_client: ClientFactory
    ) -> None:
        sent, handler = storage(PUT_SLOT)

        attachment = make_client(handler).upload_attachment(
            b"\x89PNG", name="site-plan.png", document_id=DOCUMENT_ID
        )

        [request] = sent
        assert request.method == "PUT"
        assert str(request.url) == PUT_SLOT["url"]
        assert request.content == b"\x89PNG"
        assert request.headers["content-type"] == "image/png"
        assert request.headers["cache-control"] == "max-age=31557600"
        # The store is another origin; the presigned URL is the credential.
        assert "authorization" not in request.headers
        assert str(attachment.id) == ATTACHMENT_ID
        assert attachment.url == ATTACHMENT["url"]

    def test_post_sends_the_form_fields_and_then_the_file(
        self, make_client: ClientFactory
    ) -> None:
        slot = {
            "mode": "post",
            "uploadUrl": "https://storage.test/bucket",
            "form": {"key": "uploads/site-plan.png", "policy": "p0l1cy"},
            "attachment": ATTACHMENT,
        }
        sent, handler = storage(slot, 204)

        make_client(handler).upload_attachment(b"\x89PNG", name="site-plan.png")

        [request] = sent
        content = request.read()
        assert request.method == "POST"
        assert str(request.url) == "https://storage.test/bucket"
        assert request.headers["content-type"].startswith("multipart/form-data")
        assert b'name="key"\r\n\r\nuploads/site-plan.png' in content
        assert b'name="policy"\r\n\r\np0l1cy' in content
        # S3 ignores any field after the file, so it goes last.
        assert content.index(b'name="file"') > content.index(b'name="policy"')
        assert b'filename="site-plan.png"' in content
        assert b"Content-Type: image/png" in content
        assert "authorization" not in request.headers

    def test_a_relative_upload_url_resolves_against_the_api_origin(
        self, make_client: ClientFactory
    ) -> None:
        # With local file storage, the store is Outline itself.
        slot = {
            "mode": "post",
            "uploadUrl": "/api/files.create",
            "form": {"key": "uploads/notes.txt", "sig": "s1g"},
            "attachment": ATTACHMENT,
        }
        sent, handler = storage(slot)

        make_client(handler).upload_attachment(b"hello", name="notes.txt")

        [request] = sent
        assert str(request.url) == "https://outline.example.test/api/files.create"
        assert b"Content-Type: text/plain" in request.read()

    def test_reserves_the_attachment_with_the_size_and_guessed_type(
        self, make_client: ClientFactory
    ) -> None:
        reserved: dict[str, Any] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/api/attachments.create":
                reserved.update(body(request))
                return ok(PUT_SLOT)
            return httpx.Response(200)

        make_client(handler).upload_attachment(b"%PDF-1.4", name="plan.pdf")

        assert reserved == {
            "name": "plan.pdf",
            "contentType": "application/pdf",
            "size": 8,
        }

    def test_a_refused_upload_raises_a_storage_error(
        self, make_client: ClientFactory
    ) -> None:
        _, handler = storage(
            PUT_SLOT,
            403,
            "<Error><Code>SignatureDoesNotMatch</Code>"
            "<Message>The signature does not match.</Message></Error>",
        )

        with pytest.raises(StorageError) as raised:
            make_client(handler).upload_attachment(b"\x89PNG", name="site-plan.png")

        assert raised.value.status == 403
        assert raised.value.error == "SignatureDoesNotMatch"
        assert raised.value.message == "The signature does not match."

    async def test_the_async_client_sends_the_same_request(
        self, make_async_client: AsyncClientFactory
    ) -> None:
        sent, handler = storage(PUT_SLOT)

        async with make_async_client(handler) as client:
            await client.upload_attachment(b"\x89PNG", name="site-plan.png")

        [request] = sent
        assert request.method == "PUT"
        assert request.content == b"\x89PNG"
        assert "authorization" not in request.headers


# =============================================================================
# TESTS: download_attachment
# =============================================================================


def redirecting(stored: httpx.Response) -> Callable[[httpx.Request], httpx.Response]:
    """
    Build a handler that redirects `attachments.redirect` to the file store.

    Returns:
        Callable[[httpx.Request], httpx.Response]: The handler.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "outline.example.test":
            return httpx.Response(
                302,
                headers={
                    "Location": "https://storage.test/bucket/uploads/u/a/"
                    "site%20plan.png?X-Amz-Signature=abc"
                },
            )
        return stored

    return handler


class TestDownloadAttachment:
    def test_names_the_file_after_the_redirect_target_without_a_disposition(
        self, make_client: ClientFactory
    ) -> None:
        stored = httpx.Response(
            200, content=b"\x89PNG", headers={"Content-Type": "image/png"}
        )

        download = make_client(redirecting(stored)).download_attachment(ATTACHMENT_ID)

        assert download.content == b"\x89PNG"
        assert download.name == "site plan.png"
        assert download.content_type == "image/png"

    def test_prefers_the_full_name_in_the_disposition(
        self, make_client: ClientFactory
    ) -> None:
        stored = httpx.Response(
            200,
            content=b"%PDF-1.4",
            headers={
                "Content-Type": "application/pdf; charset=binary",
                "Content-Disposition": 'attachment; filename="r?sum?.pdf"; '
                "filename*=UTF-8''r%C3%A9sum%C3%A9.pdf",
            },
        )

        download = make_client(redirecting(stored)).download_attachment(ATTACHMENT_ID)

        assert download.name == "résumé.pdf"
        assert download.content_type == "application/pdf"
