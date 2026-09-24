"""
Live coverage of the markdown renderer against Outline's own parser.

`to_markdown` spells each node the way Outline's export does, so that what a
caller reads can go back through a `text` argument unchanged. Only a live
parser can hold it to that: a document is templatized to get its rich text,
the rendering is imported as a second document, and the two must agree.
"""

import os
from collections.abc import Generator

import pytest

from outline_client.client import OutlineClient
from outline_client.prosemirror import to_markdown

pytestmark: list[pytest.MarkDecorator] = [pytest.mark.integration]

# The baseline collection and second account `docker/seed.py` creates.
COLLECTION_ID = "55555555-5555-4555-8555-555555555555"
MEMBER_ID = "44444444-4444-4444-8444-444444444444"

# One of nearly every node and mark the renderer knows. No two lists are
# adjacent, because markdown cannot keep two of one type apart, and the task
# list has one item: Outline 1.10 turns a list anywhere before a longer one into
# a task list as well.
SOURCE = f"""# Heading

Plain **bold**, *em*, ~~strike~~, ==mark==, __under__, `code`, **bold *both***, and [a link](https://example.test/x).

Ask @[Integration Test Member](mention://9e3c0f7a-8a8b-4d5e-9f00-000000000001/user/{MEMBER_ID}) :smile:

one\\
two

* outer
* second

Between the lists.

1. first
2. second

And a task.

- [x] done

```python
print(1)
```

> quote one
>
> quote two

:::warning
Careful here
:::

+++
Toggle title

hidden body
+++

| Name | Value |
|------|-------|
| pipe | a\\|b |
| **bold** | `code` |

---

$$
E = mc^2
$$

Some $x^2$ math and an ![alt text](https://example.test/i.png) image.
"""


@pytest.fixture(scope="module")
def client() -> Generator[OutlineClient]:
    if not (os.getenv("OUTLINE_API_URL") and os.getenv("OUTLINE_API_TOKEN")):
        raise RuntimeError(
            "Outline integration test misconfigured; run `make outline-up` and "
            "export: OUTLINE_API_URL, OUTLINE_API_TOKEN"
        )

    with OutlineClient() as outline:
        yield outline


class TestRoundTrip:
    def test_a_rendered_template_body_reads_back_unchanged(
        self, client: OutlineClient
    ) -> None:
        documents: list[str] = []
        templates: list[str] = []
        try:
            source = client.create_document(
                title="Source", text=SOURCE, collection_id=COLLECTION_ID, publish=True
            )
            documents.append(str(source.id))
            original = client.templatize_document(str(source.id), publish=True)
            templates.append(str(original.id))

            copy = client.create_document(
                title="Copy",
                text=to_markdown(original.data),
                collection_id=COLLECTION_ID,
                publish=True,
            )
            documents.append(str(copy.id))
            reread = client.templatize_document(str(copy.id), publish=True)
            templates.append(str(reread.id))

            assert reread.data == original.data
        finally:
            for template_id in templates:
                client.delete_template(template_id)
            for document_id in documents:
                client.delete_document(document_id)
                client.delete_document(document_id, permanent=True)
