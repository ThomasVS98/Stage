import time
import requests
from utils.logging import get_logger
from config.settings import settings
from utils.exceptions import ExternalServiceError

logger = get_logger(__name__)

_token_cache = {
    "access_token": None,
    "expires_at": 0
}

def get_graph_headers():
    global _token_cache

    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"] - 60:
        return {"Authorization": f"Bearer {_token_cache['access_token']}"}
    
    if not all([settings.SHAREPOINT_CLIENT_ID, settings.SHAREPOINT_CLIENT_SECRET, settings.SHAREPOINT_TENANT_ID]):
        logger.error("Microsoft Graph configuratie onvolledig, controleer env vars")
        raise ExternalServiceError("Microsoft Graph configuratie onvolledig")

    token_url = f"https://login.microsoftonline.com/{settings.SHAREPOINT_TENANT_ID}/oauth2/v2.0/token"

    token_data = {
        "client_id": settings.SHAREPOINT_CLIENT_ID,
        "client_secret": settings.SHAREPOINT_CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    try:

        res = requests.post(token_url, data=token_data, timeout=30)
        res.raise_for_status()
    except requests.RequestException as e:
        raise ExternalServiceError(f"Graph token request mislukt: {e}")

    data = res.json()

    access_token = data.get("access_token")
    expires_in = data.get("expires_in", 3600)

    if not access_token:
        raise ExternalServiceError("Geen access token ontvangen van Microsoft Graph API")
    
    _token_cache = {
        "access_token": access_token,
        "expires_at": time.time() + expires_in
    }

    return {"Authorization": f"Bearer {access_token}"}

def graph_get(url):
    global _token_cache

    headers = get_graph_headers()
    res = requests.get(url, headers=headers, timeout=30)

    if res.status_code == 401:
        logger.info("Token verlopen, aan het vernieuwen...")
        _token_cache = {
            "access_token": None,
            "expires_at": 0
        }

        headers = get_graph_headers()
        res = requests.get(url, headers=headers, timeout=30)

        if not res.ok:
            raise ExternalServiceError(f"Graph API fout na token refresh: {res.status_code} - {res.text[:100]}")

    return res