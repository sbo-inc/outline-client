[![CI](https://github.com/sbo-inc/outline-client/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/sbo-inc/outline-client/actions/workflows/ci.yaml)
[![PyPI](https://img.shields.io/pypi/v/outline-client.svg)](https://pypi.org/project/outline-client/)
[![Python versions](https://img.shields.io/pypi/pyversions/outline-client.svg)](https://pypi.org/project/outline-client/)
[![License](https://img.shields.io/pypi/l/outline-client.svg)](https://github.com/sbo-inc/outline-client/blob/main/LICENSE)

# Outline Python client

An unofficial typed Python client and command-line interface for the [Outline](https://www.getoutline.com) knowledge base API - no affiliation with Outline is implied or intended.

Outline's API is RPC-style: every method is a `POST` to `https://your-outline/api/:method`. This package wraps all **154** of them in a fully type-hinted client built on [Pydantic](https://docs.pydantic.dev/) models generated from the [published OpenAPI specification](https://github.com/outline/openapi), plus an `outline` CLI for reaching them from the terminal.

## Features

- **Complete** - every method in the specification, on both the sync and async clients and in the CLI.
- **Typed models** - schemas are generated from the OpenAPI specification with [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator), so `make schemas` is the whole upgrade path when the spec moves.
- **Sync and async** - `OutlineClient` and `AsyncOutlineClient` take the same arguments and return the same models.
- **Python client and CLI** - use it as a library, or straight from the shell via `outline`.
- **Typed errors** - a failed call raises `NotFoundError`, `RateLimitError`, `AuthorizationError` and friends rather than a bare exception.
- **Forward compatible** - fields Outline adds before the specification catches up are preserved rather than dropped.

## Installation

The package is published on PyPI as [`outline-client`](https://pypi.org/project/outline-client/):

```bash
pip install outline-client
# or, with uv:
uv add outline-client
```

Requires Python 3.12+.

## Configuration

An API token is the only credential this client uses. Create one under **Settings => API & Apps**; Outline's tokens begin with `ol_api_`. Treat it like a password - it carries the full access of the user who created it, and it is shown only once.

Settings are read from environment variables, or can be passed directly to the client:

| Variable | Description |
| --- | --- |
| `OUTLINE_API_URL` | The API endpoint. A workspace URL is accepted and has `/api` appended. Defaults to `https://app.getoutline.com/api`. |
| `OUTLINE_API_TOKEN` | The API token. |

```bash
# Cloud-hosted; OUTLINE_API_URL can be omitted.
export OUTLINE_API_TOKEN="ol_api_..."

# Self-hosted; either spelling of the URL works.
export OUTLINE_API_URL="https://outline.example.com"
```

OAuth 2.0 access tokens work anywhere an API token does - both are sent as a bearer credential - but this package does not implement the authorization-code exchange that obtains one.

### Timeouts and retries

Every request carries a timeout (default `(5, 60)` seconds for connect and read) so a stalled connection cannot hang the caller forever. Pass `timeout=` to override it (a single float, a `(connect, read)` tuple, or `None` to disable), and `retries=` to retry connection-establishment failures:

```python
# Wait longer, and retry a dropped or stale connection up to 3 times.
client = OutlineClient(timeout=120, retries=3)
```

`retries` retries only the connection stage, before any bytes reach the server, which is safe for the non-idempotent writes this client performs: a create whose response is merely lost is never resubmitted. The CLI reads `OUTLINE_API_TIMEOUT` (seconds) and `OUTLINE_API_RETRIES` (count) for the same behaviour.

## Quick start

### Python

```python
from outline_client import OutlineClient

# Reads OUTLINE_API_URL / OUTLINE_API_TOKEN from the environment, or pass
# url= and token= explicitly.
with OutlineClient() as outline:
    collection = outline.create_collection("Handbook", permission="read_write")

    document = outline.create_document(
        title="Onboarding",
        text="# Welcome\n\nStart here.",
        collection_id=str(collection.id),
        publish=True,
    )

    for hit in outline.search_documents("onboarding"):
        print(hit.ranking, hit.document.title, hit.context)

    print(outline.export_document(str(document.id)))
```

### Python (async)

`AsyncOutlineClient` mirrors `OutlineClient` method for method, so independent
reads can be gathered rather than awaited one at a time:

```python
import asyncio

from outline_client import AsyncOutlineClient


async def main() -> None:
    async with AsyncOutlineClient() as outline:
        documents, collections, users = await asyncio.gather(
            outline.list_documents(limit=100),
            outline.list_collections(),
            outline.list_users(),
        )
        print(len(documents), len(collections), len(users))


asyncio.run(main())
```

### CLI

```bash
# Every command prints indented JSON, so it pipes into jq unchanged.
outline auth info
outline collections list | jq -r '.[].name'
outline documents list --collection-id "$COLLECTION_ID" --limit 10

# Create a document from a file, then export it back out.
outline documents create --title "Onboarding" --text-file ./onboarding.md \
    --collection-id "$COLLECTION_ID" --publish
outline documents export "$DOCUMENT_ID" > onboarding.md
outline documents export "$DOCUMENT_ID" --accept text/html -o onboarding.html

outline --help              # every resource
outline documents --help    # every method on one resource
```

`OUTLINE_CLI_DISABLE` takes a comma-separated list of dotted command paths
(`documents.empty-trash,users.delete`) and hides them from `--help` and from
dispatch, so an embedded runtime can suppress the destructive ones.

## Usage

### Pagination

Outline's list methods take `offset` and `limit`, and report back the window
they served rather than a total. `paginate` walks the pages for any of them:

```python
for user in outline.paginate(outline.list_users, limit=100):
    print(user.email)

# On the async client it is an async iterator.
async for document in outline.paginate(outline.list_documents, limit=100):
    print(document.title)
```

### Filters

The newer list and search methods take a structured filter expression,
evaluated as an `AND` of the top-level entries. Conditions and nested
`AND`/`OR` groups are both models:

```python
from outline_client import DocumentFilterCondition, DocumentFilterGroup

recent_drafts = outline.list_documents(
    filters=[
        DocumentFilterCondition(
            field="collectionId", operator="eq", value=collection_id
        ),
        DocumentFilterGroup(
            operator="OR",
            filters=[
                DocumentFilterCondition(
                    field="title", operator="contains", value="draft"
                ),
                DocumentFilterCondition(field="updatedAt", operator="gte", value="P7D"),
            ],
        ),
    ]
)
```

### Errors

A failed call raises a subclass of `OutlineAPIError` chosen by the HTTP status,
carrying Outline's own message and its machine-readable `error` identifier:

```python
from outline_client import NotFoundError, RateLimitError

try:
    document = outline.get_document(document_id)
except NotFoundError:
    document = None
except RateLimitError as exc:
    time.sleep(exc.retry_after or 60)
```

| Exception | Status | Raised when |
| --- | --- | --- |
| `ValidationError` | 400 | The request failed one of Outline's validations. |
| `AuthenticationError` | 401 | The token is missing, malformed, or revoked. |
| `PaymentRequiredError` | 402 | The feature is not available on this installation. |
| `AuthorizationError` | 403 | The token is valid but not permitted this action. |
| `NotFoundError` | 404 | The record does not exist, or is not visible. |
| `RateLimitError` | 429 | Too many requests in the rate-limit window. |
| `ServerError` | 5xx | The request failed inside Outline. |

`OutlineConfigurationError` is raised before any request is made, when the URL
or token is missing.

### Exports and other background jobs

Exporting a collection queues a job rather than returning a file. Poll it, then
download what it produced:

```python
queued = outline.export_collection(collection_id, format="outline-markdown")
operation_id = str(queued.file_operation.id)

while outline.get_file_operation(operation_id).state in {"creating", "uploading"}:
    time.sleep(1)

Path("handbook.zip").write_bytes(outline.download_file_operation(operation_id))
```

### The escape hatch

Client methods return the `data` a response carries. The `policies` and
`pagination` beside it, an explicit JSON `null`, and any method a release does
not yet cover are all reachable through `request`:

```python
body = outline.request("documents.info", {"id": document_id})
print(body["policies"])
```

## Design

### Generated schemas, hand-written methods

`src/outline_client/schemas/models.py` is generated from Outline's published
OpenAPI specification and should not be edited; `make schemas` regenerates it.
Everything else - the operations, the client methods, the CLI - is written by
hand, so argument names, defaults, and docstrings say what the method does
rather than what a generator guessed.

The generator's output is corrected in three documented ways, each asserted so
that a specification change fails the regeneration rather than passing
silently. See `scripts/generate_schemas.py`:

- **Widened types.** `format: uri` and `format: email` become `AnyUrl` and
  `EmailStr`, which reject data Outline actually sends - an attachment's `url`
  is the relative path `/api/attachments.redirect?id=...`. Both widen to `str`.
- **Renamed classes.** Anonymous sub-schemas are named after the property they
  were found under and disambiguated with a counter, which yields `Operator1`
  and `Field3`. Each is renamed to what it is, e.g. `DocumentFilterOperator`.
- **Specification corrections.** Places where the specification and the server
  disagree, verified against a running Outline 1.10: `Permission` is missing
  `admin`, and a group membership's `permission` is a role within the group
  (`member`/`admin`), not an access level.

A few methods are corrected in the operations layer for the same reason -
`notifications.list` and `pins.list` are documented as returning an array but
answer with an object wrapping one, and `revisions.list` is documented as
taking an optional `documentId` that the server requires.

### Unknown fields are kept

Outline ships response fields before the specification catches up, so models
allow extras rather than dropping them. Anything the models do not name is
still reachable:

```python
document = outline.get_document(document_id)
print(document.__pydantic_extra__)
```

## Development

```bash
make install     # sync the locked environment
make schemas     # regenerate the models from the OpenAPI specification
make check       # ruff and mypy
make test        # unit tests, against a mocked transport
make coverage    # the same, with a coverage floor
```

### Integration tests

`make outline-up` starts a throwaway Outline 1.10.1 on
[http://localhost:8099](http://localhost:8099) with its own Postgres and Redis,
seeds a workspace, an admin, a second non-admin member, a baseline collection,
and an API token, then prints the two variables the suite reads:

```bash
make outline-up
export OUTLINE_API_URL=http://localhost:8099
export OUTLINE_API_TOKEN=ol_api_outlineClientIntegrationTests000000001
make test-integration
make outline-down   # stop it and delete its data
```

The suite exercises the real request and response shapes, which is the only way
to catch the places where the published specification is wrong. Three methods
cannot be reached from a community-edition container - `dataAttributes.*` and
`documents.answerQuestion` are not in the open-source server at all, and
`apiKeys.create` refuses an API token as the caller - so the suite asserts that
each fails for that reason rather than skipping it.

Three things about the live server are worth knowing if you write more of these
tests. Outline caches each user's accessible-collection ids in Redis for ten
seconds and filters the search and list methods by that cached set, so a
document in a brand-new collection is briefly invisible to them; the suite's
`eventually` helper polls through that window. `documents.delete` refuses
`permanent=True` on a live document, so `discard` trashes it first. And
`collections.delete` refuses to remove a workspace's only collection, which is
why the seed creates a baseline one for the suite's own collection to sit
beside.

## Reference

- [Outline API documentation](https://www.getoutline.com/developers)
- [Outline OpenAPI specification](https://github.com/outline/openapi)
- [Outline source](https://github.com/outline/outline)

## License

MIT
