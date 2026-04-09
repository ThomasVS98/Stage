from ingestion.loaders.topdesk_loader import (
    has_usable_content, 
    topdesk_items_to_documents,
    incidents_to_documents,
    html_to_markdown,
    fetch_topdesk_knowledge_items
    )
from unittest.mock import patch, MagicMock
from config.settings import settings

@patch("ingestion.loaders.topdesk_loader.requests.get")
def test_fetch_topdesk_knowledge_items_pagination(mock_get):
    """Test of de loader correct de volgende link volgt bij meerdere pagina's."""
    settings.TOPDESK_BASE_URL = "https://example.topdesk.net"
    settings.TOPDESK_USER = "user"
    settings.TOPDESK_SECRET = "secret"

    res1 = MagicMock()
    res1.json.return_value = {
        "item": [{
            "id": "1",
            "translation": {
                "content": {
                    "content": "Doc 1"
                }
            }
        }],
        "next": "https://example.topdesk.net/volgende-pagina"
    }
    res1.raise_for_status.return_value = None

    res2 = MagicMock()
    res2.json.return_value = {
        "item": [{
            "id": "2",
            "translation": {
                "content": {
                    "content": "Doc 2"
                }
            }
        }],
        "next": None
    }
    res2.raise_for_status.return_value = None

    mock_get.side_effect = [res1, res2]

    items = fetch_topdesk_knowledge_items()

    assert len(items) == 2
    assert items[0]["id"] == "1"
    assert items[1]["id"] == "2"
    assert mock_get.call_count == 2


def test_has_usable_content_true():
    item = {
        "translation": {
            "content": {
                "content": "Dit is tekst"
            }
        }
    }

    assert has_usable_content(item) is True

def test_has_usable_content_empty():
    item = {
        "translation": {
            "content": {
                "content": " "
            }
        }
    }

    assert has_usable_content(item) is False

def test_has_usable_content_missing_structure():
    item = {}

    assert has_usable_content(item) is False

def test_topdesk_items_to_documents_basic():
    items = [
        {
            "id": "1",
            "number": "INC001",
            "translation": {
                "content": {
                    "title": "Test titel",
                    "description": "<p>Beschrijving</p>",
                    "content": "<p>Inhoud</p>",
                    "keywords": "test,keyword"
                }
            }
        }
    ]

    docs = topdesk_items_to_documents(items)
    assert len(docs) == 1

    doc = docs[0]
    assert "Test titel" in doc.text
    assert "Beschrijving" in doc.text
    assert "Inhoud" in doc.text
    assert "Trefwoorden" in doc.text
    assert doc.metadata["source"] == "topdesk"
    assert doc.metadata["source_type"] == "topdesk_kb"
    assert doc.metadata["source_id"] == "1"
    assert doc.metadata["number"] == "INC001"

def test_topdesk_items_to_documents_empty_skipped():
    items = [
        {
            "id": "1",
            "number": "INC001",
            "translation": {
                "content": {
                    "title": "",
                    "description": "",
                    "content": "",
                    "keywords": ""
                }
            }
        }
    ]

    docs = topdesk_items_to_documents(items)
    assert len(docs) == 0

def test_topdesk_items_to_documents_partial_content():
    items = [
        {
            "id": "1",
            "number": "INC001",
            "translation": {
                "content": {
                    "title": "Titel only",
                    "description": "",
                    "content": "",
                    "keywords": ""
                }
            }
        }
    ]
    
    docs = topdesk_items_to_documents(items)
    assert len(docs) == 1
    assert "Titel only" in docs[0].text

def test_incidents_to_documents_basic():
    items = [
        {
            "id": "1",
            "number": "INC001",
            "briefDescription": "Laptop werkt niet",
            "request": "Kan niet opstarten"
        }
    ]

    docs = incidents_to_documents(items)
    assert len(docs) == 1

    doc = docs[0]
    assert "Laptop werkt niet" in doc.text
    assert "Kan niet opstarten" in doc.text
    assert doc.metadata["source"] == "topdesk"
    assert doc.metadata["source_type"] == "incident"
    assert doc.metadata["source_id"] == "1"

def test_incidents_to_documents_empty_skipped():
    items = [
        {
            "id": "1",
            "number": "INC001",
            "briefDescription": "",
            "request": ""
        }
    ]

    docs = incidents_to_documents(items)
    assert len(docs) == 0

def test_incidents_to_documents_only_description():
    items = [
        {
            "id": "1",
            "number": "INC001",
            "briefDescription": "Printer stuk",
            "request": ""
        }
    ]
    docs = incidents_to_documents(items)
    assert len(docs) == 1
    assert "Printer stuk" in docs[0].text

def test_incidents_to_documents_only_request():
    items = [
        {
            "id": "1",
            "number": "INC001",
            "briefDescription": "",
            "request": "Papier blijft vastzitten"
        }
    ]

    docs = incidents_to_documents(items)
    assert len(docs) == 1
    assert "Papier blijft vastzitten" in docs[0].text

def test_html_to_markdown():
    html = "<h1>Titel</h1><p>Tekst met <b>vet</b> en &amp; teken.</p><ul><li>Item 1</li><li>Item 2</li></ul>"
    md_text = html_to_markdown(html)
    
    # Check voor de header (ATX stijl: #)
    assert "# Titel" in md_text
    # Check voor vetgedrukte tekst
    assert "vet" in md_text
    # Check of HTML entities zijn vervangen
    assert "&" in md_text
    # Check of de lijst herkenbaar is
    assert "- Item 1" in md_text
    assert "- Item 2" in md_text

def test_html_to_markdown_empty_input():
    """Controleert of lege input ook een lege string teruggeeft zonder te crashen."""
    assert html_to_markdown("") == ""
    assert html_to_markdown(None) == ""