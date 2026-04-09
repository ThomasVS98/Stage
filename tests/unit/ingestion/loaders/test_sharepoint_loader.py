from ingestion.loaders.sharepoint_loader import (
    html_to_markdown,
    build_folder_url,
    extract_page_content,
    fetch_all_sharepoint_pages,
    fetch_sharepoint_files
)
from unittest.mock import patch, MagicMock
from config.settings import settings

def test_html_to_markdown_basic():
    html = "<p>Test <b>tekst</b></p>"

    text, links = html_to_markdown(html)

    assert "Test **tekst**" in text
    assert links == []

def test_html_to_markdown_links():
    settings.SHAREPOINT_BASE_URL = "https://example.com"

    html = '<a href="/path">Klik hier</a>'

    text, links = html_to_markdown(html)

    assert "Klik hier" in text
    assert len(links) == 1
    assert links[0]["url"] == "https://example.com/path"

def test_html_to_markdown_ignores_js_links():
    html = '<a href="javascript:void(0)">Klik</a>'

    text, links = html_to_markdown(html)

    assert len(links) == 0

def test_build_folder_url_root():
    url = build_folder_url("site123", "root")
    assert "root/children" in url

def test_build_folder_url_subfolder():
    url = build_folder_url("site123", "abc")
    assert "items/abc/children" in url

def test_extract_page_content_basic():
    page_details = {
        "canvasLayout": {
            "horizontalSections": [
                {
                    "columns": [
                        {
                            "webparts": [
                                {
                                    "innerHtml": "<p>Inhoudelijke blok tekst</p>"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }

    content_parts, links = extract_page_content(page_details)

    assert len(content_parts) == 1
    assert "Inhoudelijke blok tekst" in content_parts[0]
    assert links == []

def test_extract_page_content_fallback_data():
    page_details = {
        "canvasLayout": {
            "horizontalSections": [
                {
                    "columns": [
                        {
                            "webparts": [
                                {
                                    "data": {
                                        "innerHTML": "<p>Fallback inhoud</p>"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }

    content_parts, links = extract_page_content(page_details)

    assert "Fallback inhoud" in content_parts[0]

@patch("ingestion.loaders.sharepoint_loader.graph_get")
def test_fetch_all_sharepoint_pages_basic(mock_graph_get):
    res_pages = MagicMock()
    res_pages.status_code = 200
    res_pages.json.return_value = {
        "value": [
            {
                "id": "1",
                "title": "Pagina 1",
                "webUrl": "https://example.com/pagina1"
            }
        ]
    }

    res_content = MagicMock()
    res_content.status_code = 200
    res_content.json.return_value = {
        "canvasLayout": {
            "horizontalSections": [
                {
                    "columns": [
                        {
                            "webparts": [
                                {
                                    "innerHtml": "<p>Content test</p>"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }

    mock_graph_get.side_effect = [res_pages, res_content]

    result = fetch_all_sharepoint_pages("site123", "Test Site")
    assert len(result) == 1

    page = result[0]

    assert "Content test" in page["content"]
    assert page["metadata"]["source"] == "sharepoint"
    assert page["metadata"]["title"] == "Pagina 1"
    assert page["metadata"]["site_label"] == "Test Site"

    assert mock_graph_get.call_count == 2

@patch("ingestion.loaders.sharepoint_loader.graph_get")
def test_fetch_all_sharepoint_pages_error(mock_graph_get):
    res_pages = MagicMock()
    res_pages.status_code = 500
    res_pages.text = "Error"

    mock_graph_get.return_value = res_pages

    result = fetch_all_sharepoint_pages("site123", "Test Site")
    assert result == []

@patch("ingestion.loaders.sharepoint_loader.graph_get")
def test_fetch_sharepoint_files_recursive(mock_graph_get):
    """Test of de functie correct recursief door submappen gaat."""

    res_root = MagicMock()
    res_root.status_code = 200
    res_root.json.return_value = {
        "value": [
            {
                "id": "file1",
                "name": "document.pdf",
                "file": {}
            },
            {
                "id": "folder1",
                "name": "Submap",
                "folder": {}
            }
        ]
    }

    res_sub = MagicMock()
    res_sub.status_code = 200
    res_sub.json.return_value = {
        "value": [
            {
                "id": "file2",
                "name": "document2.docx",
                "file": {}
            }
        ]
    }

    mock_graph_get.side_effect = [res_root, res_sub]

    files = fetch_sharepoint_files("site123", "Site label")

    assert len(files) == 2
    assert files[0]["metadata"]["source_id"] == "file1"
    assert files[1]["metadata"]["source_id"] == "file2"
    assert mock_graph_get.call_count == 2
