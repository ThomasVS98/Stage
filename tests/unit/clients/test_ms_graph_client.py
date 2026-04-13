import pytest, requests, time
from unittest.mock import patch, MagicMock
from clients.ms_graph_client import get_graph_headers, graph_get
from clients import ms_graph_client
from utils.exceptions import ExternalServiceError
from config.settings import settings

@pytest.fixture(autouse=True)
def reset_token_cache(monkeypatch):
    import clients.ms_graph_client as m

    monkeypatch.setattr(m, "_token_cache", {
        "access_token": None,
        "expires_at": 0
    })

    monkeypatch.setattr(settings, "SHAREPOINT_CLIENT_ID", "id")
    monkeypatch.setattr(settings, "SHAREPOINT_CLIENT_SECRET", "secret")
    monkeypatch.setattr(settings, "SHAREPOINT_TENANT_ID", "tenant")

@patch("clients.ms_graph_client.requests.post")
def test_get_graph_headers_success(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "abc123",
        "expires_in": 3600
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    headers = get_graph_headers()

    assert headers == {"Authorization": "Bearer abc123"}

@patch("clients.ms_graph_client.requests.post")
def test_get_graph_headers_uses_cache(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "access_token": "cached_token",
        "expires_in": 3600
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    headers1 = get_graph_headers()
    headers2 = get_graph_headers()

    assert headers1["Authorization"] == "Bearer cached_token"
    assert headers2["Authorization"] == "Bearer cached_token"
    
    mock_post.assert_called_once()

def test_get_graph_headers_missing_config(monkeypatch):
    monkeypatch.setattr(settings, "SHAREPOINT_CLIENT_ID", None)
    monkeypatch.setattr(settings, "SHAREPOINT_CLIENT_SECRET", None)
    monkeypatch.setattr(settings, "SHAREPOINT_TENANT_ID", None)

    with pytest.raises(ExternalServiceError, match="Microsoft Graph configuratie onvolledig"):
        get_graph_headers()

@patch("clients.ms_graph_client.requests.post")
def test_get_graph_headers_network_error(mock_post):
    mock_post.side_effect = requests.RequestException("Connection timeout")
    with pytest.raises(ExternalServiceError, match="Graph token request mislukt"):
        get_graph_headers()

@patch("clients.ms_graph_client.requests.post")
def test_get_graph_headers_no_token_in_json(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {"expires_in": 3600}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    with pytest.raises(ExternalServiceError, match="Geen access token ontvangen"):
        get_graph_headers()

def test_get_graph_headers_refreshes_near_expiry():
    ms_graph_client._token_cache["access_token"] = "old_token"
    ms_graph_client._token_cache["expires_at"] = time.time() + 30
    
    with patch("clients.ms_graph_client.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "new_token", "expires_in": 3600}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        headers = get_graph_headers()
        assert headers["Authorization"] == "Bearer new_token"
        mock_post.assert_called_once()

@patch("clients.ms_graph_client.requests.get")
@patch("clients.ms_graph_client.requests.post")
def test_graph_get_refresh_on_401(mock_post, mock_get):
    mock_token_response = MagicMock()
    mock_token_response.json.return_value = {
        "access_token": "new_token",
        "expires_in": 3600
    }

    mock_token_response.raise_for_status.return_value = None
    mock_post.return_value = mock_token_response

    first_response = MagicMock()
    first_response.status_code = 401

    second_response = MagicMock()
    second_response.status_code = 200
    second_response.ok = True

    mock_get.side_effect = [first_response, second_response]

    res = graph_get("https://graph.microsoft.com/test")

    assert res.status_code == 200
    assert mock_get.call_count == 2
    assert mock_post.call_count == 2

@patch("clients.ms_graph_client.requests.get")
@patch("clients.ms_graph_client.requests.post")
def test_graph_get_refresh_failure(mock_post, mock_get):
    mock_token_response = MagicMock()
    mock_token_response.json.return_value = {
        "access_token": "new_token",
        "expires_in": 3600
    }

    mock_token_response.raise_for_status.return_value = None
    mock_post.return_value = mock_token_response

    first_response = MagicMock()
    first_response.status_code = 401

    second_response = MagicMock()
    second_response.status_code = 500
    second_response.ok = False
    second_response.text = "Internal Server error"

    mock_get.side_effect = [first_response, second_response]

    with pytest.raises(ExternalServiceError, match="Graph API fout na token refresh"):
        graph_get("https://graph.microsoft.com/test")
