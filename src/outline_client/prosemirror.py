"""
Render Outline's rich-text JSON as markdown.

Outline sends template and comment bodies only as the ProseMirror document its
editor stores, in `data`, with no markdown beside it. Documents do not have
this gap - Outline sends their body as markdown in `text` - so this covers
only the fields where the server offers no markdown of its own.

    from outline_client.prosemirror import to_markdown

    print(to_markdown(outline.get_template(template_id).data))

The node and mark names are those of Outline's editor schema, and each is
spelled the way Outline's own markdown export spells it where that costs
nothing, so the result can go back through a `text` argument unchanged.
"""

import re
from typing import Any

__all__ = ["to_markdown"]

type _Node = dict[str, Any]

# A mark reduced to what its markdown depends on: the type, and for a link its
# `href` and `title`. Two runs of text share an open mark only if these match.
type _Mark = tuple[str, str, str]

# Delimiters for the marks markdown can spell, outermost first; a link opens
# outside all of them. `code_inline` is handled apart, because its fence
# depends on the text inside it. Any other mark - `comment` and `placeholder`
# among them - has no markdown form and leaves its text bare.
_DELIMITERS = {
    "strong": "**",
    "em": "*",
    "strikethrough": "~~",
    "highlight": "==",
    "underline": "__",
}

_MARK_ORDER = ["link", *_DELIMITERS]

_INLINE_NODES = {"text", "br", "mention", "emoji", "image", "math_inline"}

_LIST_NODES = {"bullet_list", "ordered_list", "checkbox_list"}


# =============================================================================
# FUNCTION: to_markdown
# =============================================================================


def to_markdown(data: dict[str, Any] | None) -> str:
    """
    Render an Outline rich-text document as markdown.

    Covers the text blocks, lists, tables, media, inline nodes, and marks of
    Outline's editor schema. A node this function does not know renders its
    children, so a node Outline adds later degrades to its text rather than
    raising. A mention is spelled as Outline's own export spells it: a user as
    `@[Name](mention://<id>/user/<modelId>)`, a document or collection as a
    plain link.

    The conversion is lossy. A caller that syncs, exports, or round-trips
    content should keep `data` as Outline sent it. What this drops:

    - The `comment` and `placeholder` marks, and any mark it does not know,
      which have no markdown form. The text they cover is kept.
    - Image width, height, and layout, an attachment's size, and a video's
      dimensions.
    - Table column alignment and column widths.
    - The nesting depth of a toggle block.
    - Empty paragraphs, which markdown cannot hold.
    - Escaping: text is written as it was typed, so a literal `*` or `#` in
      it reads as markdown.
    - Any attribute that Outline's own markdown export also leaves out.

    Args:
        data: The rich-text document, such as a template's or comment's
            `data`.

    Returns:
        str: The markdown, or an empty string for `None`.
    """
    if not data:
        return ""

    return _block(data)


# =============================================================================
# FUNCTIONS: Blocks
# =============================================================================


def _blocks(nodes: list[_Node], *, tight: bool = False) -> str:
    """
    Render a run of blocks, separated by blank lines.

    Inside a list item (`tight`), a nested list follows the paragraph before
    it on the next line, as Outline's tight lists do, rather than after a
    blank line.

    Returns:
        str: The rendered blocks.
    """
    out: list[str] = []
    for node in nodes:
        rendered = _block(node)
        if not rendered:
            continue
        if out:
            out.append("\n" if tight and node.get("type") in _LIST_NODES else "\n\n")
        out.append(rendered)

    return "".join(out)


def _block(node: _Node) -> str:
    """
    Render one block node.

    Returns:
        str: The rendered block, or an empty string if it has no content.
    """
    attrs: dict[str, Any] = node.get("attrs") or {}
    children: list[_Node] = node.get("content") or []

    match node.get("type"):
        case "doc":
            return _blocks(children)
        case "paragraph":
            return _inline(children)
        case "heading":
            level = min(max(int(attrs.get("level") or 1), 1), 6)
            return f"{'#' * level} {_inline(children)}"
        case "blockquote":
            return "\n".join(
                f"> {line}" if line else ">" for line in _blocks(children).split("\n")
            )
        case "bullet_list":
            marker = f"{attrs.get('bullet') or '*'} "
            return "\n".join(_item(marker, "  ", item) for item in children)
        case "ordered_list":
            order = attrs.get("order")
            start = 1 if order is None else int(order)
            # Outline right-aligns the numbers, so every item's content starts
            # in the same column.
            width = len(str(start + len(children) - 1))
            return "\n".join(
                _item(f"{start + index:>{width}}. ", " " * (width + 2), item)
                for index, item in enumerate(children)
            )
        case "checkbox_list":
            return "\n".join(
                _item(
                    "- [x] " if (item.get("attrs") or {}).get("checked") else "- [ ] ",
                    "  ",
                    item,
                )
                for item in children
            )
        case "code_block" | "code_fence":
            return _fence(_text(node), attrs.get("language"))
        case "math_block":
            return f"$$\n{_text(node)}\n$$"
        case "hr":
            return str(attrs.get("markup") or "---")
        case "container_notice":
            return f":::{attrs.get('style') or 'info'}\n{_blocks(children)}\n:::"
        case "container_toggle":
            return f"+++\n{_blocks(children)}\n+++"
        case "table":
            return _table(children)
        case "attachment":
            return f"[{attrs.get('title') or 'attachment'}]({attrs.get('href') or ''})"
        case "video":
            return f"[{attrs.get('title') or 'video'}]({attrs.get('src') or ''})"
        case "embed":
            href = attrs.get("href") or ""
            return f"[{href}]({href})"
        case _ if children and not any(
            child.get("type") in _INLINE_NODES for child in children
        ):
            return _blocks(children)
        case _:
            return _inline([node])


def _item(marker: str, indent: str, item: _Node) -> str:
    """
    Render one list item, indenting its continuation lines under its content.

    `indent` is the column the item's content starts in, which for a task
    item is after the `- ` alone: the `[x]` is part of the content. Indenting
    further would turn a nested block into an indented code block.

    Returns:
        str: The rendered item.
    """
    first, *rest = _blocks(item.get("content") or [], tight=True).split("\n")

    return "\n".join(
        [marker + first, *(indent + line if line else line for line in rest)]
    )


def _fence(content: str, language: Any) -> str:
    """
    Wrap code in a fence longer than any run of backticks inside it.

    Returns:
        str: The fenced code block.
    """
    runs = [len(run) for run in re.findall(r"`{3,}", content)]
    fence = "`" * (max(runs) + 1 if runs else 3)
    # Only the first word of the language survives, as in Outline's export; a
    # backtick in it would close the fence.
    info = (str(language or "").replace("`", "").split() or [""])[0]

    return f"{fence}{info}\n{content}\n{fence}"


def _table(rows: list[_Node]) -> str:
    """
    Render a table as a GFM table, with the first row as its header.

    Returns:
        str: The rendered table, or an empty string if it has no rows.
    """
    rendered = [[_cell(cell) for cell in row.get("content") or []] for row in rows]
    if not rendered or not rendered[0]:
        return ""

    lines = [f"| {' | '.join(cells)} |" for cells in rendered]
    lines.insert(1, "|" + " --- |" * len(rendered[0]))

    return "\n".join(lines)


def _cell(cell: _Node) -> str:
    """
    Render a table cell on the one line a GFM table row allows.

    Line breaks become `<br>` and pipes are escaped, as in Outline's export.

    Returns:
        str: The rendered cell.
    """
    lines = _blocks(cell.get("content") or []).split("\n")

    return "<br>".join(line.rstrip() for line in lines).replace("|", "\\|")


# =============================================================================
# FUNCTIONS: Inline content
# =============================================================================


def _inline(nodes: list[_Node]) -> str:
    """
    Render inline content, keeping a mark open across the nodes that share it.

    A port of the `renderInline` of prosemirror-markdown, which Outline's own
    serializer forks. Closing and reopening a mark between two text nodes
    would spell `**a~~b~~**` as `**a****~~b~~**`, which markdown reads as a
    bold `a` and a literal `**`. Whitespace at the edge of a marked run moves
    outside the delimiters, because markdown does not close `** bold**`.

    Returns:
        str: The rendered content.
    """
    out: list[str] = []
    active: list[_Mark] = []
    trailing = ""

    # The trailing `None` closes whatever is still open at the end.
    for index, node in enumerate([*nodes, None]):
        marks = _marks(node) if node is not None else []
        code = node is not None and _has_code(node)
        text = str(node.get("text") or "") if node is not None else ""

        if node is not None and node.get("type") == "br":
            # A mark that ends at a hard break closes before it, so the break
            # is not left dangling inside the delimiters.
            marks = [mark for mark in marks if _continues(mark, nodes, index)]

        leading, trailing = trailing, ""
        if node is not None and node.get("type") == "text" and _expels(marks):
            parts = re.fullmatch(r"(\s*)(.*?)(\s*)", text, re.DOTALL)
            lead, text, trailing = parts.groups() if parts else ("", text, "")
            leading += lead
            if not text:
                # Whitespace alone neither opens nor closes a mark.
                node, marks = None, active

        keep = 0
        while keep < min(len(active), len(marks)) and active[keep] == marks[keep]:
            keep += 1
        while len(active) > keep:
            out.append(_close(active.pop()))

        out.append(leading)

        if node is None:
            continue

        while len(active) < len(marks):
            active.append(marks[len(active)])
            out.append(_open(active[-1]))

        if node.get("type") == "text":
            out.append(_code(text) if code else text)
        else:
            out.append(_leaf(node))

    return "".join(out)


def _marks(node: _Node) -> list[_Mark]:
    """
    Read the marks of a node that markdown can spell, outermost first.

    Returns:
        list[_Mark]: The node's marks, in the order they open.
    """
    marks: list[_Mark] = []
    for mark in node.get("marks") or []:
        kind = str(mark.get("type") or "")
        if kind not in _MARK_ORDER:
            continue
        attrs: dict[str, Any] = mark.get("attrs") or {}
        marks.append(
            (kind, str(attrs.get("href") or ""), str(attrs.get("title") or ""))
        )

    return sorted(set(marks), key=lambda mark: _MARK_ORDER.index(mark[0]))


def _has_code(node: _Node) -> bool:
    """
    Check whether a node carries the `code_inline` mark.

    Returns:
        bool: Whether the node is inline code.
    """
    return any(mark.get("type") == "code_inline" for mark in node.get("marks") or [])


def _expels(marks: list[_Mark]) -> bool:
    """
    Check whether a run's edge whitespace has to move outside its marks.

    A link keeps its whitespace, as in prosemirror-markdown; every delimited
    mark does not.

    Returns:
        bool: Whether any of the marks is delimited.
    """
    return any(kind in _DELIMITERS for kind, _, _ in marks)


def _continues(mark: _Mark, nodes: list[_Node], index: int) -> bool:
    """
    Check whether a mark on a hard break carries on into the next node.

    Returns:
        bool: Whether the next node has the mark and is not blank text.
    """
    if index + 1 >= len(nodes):
        return False

    after = nodes[index + 1]
    if mark not in _marks(after):
        return False

    return after.get("type") != "text" or bool(str(after.get("text") or "").strip())


def _open(mark: _Mark) -> str:
    """
    Spell the opening delimiter of a mark.

    Returns:
        str: The delimiter.
    """
    kind, _, _ = mark

    return "[" if kind == "link" else _DELIMITERS[kind]


def _close(mark: _Mark) -> str:
    """
    Spell the closing delimiter of a mark, which for a link is its target.

    Returns:
        str: The delimiter.
    """
    kind, href, title = mark
    if kind != "link":
        return _DELIMITERS[kind]
    if not title:
        return f"]({href})"

    return f"]({href} {_quote(title)})"


def _quote(title: str) -> str:
    """
    Quote a link title with whichever quotes it does not contain.

    Returns:
        str: The quoted title.
    """
    if '"' not in title:
        return f'"{title}"'
    if "'" not in title:
        return f"'{title}'"

    return f"({title})"


def _code(text: str) -> str:
    """
    Wrap inline code in a fence longer than any run of backticks inside it.

    Returns:
        str: The code span.
    """
    runs = [len(run) for run in re.findall(r"`+", text)]
    if not runs:
        return f"`{text}`"

    fence = "`" * (max(runs) + 1)

    return f"{fence} {text} {fence}"


def _leaf(node: _Node) -> str:
    """
    Render an inline node other than text.

    Returns:
        str: The rendered node.
    """
    attrs: dict[str, Any] = node.get("attrs") or {}

    match node.get("type"):
        case "br":
            # Two trailing spaces, as Outline's portable export spells a hard
            # break; a bare newline would read back as a space.
            return "  \n"
        case "mention":
            return _mention(attrs)
        case "emoji":
            name = attrs.get("data-name")
            return f":{name}:" if name else ""
        case "math_inline":
            return f"${_text(node)}$"
        case "image":
            title = attrs.get("title")
            target = (
                f"{attrs.get('src') or ''} {_quote(title)}"
                if title
                else attrs.get("src") or ""
            )
            return f"![{attrs.get('alt') or ''}]({target})"
        case _:
            return _inline(node.get("content") or [])


def _mention(attrs: dict[str, Any]) -> str:
    """
    Spell a mention the way Outline's own markdown export does.

    Returns:
        str: The mention, as a link.
    """
    label = attrs.get("label") or ""
    kind = attrs.get("type") or "user"
    model_id = attrs.get("modelId") or ""

    if kind == "document":
        anchor = attrs.get("anchorId")
        return f"[{label}](/doc/{model_id}{f'#{anchor}' if anchor else ''})"
    if kind == "collection":
        return f"[{label}](/collection/{model_id})"

    return f"@[{label}](mention://{attrs.get('id') or ''}/{kind}/{model_id})"


def _text(node: _Node) -> str:
    """
    Concatenate every text node under a node, for code and math content.

    Returns:
        str: The node's text.
    """
    if node.get("type") == "text":
        return str(node.get("text") or "")

    return "".join(_text(child) for child in node.get("content") or [])
