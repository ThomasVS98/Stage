import pytest
from ingestion.loaders.sharepoint_external_links_loader import (
    scrape_page,
    is_valid_external
)
from unittest.mock import patch, MagicMock

def test_valid_url():
    assert is_valid_external("http://example.com") is True

def test_invalid_scheme():
    assert is_valid_external("ftp://example.com") is False

def test_no_host():
    assert is_valid_external("http:///path") is False

def test_localhost_blocked():
    assert is_valid_external("http://localhost/test") is False

def test_private_ip_blocked():
    assert is_valid_external("http://192.168.1.1") is False

def test_loopback_ip_blocked():
    assert is_valid_external("http://127.0.0.1") is False

def test_bad_paths_blocked():
    assert is_valid_external("https://example.com/login") is False

def test_block_sharepoint():
    assert is_valid_external("https://tenant.sharepoint.com/page") is False

def test_block_microsoftonline():
    assert is_valid_external("https://login.microsoftonline.com") is False

def test_block_topdesk():
    assert is_valid_external("https://company.topdesk.net") is False

def test_block_canvas():
    assert is_valid_external("https://canvas.instructure.com") is False

@patch("ingestion.loaders.sharepoint_external_links_loader.requests.get")
def test_scrape_page_success(mock_get):
    html = "<html><head><title>Test</title></head><body><main><p>Hello</p></main></body></html>"

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.text = html
    mock_res.url = "http://example.com"

    mock_get.return_value = mock_res

    text,title = scrape_page("http://example.com")

    assert "Hello" in text
    assert title == "Test"

@patch("ingestion.loaders.sharepoint_external_links_loader.requests.get")
@patch("ingestion.loaders.sharepoint_external_links_loader.is_valid_external")
def test_scrape_page_redirect_blocked(mock_valid, mock_get):
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.text = "<html></html>"
    mock_res.url = "http://localhost"

    mock_get.return_value = mock_res
    mock_valid.return_value = False

    text, title = scrape_page("https://example.com")

    assert text == ""
    assert title == "Externe pagina"

@patch("ingestion.loaders.sharepoint_external_links_loader.requests.get")
def test_scrape_page_bad_status(mock_get):
    mock_res = MagicMock()
    mock_res.status_code = 404
    mock_res.url = "https://example.com"

    mock_get.return_value = mock_res

    text, title = scrape_page("https://example.com")

    assert text == ""
    assert title == "Externe pagina"

@patch("ingestion.loaders.sharepoint_external_links_loader.requests.get")
def test_scrape_page_fallback_body(mock_get):
    html = "<html><head><title>T</title></head><body><p>Body content</p></body></html>"

    mock_res = MagicMock(status_code=200, text=html, url="https://example.com")
    mock_get.return_value = mock_res

    text, _ = scrape_page("https://example.com")

    assert "Body content" in text

@patch("ingestion.loaders.sharepoint_external_links_loader.requests.get")
def test_scrape_page_exception(mock_get):
    mock_get.side_effect = Exception("fail")

    text, title = scrape_page("https://example.com")

    assert text == ""
    assert title == "Externe pagina"

@patch("ingestion.loaders.sharepoint_external_links_loader.requests.get")
def test_scrape_page_no_title(mock_get):
    html = "<html><body><main><p>Text</p></main></body></html>"

    mock_res = MagicMock(status_code=200, text=html, url="https://example.com")
    mock_get.return_value = mock_res

    _, title = scrape_page("https://example.com")

    assert title == "Externe pagina"

