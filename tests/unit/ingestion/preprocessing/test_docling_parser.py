from ingestion.preprocessing.docling_parser import extract_with_docling
from unittest.mock import patch, MagicMock

@patch("ingestion.preprocessing.docling_parser.get_converter")
def test_extract_with_docling_success(mock_get_converter):
    mock_converter = MagicMock()
    mock_get_converter.return_value = mock_converter

    mock_result  = MagicMock()
    mock_result.document.export_to_markdown.return_value = "Test output"
    
    mock_converter.convert.return_value = mock_result

    result = extract_with_docling("file.pdf")

    assert result == "Test output"
    mock_converter.convert.assert_called_once_with("file.pdf")

@patch("ingestion.preprocessing.docling_parser.get_converter")
def test_extract_with_docling_exception(mock_get_converter):
    mock_converter = MagicMock()
    mock_get_converter.return_value = mock_converter
    mock_converter.convert.side_effect = Exception("fail")

    result = extract_with_docling("file.pdf")

    assert result == ""

@patch("ingestion.preprocessing.docling_parser.get_converter")
def test_extract_with_docling_strips_output(mock_get_converter):
    mock_converter = MagicMock()
    mock_get_converter.return_value = mock_converter

    mock_result = MagicMock()
    mock_result.document.export_to_markdown.return_value = " tekst \n"

    mock_converter.convert.return_value = mock_result

    result = extract_with_docling("file.pdf")

    assert result == "tekst"

@patch("ingestion.preprocessing.docling_parser.gc.collect")
@patch("ingestion.preprocessing.docling_parser.get_converter")
def test_extract_with_docling_calls_gc(mock_get_converter, mock_gc):
    mock_converter = MagicMock()
    mock_get_converter.return_value = mock_converter

    mock_result = MagicMock()
    mock_result.document.export_to_markdown.return_value = "text"
    mock_converter.convert.return_value = mock_result

    extract_with_docling("file.pdf")

    mock_gc.assert_called_once()
