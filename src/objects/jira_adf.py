from __future__ import annotations

import copy
from typing import Any

_BLOCK_TYPES_WITH_INLINE_CONTENT = frozenset({"paragraph", "heading"})


def _sanitize_text_node(node: dict[str, Any]) -> dict[str, Any]:
    text = node.get("text")
    if isinstance(text, str):
        text = text.replace("\x00", "")
    if text is None or text == "":
        text = " "
    node = {**node, "text": text}
    marks = node.get("marks")
    if not isinstance(marks, list):
        return node
    kept: list[dict[str, Any]] = []
    for m in marks:
        if m.get("type") == "link":
            href = (m.get("attrs") or {}).get("href")
            if not href:
                continue
        kept.append(m)
    if not kept:
        return {k: v for k, v in node.items() if k != "marks"}
    return {**node, "marks": kept}


def _walk_adf_node(node: dict[str, Any]) -> dict[str, Any]:
    if node.get("type") == "text":
        return _sanitize_text_node(node)
    content = node.get("content")
    if isinstance(content, list):
        new_children = [_walk_adf_node(c) if isinstance(c, dict) else c for c in content]
        ntype = node.get("type")
        if ntype in _BLOCK_TYPES_WITH_INLINE_CONTENT and len(new_children) == 0:
            new_children = [{"type": "text", "text": " "}]
        node = {**node, "content": new_children}
    return node


def sanitize_jira_adf_doc(doc: dict[str, Any]) -> dict[str, Any]:
    return _walk_adf_node(copy.deepcopy(doc))


def plain_text_to_adf_doc(plain: str) -> dict[str, Any]:
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": plain}],
            }
        ],
    }


def adf_doc(*blocks: dict[str, Any]) -> dict[str, Any]:
    return {"type": "doc", "version": 1, "content": list(blocks)}


def paragraph(*inline_nodes: dict[str, Any]) -> dict[str, Any]:
    return {"type": "paragraph", "content": list(inline_nodes)}


def heading(level: int, *inline_nodes: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": list(inline_nodes),
    }


def inline_text(
    text: str,
    *,
    bold: bool = False,
    italic: bool = False,
    url: str | None = None,
) -> dict[str, Any]:
    node: dict[str, Any] = {"type": "text", "text": text}
    marks: list[dict[str, Any]] = []
    if bold:
        marks.append({"type": "strong"})
    if italic:
        marks.append({"type": "em"})
    if url:
        marks.append({"type": "link", "attrs": {"href": url}})
    if marks:
        node["marks"] = marks
    return node


def adf_mention(account_id: str, display_stub: str) -> dict[str, Any]:
    return {
        "type": "mention",
        "attrs": {
            "id": account_id,
            "text": display_stub,
        },
    }


def closed_by_firewatch_adf() -> dict[str, Any]:
    return adf_doc(
        paragraph(
            inline_text("Closed by "),
            inline_text(
                "firewatch",
                url="https://github.com/CSPI-QE/firewatch",
            ),
            inline_text("."),
        ),
    )


def _adf_node_plain_text(node: dict[str, Any]) -> str:
    t = node.get("type")
    if t == "text":
        return str(node.get("text", ""))
    if t == "mention":
        return str(node.get("attrs", {}).get("text", ""))
    if t == "hardBreak":
        return "\n"
    parts = node.get("content")
    if isinstance(parts, list):
        return "".join(_adf_node_plain_text(c) for c in parts if isinstance(c, dict))
    return ""


def description_to_plain_text_for_search(description: str | dict[str, Any] | None) -> str:
    if description is None:
        return ""
    if isinstance(description, str):
        return description
    if isinstance(description, dict) and description.get("type") == "doc":
        return "".join(
            _adf_node_plain_text(block) for block in description.get("content", []) if isinstance(block, dict)
        )
    if isinstance(description, dict):
        return _adf_node_plain_text(description)
    return ""
