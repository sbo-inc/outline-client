# Changelog

## [Unreleased]

- **Breaking:** the arguments Outline accepts as JSON null now default to `NOT_GIVEN`, and `None` sends the null rather than leaving the field out. `update_document(id, icon=None)` used to leave the icon alone and now clears it; code that forwards an optional value into one of these arguments should pass `NOT_GIVEN` when it has none. `move_document(id, collection_id=..., parent_document_id=None)` now sends `parentDocumentId: null`, which moves the document to the collection root - as leaving it out already did on Outline 1.10. The arguments are on `update_document`, `move_document`, `update_collection`, `update_template`, `update_share`, `update_user`, `update_oauth_client`, and `update_notification`, and each method's docstring names them. `NOT_GIVEN` and `NotGiven` are exported from the package, and the CLI sends a null with `--clear FIELD`.

## [0.1.0] - 2026-09-22

- First release. `OutlineClient` and `AsyncOutlineClient` cover all 154 methods in Outline's OpenAPI specification, with Pydantic models generated from it, and an `outline` CLI over the same surface.
