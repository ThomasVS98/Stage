import pytest
from unittest.mock import patch, MagicMock
from services.intake.intake_service import start, answer
from utils.exceptions import AppValidationError, ExternalServiceError

@patch("services.intake.intake_service.session_store")
def test_start_creates_session(mock_store):
    mock_store.create = MagicMock()
    mock_store.update = MagicMock()

    result = start("Laptop werkt niet")

    assert "session_id" in result
    assert "question" in result

    mock_store.create.assert_called_once()
    mock_store.update.assert_called_once_with(
        result["session_id"],
        "original_question",
        "Laptop werkt niet"
    )

def test_answer_missing_field():
    with pytest.raises(AppValidationError, match="Missing session_id or answer"):
        answer({})

@patch("services.intake.intake_service.session_store")
def test_answer_invalid_session(mock_store):
    mock_store.get.return_value = None

    with pytest.raises(AppValidationError, match="Invalid session"):
        answer({"session_id": "invalid", "answer": "test"})

@patch("services.intake.intake_service.validate_answer", return_value="cleaned")
@patch("services.intake.intake_service.session_store")
def test_answer_next_step(mock_store, mock_validate):
    mock_store.get.return_value = {
        "step": 0,
        "data": {}
    }

    result = answer({
        "session_id": "abc",
        "answer": "test"
    })

    assert result["done"] is False
    assert "question" in result

    mock_store.update.assert_called_once()
    mock_store.increment_step.assert_called_once()

@patch("services.intake.intake_service.is_relevant", return_value=False)
@patch("services.intake.intake_service.session_store")
@patch("services.intake.intake_service.validate_answer", return_value="cleaned")
def test_answer_not_relevant(mock_validate, mock_store, mock_relevant):
    mock_store.get.return_value = {
        "step": 0,
        "data": {"original_question": "vraag"}
    }

    with patch("services.intake.intake_service.INTAKE_QUESTIONS", [("key", "question")]):
        result = answer({
            "session_id": "abc",
            "answer": "test"
        })

    assert result["done"] is True
    assert "error" in result
    assert "lijken niet overeen te komen" in result["error"]

@patch("services.intake.intake_service.find_similar_ticket")
@patch("services.intake.intake_service.is_relevant", return_value=True)
@patch("services.intake.intake_service.session_store")
@patch("services.intake.intake_service.validate_answer", return_value="cleaned")
def test_answer_returns_similar_ticket(mock_validate, mock_store, mock_relevant, mock_match):
    mock_store.get.return_value = {}
