from src.objects.jira_adf import (
    adf_doc,
    adf_mention,
    closed_by_firewatch_adf,
    description_to_plain_text_for_search,
    heading,
    inline_text,
    paragraph,
    plain_text_to_adf_doc,
    sanitize_jira_adf_doc,
)


class TestPlainTextToAdfDoc:
    def test_single_paragraph_matches_minimal_doc_shape(self):
        plain = "Line one\nLine two"
        assert plain_text_to_adf_doc(plain) == {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": plain}],
                }
            ],
        }


class TestAdfDoc:
    def test_root_has_doc_type_version_and_content(self):
        p = paragraph(inline_text("only"))
        doc = adf_doc(p)
        assert doc == {
            "type": "doc",
            "version": 1,
            "content": [p],
        }


class TestParagraph:
    def test_paragraph_wraps_inline_nodes(self):
        assert paragraph(inline_text("a"), inline_text("b", bold=True)) == {
            "type": "paragraph",
            "content": [
                {"type": "text", "text": "a"},
                {"type": "text", "text": "b", "marks": [{"type": "strong"}]},
            ],
        }


class TestHeading:
    def test_heading_level_four_for_section_titles(self):
        assert heading(
            4,
            inline_text("Section"),
        ) == {
            "type": "heading",
            "attrs": {"level": 4},
            "content": [{"type": "text", "text": "Section"}],
        }


class TestInlineText:
    def test_plain_text_node(self):
        assert inline_text("hello") == {"type": "text", "text": "hello"}

    def test_bold_uses_strong_mark(self):
        assert inline_text("x", bold=True) == {
            "type": "text",
            "text": "x",
            "marks": [{"type": "strong"}],
        }

    def test_italic_uses_em_mark(self):
        assert inline_text("x", italic=True) == {
            "type": "text",
            "text": "x",
            "marks": [{"type": "em"}],
        }

    def test_link_uses_link_mark_with_href(self):
        assert inline_text("firewatch", url="https://example.com/fw") == {
            "type": "text",
            "text": "firewatch",
            "marks": [{"type": "link", "attrs": {"href": "https://example.com/fw"}}],
        }

    def test_bold_link_combines_marks_in_order(self):
        assert inline_text("label", bold=True, url="https://x.test") == {
            "type": "text",
            "text": "label",
            "marks": [
                {"type": "strong"},
                {"type": "link", "attrs": {"href": "https://x.test"}},
            ],
        }


class TestMention:
    def test_mention_uses_cloud_account_id_and_display_stub(self):
        account_id = "5b10a" + "2844b82e0069f46e23a"
        assert adf_mention(account_id, "@User Name") == {
            "type": "mention",
            "attrs": {
                "id": account_id,
                "text": "@User Name",
            },
        }


class TestSanitizeJiraAdfDoc:
    def test_empty_text_node_becomes_space(self):
        doc = adf_doc(paragraph(inline_text("")))
        out = sanitize_jira_adf_doc(doc)
        assert out["content"][0]["content"][0]["text"] == " "

    def test_none_text_node_becomes_space(self):
        doc = {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text"}]}],
        }
        out = sanitize_jira_adf_doc(doc)
        assert out["content"][0]["content"][0]["text"] == " "

    def test_strips_nul_bytes_from_text(self):
        doc = adf_doc(paragraph(inline_text("a\x00b")))
        out = sanitize_jira_adf_doc(doc)
        assert out["content"][0]["content"][0]["text"] == "ab"

    def test_heading_with_empty_content_gets_placeholder(self):
        doc = {"type": "doc", "version": 1, "content": [{"type": "heading", "attrs": {"level": 4}, "content": []}]}
        out = sanitize_jira_adf_doc(doc)
        assert out["content"][0]["content"] == [{"type": "text", "text": " "}]

    def test_keeps_strong_mark_when_dropping_invalid_link(self):
        raw = {
            "type": "text",
            "text": "x",
            "marks": [
                {"type": "strong"},
                {"type": "link", "attrs": {"href": ""}},
            ],
        }
        fixed = sanitize_jira_adf_doc({
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [raw]}],
        })
        node = fixed["content"][0]["content"][0]
        assert node["marks"] == [{"type": "strong"}]

    def test_strips_link_mark_when_href_empty(self):
        raw = {
            "type": "text",
            "text": "x",
            "marks": [{"type": "link", "attrs": {"href": ""}}],
        }
        fixed = sanitize_jira_adf_doc({
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [raw]}],
        })
        assert "marks" not in fixed["content"][0]["content"][0]

    def test_empty_paragraph_gets_placeholder_text(self):
        doc = {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": []}]}
        out = sanitize_jira_adf_doc(doc)
        assert out["content"][0]["content"] == [{"type": "text", "text": " "}]


class TestDescriptionToPlainTextForSearch:
    def test_none_returns_empty(self):
        assert description_to_plain_text_for_search(None) == ""

    def test_plain_string_passthrough(self):
        assert description_to_plain_text_for_search("plain") == "plain"

    def test_block_without_content_list_yields_empty_for_unknown_node(self):
        assert description_to_plain_text_for_search({"type": "rule"}) == ""

    def test_includes_mention_stub(self):
        doc = adf_doc(paragraph(adf_mention("acc-1", "@qa")))
        assert "@qa" in description_to_plain_text_for_search(doc)

    def test_hard_break_inserts_newline(self):
        doc = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "a"},
                        {"type": "hardBreak"},
                        {"type": "text", "text": "b"},
                    ],
                },
            ],
        }
        assert description_to_plain_text_for_search(doc) == "a\nb"

    def test_non_doc_dict_uses_recursive_plain_text(self):
        block = {"type": "paragraph", "content": [{"type": "text", "text": "only"}]}
        assert description_to_plain_text_for_search(block) == "only"

    def test_non_dict_non_str_returns_empty(self):
        assert description_to_plain_text_for_search(0) == ""  # type: ignore[arg-type]


class TestClosedByFirewatchAdf:
    def test_returns_doc_with_link_to_repo(self):
        doc = closed_by_firewatch_adf()
        assert doc["type"] == "doc"
        assert doc["version"] == 1
        assert "firewatch" in description_to_plain_text_for_search(doc)


class TestComposedDocument:
    def test_doc_with_heading_paragraph_and_mixed_inline(self):
        doc = adf_doc(
            heading(4, inline_text("Title")),
            paragraph(
                inline_text("See "),
                inline_text("docs", url="https://docs.example.com"),
                inline_text(" and "),
                adf_mention("acc-1", "@qa"),
                inline_text("."),
            ),
        )
        assert doc["type"] == "doc"
        assert doc["version"] == 1
        assert len(doc["content"]) == 2
        assert doc["content"][0]["type"] == "heading"
        assert doc["content"][1]["type"] == "paragraph"
        mention = doc["content"][1]["content"][3]
        assert mention["type"] == "mention"
        assert mention["attrs"]["id"] == "acc-1"
