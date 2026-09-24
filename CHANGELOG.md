# Changelog

## [0.2.0] - 2026-09-24

- `outline_client.prosemirror.to_markdown` renders template and comment bodies as markdown, and the CLI gets `--markdown` ([#1]).
- `list_comments` takes `parent_comment_id` and `status_filter` ([#2]).
- `update_comment` takes a markdown `text` body ([#3]).
- **Breaking:** on fields Outline accepts as null, `None` now sends null, and `NOT_GIVEN` leaves the field out ([#4]).
- **Breaking:** `upload_attachment` uploads a file in one call, and `download_attachment` returns an `AttachmentDownload` ([#5]).
- **Breaking:** `get_share` returns a `SharesResult`, which holds what `shares.info` actually sends ([#11]).
- The test seed gives the Baseline collection a sort, so its shares load ([#12]).
- Fixed a flaky async integration test ([#13]).

## [0.1.0] - 2026-09-22

- First release. `OutlineClient` and `AsyncOutlineClient` cover all 154 methods in Outline's OpenAPI specification, with Pydantic models generated from it, and an `outline` CLI over the same surface.

[0.2.0]: https://github.com/sbo-inc/outline-client/releases/tag/v0.2.0
[0.1.0]: https://github.com/sbo-inc/outline-client/releases/tag/v0.1.0
[#1]: https://github.com/sbo-inc/outline-client/issues/1
[#2]: https://github.com/sbo-inc/outline-client/issues/2
[#3]: https://github.com/sbo-inc/outline-client/issues/3
[#4]: https://github.com/sbo-inc/outline-client/issues/4
[#5]: https://github.com/sbo-inc/outline-client/issues/5
[#11]: https://github.com/sbo-inc/outline-client/issues/11
[#12]: https://github.com/sbo-inc/outline-client/issues/12
[#13]: https://github.com/sbo-inc/outline-client/issues/13
