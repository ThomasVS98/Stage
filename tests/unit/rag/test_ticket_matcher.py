from unittest.mock import patch, MagicMock
from rag.ticket_matcher import find_similar_ticket


@patch("rag.ticket_matcher.get_index")
def test_find_similar_ticket_no_index(mock_get_index):
    mock_get_index.return_value = None

    result = find_similar_ticket({"beschrijving": "test"})

    assert result is None


@patch("rag.ticket_matcher.rerank_nodes")
@patch("rag.ticket_matcher.retrieve_nodes")
@patch("rag.ticket_matcher.get_index")
def test_find_similar_ticket_no_nodes(mock_get_index, mock_retrieve, mock_rerank):
    mock_get_index.return_value = "index"
    mock_retrieve.return_value = []
    mock_rerank.return_value = []

    result = find_similar_ticket({"beschrijving": "test"})

    assert result is None


@patch("rag.ticket_matcher.rerank_nodes")
@patch("rag.ticket_matcher.retrieve_nodes")
@patch("rag.ticket_matcher.get_index")
def test_find_similar_ticket_below_threshold(
    mock_get_index, mock_retrieve, mock_rerank
):
    mock_get_index.return_value = "index"

    node = MagicMock()
    node.score = 0.5

    mock_retrieve.return_value = ["node"]
    mock_rerank.return_value = [node]

    result = find_similar_ticket({"beschrijving": "test"})

    assert result is None


@patch("rag.ticket_matcher.rerank_nodes")
@patch("rag.ticket_matcher.retrieve_nodes")
@patch("rag.ticket_matcher.get_index")
def test_find_similar_ticket_success(mock_get_index, mock_retrieve, mock_rerank):
    mock_get_index.return_value = "index"

    mock_node_inner = MagicMock()
    mock_node_inner.get_content.return_value = "oplossing"

    node = MagicMock()
    node.score = 0.8
    node.node = mock_node_inner

    mock_retrieve.return_value = ["node"]
    mock_rerank.return_value = [node]

    result = find_similar_ticket({"beschrijving": "test"})

    assert result == {"score": 0.8, "text": "oplossing"}


@patch("rag.ticket_matcher.rerank_nodes")
@patch("rag.ticket_matcher.retrieve_nodes")
@patch("rag.ticket_matcher.get_index")
def test_find_similar_ticket_query_format(mock_get_index, mock_retrieve, mock_rerank):
    mock_get_index.return_value = "index"
    mock_retrieve.return_value = []
    mock_rerank.return_value = []

    data = {"beschrijving": "probleem", "context": "extra", "doel": "oplossen"}

    find_similar_ticket(data)

    args, _ = mock_retrieve.call_args
    query = args[1]

    assert "probleem" in query
    assert "extra" in query
    assert "oplossen" in query
