from unittest.mock import patch, mock_open
import sys

@patch("builtins.open", new_callable=mock_open)
@patch("ingestion.preprocessing.docling_worker.extract_with_docling")
def test_docling_worker_main(mock_extract, mock_file):
    mock_extract.return_value = "output text"

    with patch.object(sys, "argv", ["script.py", "input.pdf", "output.txt"]):
        from ingestion.preprocessing.docling_worker import main
        main()

    mock_extract.assert_called_once_with("input.pdf")
    mock_file().write.assert_called_once_with("output text")