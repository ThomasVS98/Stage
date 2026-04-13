from rag.pipeline import run_rag
from unittest.mock import patch, MagicMock

@patch("rag.pipeline.get_index")
def test_run_rag_no_index(mock_get_index):
    mock_get_index.return_value = None

    nodes, answer = run_rag("test vraag")

    assert nodes is None
    assert answer is None

@patch("rag.pipeline.retrieve_nodes")
@patch("rag.pipeline.get_index")
def test_run_rag_no_nodes(mock_get_index, mock_retrieve):
    mock_get_index.return_value = "fake_index"
    mock_retrieve.return_value = []

    nodes, answer = run_rag("test vraag")

    assert nodes == []
    assert answer is None

@patch("rag.pipeline.rerank_nodes")
@patch("rag.pipeline.retrieve_nodes")
@patch("rag.pipeline.get_index")
def test_run_rag_no_valid_nodes(mock_get_index, mock_retrieve, mock_rerank):
    mock_get_index.return_value = "fake_index"
    mock_retrieve.return_value = ["node1"]
    mock_rerank.return_value = []

    nodes, answer = run_rag("test vraag")

    assert nodes == []
    assert answer is None


@patch("rag.pipeline.get_llm")
@patch("rag.pipeline.generate_answer")
@patch("rag.pipeline.build_context")
@patch("rag.pipeline.rerank_nodes")
@patch("rag.pipeline.retrieve_nodes")
@patch("rag.pipeline.get_index")
def test_run_rag_success(
    mock_get_index,
    mock_retrieve,
    mock_rerank,
    mock_build_context,
    mock_generate_answer,
    mock_get_llm
):
    
    mock_get_index.return_value = "fake_index"
    mock_retrieve.return_value = ["node1"]
    mock_rerank.return_value = ["node1"]
    mock_build_context.return_value = "fake_context"
    mock_get_llm.return_value = "fake_llm"

    token1 = MagicMock()
    token1.delta = "Hello "

    token2 = MagicMock()
    token2.delta = "world"

    mock_generate_answer.return_value = [token1, token2]

    nodes,answer = run_rag("test vraag")

    assert nodes == ["node1"]
    assert answer == "Hello world"

    mock_generate_answer.assert_called_once_with(
        "fake_llm", 
        "fake_context", 
        "test vraag"
    )

@patch("rag.pipeline.get_llm")
@patch("rag.pipeline.generate_answer")
@patch("rag.pipeline.build_context")
@patch("rag.pipeline.rerank_nodes")
@patch("rag.pipeline.retrieve_nodes")
@patch("rag.pipeline.get_index")
def test_run_rag_ignores_empty_token(
    mock_get_index,
    mock_retrieve,
    mock_rerank,
    mock_build_context,
    mock_generate_answer,
    mock_get_llm
):
    
    mock_get_index.return_value = "fake_index"
    mock_retrieve.return_value = ["node1"]
    mock_rerank.return_value = ["node1"]
    mock_build_context.return_value = "fake_context"
    mock_get_llm.return_value = "fake_llm"

    token1 = MagicMock()
    token1.delta = None

    token2 = MagicMock()
    token2.delta = "Hi"

    token3 = MagicMock()
    token3.delta = ""

    mock_generate_answer.return_value = [token1, token2, token3]

    nodes, answer = run_rag("test vraag")

    assert answer == "Hi"

@patch("rag.pipeline.get_index")
def test_run_rag_uses_custom_collection(mock_get_index):
    mock_get_index.return_value = None
    run_rag("vraag", collection="tickets")
    mock_get_index.assert_called_once_with("tickets")

