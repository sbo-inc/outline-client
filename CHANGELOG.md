# Changelog

## [Unreleased]

- **Breaking:** `get_share` returns a `SharesResult` rather than a `Share`. `shares.info` has always answered with a bundle, so the `Share` it returned before had every field empty. The result holds the `shares` found and, for a public-link load by `id`, the `document`, `collection`, `team`, and `shared_tree` the link exposes. `get_share` also takes `collection_id`, and a document or collection with no share gives an empty `shares` rather than an error.
- **Breaking:** the arguments Outline accepts as JSON null now default to `NOT_GIVEN`, and `None` sends the null rather than leaving the field out. `update_document(id, icon=None)` used to leave the icon alone and now clears it; code that forwards an optional value into one of these arguments should pass `NOT_GIVEN` when it has none. `move_document(id, collection_id=..., parent_document_id=None)` now sends `parentDocumentId: null`, which moves the document to the collection root - as leaving it out already did on Outline 1.10. The arguments are on `update_document`, `move_document`, `update_collection`, `update_template`, `update_share`, `update_user`, `update_oauth_client`, and `update_notification`, and each method's docstring names them. `NOT_GIVEN` and `NotGiven` are exported from the package, and the CLI sends a null with `--clear FIELD`.
- `upload_attachment` uploads a file as an attachment in one call, in either of Outline's upload modes, and returns the `Attachment`. A store that refuses the upload raises the new `StorageError`. `Attachment` now has its `id`.
- **Breaking:** `download_attachment` returns an `AttachmentDownload` with `content`, `name`, and `content_type`, rather than the bytes alone; read `.content` for what it returned before. `outline attachments download ID` now saves the file under its own name; pass `-o -` for the old write to stdout.

## [0.1.0] - 2026-09-22

- First release. `OutlineClient` and `AsyncOutlineClient` cover all 154 methods in Outline's OpenAPI specification, with Pydantic models generated from it, and an `outline` CLI over the same surface.
