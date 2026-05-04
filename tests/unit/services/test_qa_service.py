from services.qa_service import (
    answer
)
from unittest.mock import patch, MagicMock

@patch("services.qa_service.run_rag")
def test_answer_db_not_initialized(mock_rag):
    mock_rag.return_value = (None, None, None)

    result = answer("test vraag")

    assert "database is nog niet geïnitialiseerd" in result["answer"].lower()
    assert result["sources"] == []

@patch("services.qa_service.detect_intent", return_value="SUPPORT")
@patch("services.qa_service.get_llm")
@patch("services.qa_service.run_rag")
def test_answer_no_results_support(mock_rag, mock_llm, mock_intent):
    mock_rag.return_value = ([], None, None)

    result = answer("help mij")

    assert result["action"] == "INTAKE"
    assert result["sources"] == []
    assert "ticket" in result["answer"].lower()

@patch("services.qa_service.detect_intent", return_value="ALGEMEEN")
@patch("services.qa_service.get_llm")
@patch("services.qa_service.run_rag")
def test_answer_no_results_algemeen(mock_rag, mock_llm, mock_intent):
    mock_rag.return_value = ([], None, None)

    result = answer("algemene vraag")

    assert result["sources"] == []
    assert "niet genoeg informatie" in result["answer"].lower()
    assert "action" not in result

@patch("services.qa_service.detect_intent", return_value="IRRELEVANT")
@patch("services.qa_service.get_llm")
@patch("services.qa_service.run_rag")
def test_answer_no_results_irrelevant(mock_rag, mock_llm, mock_intent):
    mock_rag.return_value = ([], None, None)

    result = answer("random")

    assert result["sources"] == []
    assert "niet relevant" in result["answer"].lower()

@patch("services.qa_service.detect_intent", return_value="UNKNOWN")
@patch("services.qa_service.get_llm")
@patch("services.qa_service.run_rag")
def test_answer_no_results_unknown(mock_rag, mock_llm, mock_intent):
    mock_rag.return_value = ([], None, None)

    result = answer("???")

    assert result["sources"] == []
    assert "niet goed interpreteren" in result["answer"].lower()

@patch("services.qa_service.executor.submit")
@patch("services.qa_service.run_rag")
def test_answer_with_results(mock_rag, mock_submit):
    mock_node = MagicMock()
    mock_node.node.metadata = {
        "title": "Doc1",
        "url": "http://test.com"
    }

    mock_rag.return_value = ([mock_node], "Dit is het antwoord", "context")

    result = answer("vraag")

    assert result["answer"] == "Dit is het antwoord"
    assert result["sources"] == ["Doc1: http://test.com"]
    mock_submit.assert_called_once()

@patch("services.qa_service.executor.submit")
@patch("services.qa_service.run_rag")
def test_answer_with_topdesk_source(mock_rag, mock_submit):
    mock_node = MagicMock()
    mock_node.node.metadata = {
        "title": "Kennis-item 0",
        "source": "topdesk"
    }

    mock_rag.return_value = ([mock_node], "Antwoord", "context")

    result = answer("vraag")

    assert result["answer"] == "Antwoord"
    assert result["sources"] == ["Kennis-item 0 (TOPdesk)"]
    mock_submit.assert_called_once()

@patch("services.qa_service.executor.submit")
@patch("services.qa_service.run_rag")
def test_answer_multiple_sources(mock_rag, mock_submit):
    node1 = MagicMock()
    node1.node.metadata = {
        "title": "Doc1",
        "url": "http://test.com"
    }

    node2 = MagicMock()
    node2.node.metadata = {
        "title": "Kennis-item 0",
        "source": "topdesk"
    }

    mock_rag.return_value = ([node1, node2], "Antwoord", "context")

    result = answer("vraag")

    assert result["sources"] == [
        "Doc1: http://test.com",
        "Kennis-item 0 (TOPdesk)"
    ]
    mock_submit.assert_called_once()