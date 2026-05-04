from ingestion.processing.file_processor import create_document_from_file, process_file
from unittest.mock import patch, MagicMock, mock_open
import sys


def test_create_document_from_file_basic():
    content = "Test content"
    metadata = {"source": "test", "download_url": "abc"}

    doc = create_document_from_file(content, metadata)

    assert doc is not None
    assert doc.text == "Test content"
    assert doc.metadata["source"] == "test"
    assert "download_url" not in doc.metadata


def test_create_document_from_file_empty():
    doc = create_document_from_file("  ", {"source": "test"})

    assert doc is None


def test_create_document_sets_default_source_type():
    doc = create_document_from_file("content", {"source": "test"})

    assert doc.metadata["source_type"] == "file"


def test_create_document_metadata_exclusions():
    metadata = {"source": "test", "url": "secret_url", "source_id": "123"}
    doc = create_document_from_file("content", metadata)

    assert "url" in doc.excluded_embed_metadata_keys
    assert "download_url" in doc.excluded_embed_metadata_keys
    assert "source_id" in doc.excluded_embed_metadata_keys

    assert "url" in doc.excluded_llm_metadata_keys
    assert "filename" in doc.excluded_llm_metadata_keys


@patch("ingestion.processing.file_processor.SimpleDirectoryReader")
def test_process_file_non_pdf(mock_reader):
    mock_doc = MagicMock()
    mock_doc.text = "File content"

    mock_reader.return_value.load_data.return_value = [mock_doc]

    result = process_file("file.txt", "file.txt")

    assert "File content" in result


@patch("ingestion.processing.file_processor.subprocess.run")
@patch("ingestion.processing.file_processor.clean_markdown")
@patch("ingestion.processing.file_processor.clean_text")
def test_process_file_pdf_uses_docling_worker_and_cleaning(
    mock_clean_text, mock_clean_md, mock_run
):

    mock_clean_md.return_value = "raw content"
    mock_clean_text.return_value = "clean content"

    with patch("builtins.open", mock_open(read_data="raw content")):
        result = process_file("file.pdf", "file.pdf")

    assert result == "clean content"

    mock_run.assert_called_once()

    args = mock_run.call_args[0][0]

    assert sys.executable in args[0]
    assert "docling_worker.py" in args[1]
    assert "file.pdf" in args[2]


@patch("ingestion.processing.file_processor.SimpleDirectoryReader")
def test_process_file_exception(mock_reader):
    mock_reader.side_effect = Exception("fail")

    result = process_file("file.txt", "file.txt")

    assert result == ""


@patch("ingestion.processing.file_processor.subprocess.run")
@patch("ingestion.processing.file_processor.clean_markdown")
@patch("ingestion.processing.file_processor.clean_text")
def test_process_file_docx_uses_subprocess(mock_clean_text, mock_clean_md, mock_run):
    with patch("builtins.open", mock_open(read_data="docx content")):
        process_file("test.docx", "test.docx")

    args = mock_run.call_args[0][0]

    assert sys.executable in args[0]
    assert "docling_worker.py" in args[1]
    assert "test.docx" in args[2]


@patch("ingestion.processing.file_processor.tempfile.NamedTemporaryFile")
@patch("ingestion.processing.file_processor.os.path.exists")
@patch("ingestion.processing.file_processor.os.remove")
@patch("ingestion.processing.file_processor.subprocess.run")
def test_process_file_cleanup_on_failure(
    mock_run, mock_remove, mock_exists, mock_tempfile
):
    mock_exists.return_value = True
    mock_run.side_effect = Exception("Subprocess crashed")

    mock_temp = MagicMock()
    mock_temp.name = "/temp/tempfile.pdf"
    mock_tempfile.return_value.__enter__.return_value = mock_temp

    process_file("file.pdf", "file.pdf")

    mock_exists.assert_called_once()
    mock_remove.assert_called_once_with("/temp/tempfile.pdf")


@patch("ingestion.processing.file_processor.SimpleDirectoryReader")
@patch("ingestion.processing.file_processor.clean_text")
def test_process_file_calls_cleaning_on_text_files(mock_clean, mock_reader):
    mock_doc = MagicMock()
    mock_doc.text = "Raw content"
    mock_reader.return_value.load_data.return_value = [mock_doc]
    mock_clean.return_value = "Cleaned content"

    result = process_file("file.txt", "file.txt")

    mock_clean.assert_called_once_with("Raw content")
    assert result == "Cleaned content"
