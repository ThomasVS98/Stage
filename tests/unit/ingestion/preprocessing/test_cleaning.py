from ingestion.preprocessing.cleaning import (
    clean_text,
    clean_markdown,
    clean_topdesk_text,
    normalize_text,
)


def test_clean_text_basic():
    text = "Dit  is  tekst"
    result = clean_text(text)

    assert result == "Dit is tekst"


def test_clean_text_newlines():
    text = "Hallo\n\n\n\nwereld"
    result = clean_text(text)

    assert result == "Hallo\n\nwereld"


def test_clean_markdown_removes_image_markers():
    text = "Dit is een afbeelding: <!-- image -->"
    result = clean_markdown(text)

    assert "<!-- image -->" not in result


def test_clean_markdown_newlines():
    text = "Regel 1\n\n\n\nRegel 2"
    result = clean_markdown(text)

    assert result == "Regel 1\n\nRegel 2"


def test_clean_topdesk_text_removes_prefix():
    text = "12-12-2023 10:00 Topdesk: Dit is een test"
    result = clean_topdesk_text(text)

    assert "Topdesk:" not in result
    assert result == "Dit is een test"


def test_clean_topdesk_text_empty():
    assert clean_topdesk_text("") == ""
    assert clean_topdesk_text(None) == ""


def test_clean_topdesk_text_variations():
    assert clean_topdesk_text("01-01-2024 Topdesk: Voorbeeld") == "Voorbeeld"
    assert clean_topdesk_text("Alleen tekst") == "Alleen tekst"


def test_normalize_text_newlines():
    text = "Regel 1\r\nRegel 2\rRegel 3\n\n\nRegel 4"
    result = normalize_text(text)

    assert result == "Regel 1\nRegel 2\nRegel 3\n\nRegel 4"


def test_normalize_text_whitespace():
    text = "Dit  is \t een   test"
    result = normalize_text(text)

    assert result == "Dit is een test"


def test_normalize_text_excessive_newlines():
    text = "Regel 1\n\n\n\nRegel 2"
    result = normalize_text(text)

    assert result == "Regel 1\n\nRegel 2"


def test_normalize_text_tabs_between_newlines():
    text = "Regel1\n   \nRegel 2"
    result = normalize_text(text)
    assert result == "Regel1\n\nRegel 2"
