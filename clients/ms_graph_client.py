import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SHAREPOINT_CLIENT_ID")
CLIENT_SECRET = os.getenv("SHAREPOINT_CLIENT_SECRET")
TENANT_ID = os.getenv("SHAREPOINT_TENANT_ID")

_token_cache = None

def get_graph_headers():
    global _token_cache

    if _token_cache:
        return {"Authorization": f"Bearer {_token_cache}"}

    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    res = requests.post(token_url, data=token_data)
    res.raise_for_status()

    token = res.json().get("access_token")

    if not token:
        raise Exception("Geen access token ontvangen van Microsoft Graph API")
    
    _token_cache = token

    return {"Authorization": f"Bearer {token}"}