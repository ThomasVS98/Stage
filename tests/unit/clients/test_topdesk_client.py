import pytest
from clients.topdesk_client import build_incident_payload, create_incident
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

def test_create_incident_mock_mode(monkeypatch):
    monkeypatch.setattr(settings, "TOPDESK_ENABLED", False)

    data = {
        "beschrijving": "Laptop stuk",
        "context": "Op kantoor",
        "doel": "Herstellen"
    }

    result = create_incident(data)

    assert result["number"] == "MOCK-1234"
    assert result["id"] == "mock_id"

@patch("clients.topdesk_client.requests.post")
def test_create_incident_success(mock_post, monkeypatch):
    monkeypatch.setattr(settings, "TOPDESK_ENABLED", True)

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "number": "INC-123",
        "id": "abc"
    }

    mock_post.return_value = mock_response

    data = {
        "beschrijving": "Laptop stuk",
        "context": "Op kantoor",
        "doel": "Herstellen"
    }

    result = create_incident(data)

    assert result["number"] == "INC-123"
    assert result["id"] == "abc"

@patch("clients.topdesk_client.requests.post")
def test_create_incident_api_error(mock_post, monkeypatch):
    monkeypatch.setattr(settings, "TOPDESK_ENABLED", True)
    
    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.status_code = 500
    mock_response.text = "Server Error"

    mock_post.return_value = mock_response

    data = {
        "beschrijving": "Laptop stuk",
        "context": "Op kantoor",
        "doel": "Herstellen"
    }

    with pytest.raises(ExternalServiceError):
        create_incident(data)

def test_create_incident_missing_config(monkeypatch):
    monkeypatch.setattr(settings, "TOPDESK_ENABLED", True)
    monkeypatch.setattr(settings, "TOPDESK_BASE_URL", None)
    monkeypatch.setattr(settings, "TOPDESK_USER", None)
    monkeypatch.setattr(settings, "TOPDESK_SECRET", None)

    data = {
        "beschrijving": "Laptop stuk",
        "context": "Op kantoor",
        "doel": "Herstellen"
    }

    with pytest.raises(ExternalServiceError, match="TOPdesk configuratie onvolledig"):
        create_incident(data)