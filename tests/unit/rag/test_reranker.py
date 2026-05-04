import pytest
import rag.reranker as reranker_module
from rag.reranker import get_reranker, rerank_nodes
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def reset_reranker():
    reranker_module._reranker = None


def test_get_reranker_called_once():
    with patch("rag.reranker.SentenceTransformerRerank") as mock_reranker:
        instance = mock_reranker.return_value

        r1 = get_reranker()
        r2 = get_reranker()

        assert r1 is instance
        assert r2 is instance

        mock_reranker.assert_called_once()


def test_get_reranker_configuration():
    with patch("rag.reranker.SentenceTransformerRerank") as mock_reranker:
        get_reranker()

        _, kwargs = mock_reranker.call_args

        assert kwargs.get("model") == "BAAI/bge-reranker-v2-m3"
        assert isinstance(kwargs.get("top_n"), int)
        assert kwargs.get("top_n") > 0


@patch("rag.reranker.get_reranker")
def test_rerank_nodes_filters_by_score(mock_get_reranker):
    mock_reranker = MagicMock()
    mock_get_reranker.return_value = mock_reranker

    node1 = MagicMock(score=0.8)
    node2 = MagicMock(score=0.3)

    mock_reranker.postprocess_nodes.return_value = [node1, node2]

    result = rerank_nodes(["input"], "query", threshold=0.5)

    assert result == [node1]


@patch("rag.reranker.get_reranker")
def test_rerank_nodes_ignores_none_scores(mock_get_reranker):
    mock_reranker = MagicMock()
    mock_get_reranker.return_value = mock_reranker

    node1 = MagicMock(score=None)
    node2 = MagicMock(score=0.9)

    mock_reranker.postprocess_nodes.return_value = [node1, node2]

    result = rerank_nodes(["input"], "query")

    assert result == [node2]


@patch("rag.reranker.get_reranker")
def test_rerank_nodes_all_filtered(mock_get_reranker):
    mock_reranker = MagicMock()
    mock_get_reranker.return_value = mock_reranker

    node1 = MagicMock(score=0.2)
    node2 = MagicMock(score=0.3)

    mock_reranker.postprocess_nodes.return_value = [node1, node2]

    result = rerank_nodes(["input"], "query", threshold=0.5)

    assert result == []


@patch("rag.reranker.get_reranker")
def test_rerank_nodes_calls_postprocess(mock_get_reranker):
    mock_reranker = MagicMock()
    mock_get_reranker.return_value = mock_reranker

    mock_reranker.postprocess_nodes.return_value = []

    rerank_nodes(["input"], "query")

    mock_reranker.postprocess_nodes.assert_called_once()
