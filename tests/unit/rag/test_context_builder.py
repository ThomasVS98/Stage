from rag.context_builder import build_context
from unittest.mock import MagicMock

def make_mock_node(text, metadata):
    inner_node = MagicMock()
    inner_node.get_content.return_value = text
    inner_node.metadata = metadata

    outer_node = MagicMock()
    outer_node.node = inner_node

    return outer_node

def test_build_context_single_node():
    node = make_mock_node(
        "Dit is tekst",
        {"title": "Titel", "source": "SharePoint", "url": "http://example.com/1"}
    )

    result = build_context([node])

    assert "[DOCUMENT]" in result
    assert "Titel: Titel" in result
    assert "Bron: SharePoint" in result
    assert "URL: http://example.com/1" in result
    assert "Dit is tekst" in result
    assert result.strip().endswith("[/DOCUMENT]")

def test_build_context_multiple_nodes():
    node1 = make_mock_node("Text1", {"title": "T1"})
    node2 = make_mock_node("Text2", {"title": "T2"})

    result = build_context([node1, node2])

    assert result.count("[DOCUMENT]") == 2
    assert "Text1" in result
    assert "Text2" in result

def test_build_context_missing_metadata():
    node = make_mock_node("Text", {})

    result = build_context([node])

    assert "Geen titel" in result
    assert "Geen bron" in result
    assert "Geen URL" in result

def test_build_context_empty_list():
    result = build_context([])

    assert result == ""