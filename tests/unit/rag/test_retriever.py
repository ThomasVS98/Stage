from unittest.mock import MagicMock
from rag.retriever import retrieve_nodes


def test_retrieve_nodes_calls_retriever():
    mock_index = MagicMock()
    mock_retriever = MagicMock()

    mock_index.as_retriever.return_value = mock_retriever
    mock_retriever.retrieve.return_value = ["node1", "node2"]

    result = retrieve_nodes(mock_index, "test query")

    assert result == ["node1", "node2"]

    mock_index.as_retriever.assert_called_once_with(similarity_top_k=25, filters=None)

    mock_retriever.retrieve.assert_called_once_with("test query")


def test_retrieve_nodes_returns_empty_list():
    mock_index = MagicMock()
    mock_retriever = MagicMock()

    mock_index.as_retriever.return_value = mock_retriever
    mock_retriever.retrieve.return_value = []

    result = retrieve_nodes(mock_index, "query")

    assert result == []
