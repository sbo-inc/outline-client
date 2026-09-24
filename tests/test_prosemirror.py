"""
The rich-text to markdown renderer.

Each row is a small document and the markdown it must render to. The spellings
follow Outline's own markdown export, so that what a caller reads can go back
through a `text` argument unchanged.
"""

from typing import Any

import pytest

from outline_client.prosemirror import to_markdown


def doc(*blocks: dict[str, Any]) -> dict[str, Any]:
    return {"type": "doc", "content": list(blocks)}


def text(value: str, *marks: str, href: str | None = None) -> dict[str, Any]:
    node: dict[str, Any] = {"type": "text", "text": value}
    if marks or href:
        node["marks"] = [{"type": mark} for mark in marks]
        if href:
            node["marks"].append({"type": "link", "attrs": {"href": href}})
    return node


def para(*inline: dict[str, Any]) -> dict[str, Any]:
    return {"type": "paragraph", "content": list(inline)}


def item(kind: str, *blocks: dict[str, Any], checked: bool = False) -> dict[str, Any]:
    node: dict[str, Any] = {"type": kind, "content": list(blocks)}
    if kind == "checkbox_item":
        node["attrs"] = {"checked": checked}
    return node


def row(kind: str, *cells: str) -> dict[str, Any]:
    return {
        "type": "tr",
        "content": [{"type": kind, "content": [para(text(cell))]} for cell in cells],
    }


@pytest.mark.parametrize(
    ("data", "markdown"),
    [
        # Marks
        pytest.param(
            doc(
                {"type": "heading", "attrs": {"level": 2}, "content": [text("Scope")]},
                para(text("Plain "), text("bold", "strong"), text(" end")),
            ),
            "## Scope\n\nPlain **bold** end",
            id="heading-and-marked-text",
        ),
        pytest.param(
            # Markdown does not close a delimiter that follows a space.
            doc(para(text("a"), text(" both ", "strong", "em"), text("b"))),
            "a ***both*** b",
            id="edge-whitespace-inside-a-mark",
        ),
        pytest.param(
            # Closing and reopening the bold between the two runs would spell
            # `**a****~~b~~**`, which markdown reads as a literal `**`.
            doc(para(text("a", "strong"), text("b", "strong", "strikethrough"))),
            "**a~~b~~**",
            id="a-mark-stays-open-across-runs",
        ),
        pytest.param(
            doc(para(text("site", href="https://example.test/x"))),
            "[site](https://example.test/x)",
            id="link",
        ),
        pytest.param(
            doc(para(text("run", "code_inline", "strong"))),
            "**`run`**",
            id="code-inside-strong",
        ),
        pytest.param(
            doc(para(text("a `tick`", "code_inline"))),
            "`` a `tick` ``",
            id="code-containing-a-backtick",
        ),
        pytest.param(
            # Neither mark has a markdown form, so the text is kept bare.
            doc(para(text("Name", "placeholder"), text(" noted", "comment"))),
            "Name noted",
            id="marks-without-a-markdown-form",
        ),
        # Blocks
        pytest.param(
            doc(
                {
                    "type": "bullet_list",
                    "content": [
                        item(
                            "list_item",
                            para(text("outer")),
                            {
                                "type": "ordered_list",
                                "attrs": {"order": 3},
                                "content": [
                                    item("list_item", para(text("three"))),
                                    item("list_item", para(text("four"))),
                                ],
                            },
                        )
                    ],
                }
            ),
            "* outer\n  3. three\n  4. four",
            id="nested-list-with-an-order-start",
        ),
        pytest.param(
            doc(
                {
                    "type": "checkbox_list",
                    "content": [
                        item(
                            "checkbox_item",
                            para(text("done")),
                            para(text("details")),
                            checked=True,
                        ),
                        item("checkbox_item", para(text("open"))),
                    ],
                }
            ),
            # The continuation lines up with the item's content, which starts
            # after the `- `; the `[x]` is part of it.
            "- [x] done\n\n  details\n- [ ] open",
            id="checkbox-list",
        ),
        pytest.param(
            doc(
                {
                    "type": "code_fence",
                    "attrs": {"language": "python"},
                    "content": [text("print(1)\nprint(2)")],
                }
            ),
            "```python\nprint(1)\nprint(2)\n```",
            id="code-fence-with-a-language",
        ),
        pytest.param(
            doc({"type": "code_block", "content": [text("```\nnested\n```")]}),
            "````\n```\nnested\n```\n````",
            id="code-fence-containing-a-fence",
        ),
        pytest.param(
            doc(
                {
                    "type": "container_notice",
                    "attrs": {"style": "warning"},
                    "content": [para(text("Careful"))],
                }
            ),
            ":::warning\nCareful\n:::",
            id="notice",
        ),
        pytest.param(
            doc(
                {
                    "type": "blockquote",
                    "content": [para(text("one")), para(text("two"))],
                }
            ),
            "> one\n>\n> two",
            id="blockquote-with-two-paragraphs",
        ),
        # The rest
        pytest.param(
            doc(
                para(
                    text("Ask "),
                    {
                        "type": "mention",
                        "attrs": {
                            "type": "user",
                            "label": "Pat Lee",
                            "modelId": "user-1",
                            "id": "mention-1",
                        },
                    },
                    text(" about "),
                    {
                        "type": "mention",
                        "attrs": {
                            "type": "document",
                            "label": "Setup",
                            "modelId": "doc-1",
                        },
                    },
                )
            ),
            "Ask @[Pat Lee](mention://mention-1/user/user-1) about [Setup](/doc/doc-1)",
            id="user-and-document-mentions",
        ),
        pytest.param(
            doc(
                {
                    "type": "table",
                    "content": [row("th", "Name", "Value"), row("td", "pipe", "a|b")],
                }
            ),
            "| Name | Value |\n| --- | --- |\n| pipe | a\\|b |",
            id="table-with-a-pipe-in-a-cell",
        ),
        pytest.param(
            # Two trailing spaces, as Outline's portable export spells it; a
            # bare newline would read back as a space.
            doc(para(text("line one"), {"type": "br"}, text("line two"))),
            "line one  \nline two",
            id="hard-break",
        ),
        pytest.param(
            # A node Outline adds later degrades to its text.
            doc({"type": "future_block", "content": [para(text("kept"))]}),
            "kept",
            id="unknown-node",
        ),
        pytest.param(None, "", id="none"),
    ],
)
def test_to_markdown(data: dict[str, Any] | None, markdown: str) -> None:
    assert to_markdown(data) == markdown
