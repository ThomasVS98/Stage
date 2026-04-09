import pytest
from clients.topdesk_client import (
    build_incident_payload, 
    create_incident,
    create_topdesk_incident
)
from config.settings import settings
from unittest.mock import patch, MagicMock
from utils.exceptions import ExternalServiceError

def test_build_incident_payload_basic():
    data = {
        "beschrijving": "Laptop stuk",
        "context": "Op kantoor",
        "doel": "Herstellen"
    }

    payload = build_incident_payload(data)

    assert payload["briefDescription"] == "Laptop stuk"
    assert "Context: Op kantoor" in payload["request"]
    assert "Doel: Herstellen" in payload["request"]
    assert payload["caller"]["dynamicName"] == "Test user"

@patch("clients.topdesk_client.requests.post")
def test_create_topdesk_incident_success(mock_post, monkeypatch):
    monkeypatch.setattr(settings, "TOPDESK_BASE_URL", "http://fake-topdesk.com")
    monkeypatch.setattr(settings, "TOPDESK_USER", "user")
    monkeypatch.setattr(settings, "TOPDESK_SECRET", "secret")

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "number": "INC-999",
        "id": "xyz"
    }

    mock_post.return_value = mock_response

    data = {
        "beschrijving": "Test",
        "context": "Ctx",
        "doel": "Goal"
    }

    result = create_topdesk_incident(data)
    mock_post.assert_called_once()

    assert result["number"] == "INC-999"
    assert result["id"] == "xyz" 

@patch("clients.topdesk_client.requests.post")
def test_create_topdesk_incident_api_error(mock_post, monkeypatch):
    monkeypatch.setattr(settings, "TOPDESK_BASE_URL", "http://fake-topdesk.com")
    monkeypatch.setattr(settings, "TOPDESK_USER", "user")
    monkeypatch.setattr(settings, "TOPDESK_SECRET", "secret")

    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 500
    mock_response.text = "Server Error"

    mock_post.return_value = mock_response

    with pytest.raises(ExternalServiceError, match="TOPdesk error"):
        create_topdesk_incident({})

def test_create_topdesk_incident_missing_config(monkeypatch):
    monkeypatch.setattr(settings, "TOPDESK_BASE_URL", None)
    monkeypatch.setattr(settings, "TOPDESK_USER", None)
    monkeypatch.setattr(settings, "TOPDESK_SECRET", None)

    data = {
        "beschrijving": "Test",
        "context": "Ctx",
        "doel": "Goal"
    }

    with pytest.raises(ExternalServiceError):
        create_topdesk_incident(data)

def test_create_incident_mock_mode(monkeypatch):
    monkeypatch.setattr(settings, "TOPDESK_ENABLED", False)
    mock_writer = MagicMock()

    data = {
        "beschrijving": "Laptop stuk",
        "context": "Op kantoor",
        "doel": "Herstellen"
    }

    result = create_incident(data, writer=mock_writer)

    assert result["number"] == "MOCK-1234"
    assert result["id"] == "mock_id"
    mock_writer.assert_called_once_with(data)

def test_create_incident_mock_mode_default_writer(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "TOPDESK_ENABLED", False)
    monkeypatch.chdir(tmp_path)

    data = {
        "beschrijving": "Laptop stuk",
        "context": "Op kantoor",
        "doel": "Herstellen"
    }

    create_incident(data)

    file_path = tmp_path / "mock_tickets.jsonl"
    assert file_path.exists()

    content = file_path.read_text()
    assert "Laptop stuk" in content

@patch("clients.topdesk_client.create_topdesk_incident")
def test_create_incident_success(mock_client, monkeypatch):
    monkeypatch.setattr(settings, "TOPDESK_ENABLED", True)

    mock_client.return_value = {
        "number": "INC-123",
        "id": "abc"
    }

    data = {
        "beschrijving": "Test",
        "context": "Ctx",
        "doel": "Goal"
    }

    result = create_incident(data)

    assert result["number"] == "INC-123"
    mock_client.assert_called_once_with(data)

@patch("clients.topdesk_client.create_topdesk_incident")
def test_create_incident_api_error(mock_client, monkeypatch):
    monkeypatch.setattr(settings, "TOPDESK_ENABLED", True)
    
    mock_client.side_effect = ExternalServiceError("Server Error")

    data = {
        "beschrijving": "Laptop stuk",
        "context": "Op kantoor",
        "doel": "Herstellen"
    }

    with pytest.raises(ExternalServiceError, match="Server Error"):
        create_incident(data)

def test_build_incident_payload_missing_desc():
    data = {
        "context": "Op kantoor",
        "doel": "Herstellen"
    }
    payload = build_incident_payload(data)
    assert payload["briefDescription"] == ""