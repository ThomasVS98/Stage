import json
from unittest.mock import patch, mock_open
from services.feedback_service import save_feedback
from fastapi.testclient import TestClient
from api.main import app
import pytest

@pytest.fixture
def client():
    return TestClient(app)

@patch("services.feedback_service.open", new_callable=mock_open)
def test_save_feedback_writes_file(mock_file):
    save_feedback("vraag", "antwoord", "up")

    mock_file.assert_called_once_with("feedback.jsonl", "a", encoding="utf-8")

    handle = mock_file()
    handle.write.assert_called_once()

    written = handle.write.call_args[0][0]
    data = json.loads(written.strip())

    assert data["query"] == "vraag"
    assert data["answer"] == "antwoord"
    assert data["score"] == "up"
    assert "timestamp" in data

@patch("services.feedback_service.logger")
@patch("services.feedback_service.open", side_effect=Exception("fail"))
def test_save_feedback_handles_exception(mock_open, mock_logger):
    save_feedback("vraag", "antwoord", "up")
    mock_logger.exception.assert_called_once()

def test_feedback_invalid_score(client):
    response = client.post("/feedback", json={
        "query": "vraag",
        "answer": "antwoord",
        "score": "invalid"
    })

    assert response.status_code == 422
