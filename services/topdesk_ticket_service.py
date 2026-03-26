import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOPDESK_BASE_URL = os.getenv("TOPDESK_BASE_URL")
TOPDESK_USER = os.getenv("TOPDESK_USER")
TOPDESK_SECRET = os.getenv("TOPDESK_SECRET")

def build_incident_payload(data:dict)->dict:
    return {
        "briefDescription": data.get("beschrijving")[:80],
        "request": f"""
Context: {data.get("context")}

Doel: {data.get("doel")}
""".strip(),
        "caller": {
            "dynamicName": "Test user"
        }
    }

def create_incident(data:dict)->dict:
    url = f"{TOPDESK_BASE_URL}tas/api/incidents"

    payload = build_incident_payload(data)

    response = requests.post(
        url,
        json=payload,
        auth=(TOPDESK_USER,TOPDESK_SECRET),
        headers={"Content-Type": "application/json"},
        timeout = 30
    )

    if not response.ok:
        raise Exception(f"TOPdesk error {response.status_code}: {response.text}")
    return response.json()
