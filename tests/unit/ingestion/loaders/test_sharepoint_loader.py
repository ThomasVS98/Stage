from ingestion.loaders.sharepoint_loader import (
    html_to_markdown,
    build_folder_url,
    extract_page_content,
    fetch_all_sharepoint_pages,
    fetch_sharepoint_files,
    load_sharepoint_source,
    download_sharepoint_file
)
from unittest.mock import patch, MagicMock
from config.settings import settings

def test_html_to_markdown_basic():
    html = "<p>Test <b>tekst</b></p>"

    text, links = html_to_markdown(html)

    assert "Test **tekst**" in text
    assert links == []

def test_html_to_markdown_links(monkeypatch):
    monkeypatch.setattr(settings, "SHAREPOINT_BASE_URL", "https://example.com")

    html = '<a href="/path">Klik hier</a>'

    text, links = html_to_markdown(html)

    assert "Klik hier" in text
    assert len(links) == 1
    assert links[0]["url"] == "https://example.com/path"

    monkeypatch.setattr(settings, "SHAREPOINT_BASE_URL", None)

def test_html_to_markdown_ignores_js_links():
    html = '<a href="javascript:void(0)">Klik</a>'

    text, links = html_to_markdown(html)

    assert len(links) == 0

def test_html_to_markdown_empty():
    text, links = html_to_markdown(None)
    assert text == ""
    assert links == []

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
    assert "links" in page

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

@patch("ingestion.loaders.sharepoint_loader.graph_get")
def test_fetch_sharepoint_files_graph_error(mock_graph_get):
    res = MagicMock(status_code=500, text="fail")
    mock_graph_get.return_value = res

    files = fetch_sharepoint_files("site", "label")
    assert files == []

@patch("ingestion.loaders.sharepoint_loader.graph_get")
def test_fetch_sharepoint_files_ignores_non_supported(mock_graph_get):
    res = MagicMock(status_code=200)
    res.json.return_value = {
        "value": [
            {"id": "1", "name": "image.jpg", "file": {}}
        ]
    }

    mock_graph_get.return_value = res

    files = fetch_sharepoint_files("site", "label")
    assert files == []

@patch("ingestion.loaders.sharepoint_loader.graph_get")
def test_fetch_sharepoint_files_deduplicates(mock_graph_get):
    res = MagicMock(status_code=200)
    res.json.return_value = {
        "value": [
            {"id": "1", "name": "doc.pdf", "file": {}},
            {"id": "1", "name": "doc.pdf", "file": {}}
        ]
    }

    mock_graph_get.return_value = res

    files = fetch_sharepoint_files("site", "label")
    assert len(files) == 1

@patch("ingestion.loaders.sharepoint_loader.graph_get")
def test_fetch_pages_skip_on_bad_content(mock_graph_get):
    res_pages = MagicMock(status_code=200)
    res_pages.json.return_value = {"value": [{"id": "1", "title": "t"}]}

    res_content = MagicMock(status_code=500)

    mock_graph_get.side_effect = [res_pages, res_content]

    result = fetch_all_sharepoint_pages("site", "label")
    assert result == []

@patch("ingestion.loaders.sharepoint_loader.is_valid_external")
@patch("ingestion.loaders.sharepoint_loader.fetch_all_sharepoint_pages")
def test_load_sharepoint_source_external_links_filtered(
    mock_fetch_pages, mock_is_valid
):
    mock_fetch_pages.return_value = [
        {
            "content": "Test pagina",
            "links": [{"url": "https:bad.com"}],
            "metadata": {"title": "Titel"}
        }
    ]

    mock_is_valid.return_value = False

    docs = list(load_sharepoint_source({
        "site_id": "site123",
        "include_external_links": True
    }))

    assert len(docs) == 1

@patch("ingestion.loaders.sharepoint_loader.scrape_page")
@patch("ingestion.loaders.sharepoint_loader.is_valid_external")
@patch("ingestion.loaders.sharepoint_loader.fetch_all_sharepoint_pages")
def test_load_sharepoint_source_external_links_deduplicated(
    mock_fetch_pages, mock_is_valid, mock_scrape
):
    mock_fetch_pages.return_value = [
        {
            "content": "Test pagina",
            "links": [
                {"url": "https://example.com"},
                {"url": "https://example.com/"}
            ],
            "metadata": {"title": "Titel"}
        }
    ]

    mock_is_valid.return_value = True
    mock_scrape.return_value = ("Scraped content", "Titel")

    docs = list(load_sharepoint_source({
        "site_id": "site123",
        "include_external_links": True
    }))

    assert len(docs) == 2

@patch("ingestion.loaders.sharepoint_loader.fetch_all_sharepoint_pages")
def test_load_sharepoint_source_without_external_links(mock_fetch_pages):

    mock_fetch_pages.return_value = [
        {
            "content": "Test pagina",
            "links": [{"url": "https://example.com"}],
            "metadata": {"title": "Titel"}
        }
    ]

    docs = list(load_sharepoint_source({
        "site_id": "site123",
        "include_external_links": False
    }))

    assert len(docs) == 1

@patch("ingestion.loaders.sharepoint_loader.scrape_page")
@patch("ingestion.loaders.sharepoint_loader.is_valid_external")
@patch("ingestion.loaders.sharepoint_loader.fetch_all_sharepoint_pages")
def test_load_sharepoint_source_external_links_empty_content(
    mock_fetch_pages, mock_is_valid, mock_scrape
):
    mock_fetch_pages.return_value = [
        {
            "content": "Test pagina",
            "links": [{"url": "https://example.com"}],
            "metadata": {"title": "Titel"}
        }
    ]

    mock_is_valid.return_value = True
    mock_scrape.return_value = ("", "Titel")

    docs = list(load_sharepoint_source({
        "site_id": "site123",
        "include_external_links": True
    }))

    assert len(docs) == 2
    assert "Externe pagina" in docs[1].text


@patch("ingestion.loaders.sharepoint_loader.scrape_page")
@patch("ingestion.loaders.sharepoint_loader.is_valid_external")
@patch("ingestion.loaders.sharepoint_loader.fetch_all_sharepoint_pages")
def test_load_sharepoint_source_external_links_limit(
    mock_fetch_pages, mock_is_valid, mock_scrape
):
    mock_fetch_pages.return_value = [
        {
            "content": "Test pagina",
            "links": [{"url": f"https://example{i}.com"} for i in range(5)],
            "metadata": {"title": "Titel"}
        }
    ]

    mock_is_valid.return_value = True
    mock_scrape.return_value = ("Content", "Titel")

    docs = list(load_sharepoint_source({
        "site_id": "site123",
        "include_external_links": True
    }))

    assert len(docs) == 4

@patch("ingestion.loaders.sharepoint_loader.scrape_page")
@patch("ingestion.loaders.sharepoint_loader.is_valid_external")
@patch("ingestion.loaders.sharepoint_loader.fetch_all_sharepoint_pages")
def test_load_sharepoint_source_external_links_scrape_error(
    mock_fetch_pages, mock_is_valid, mock_scrape
):
    mock_fetch_pages.return_value = [
        {
            "content": "Test pagina",
            "links": [{"url": "https://example.com"}],
            "metadata": {"title": "Titel"}
        }
    ]

    mock_is_valid.return_value = True
    mock_scrape.side_effect = Exception("fail")

    docs = list(load_sharepoint_source({
        "site_id": "site123",
        "include_external_links": True
    }))

    assert len(docs) == 1

@patch("ingestion.loaders.sharepoint_loader.fetch_sharepoint_files")
@patch("ingestion.loaders.sharepoint_loader.download_sharepoint_file")
@patch("ingestion.loaders.sharepoint_loader.process_file")
@patch("ingestion.loaders.sharepoint_loader.create_document_from_file")
@patch("os.remove")
def test_load_sharepoint_source_file_flow(
    mock_remove,
    mock_create_doc,
    mock_process,
    mock_download,
    mock_fetch_files
):
    mock_fetch_files.return_value = [
        {
            "metadata": {
                "filename": "test.pdf",
                "download_url": "url",
                "source": "sharepoint"
            }
        }
    ]

    mock_download.return_value = True
    mock_process.return_value = "file content"

    mock_doc = MagicMock()
    mock_create_doc.return_value = mock_doc

    list(load_sharepoint_source({
        "site_id": "site123",
        "include_external_links": False
    }))

    assert mock_create_doc.call_count == 1

@patch("requests.get")
def test_download_sharepoint_file_success(mock_get, tmp_path):
    mock_get.return_value.status_code = 200
    mock_get.return_value.content = b"data"

    file_path = tmp_path / "test.txt"

    result = download_sharepoint_file("url", str(file_path))
    assert result is True
    assert file_path.exists()

@patch("requests.get")
def test_download_sharepoint_file_fail_status(mock_get, tmp_path):
    mock_get.return_value.status_code = 404

    result = download_sharepoint_file("url", str(tmp_path / "file.txt"))
    assert result is False

@patch("requests.get")
def test_download_sharepoint_file_exception(mock_get, tmp_path):
    mock_get.side_effect = Exception("fail")

    result = download_sharepoint_file("url", str(tmp_path / "file.txt"))
    assert result is False

def test_load_sharepoint_source_no_site_id():
    docs = list(load_sharepoint_source({}))
    assert docs == []
