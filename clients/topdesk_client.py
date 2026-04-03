import os
import requests
import json
from utils.logging import get_logger
from config.settings import settings
from utils.exceptions import ExternalServiceError

TOPDESK_BASE_URL = settings.TOPDESK_BASE_URL
TOPDESK_USER = settings.TOPDESK_USER
TOPDESK_SECRET = settings.TOPDESK_SECRET

TOPDESK_ENABLED = settings.TOPDESK_ENABLED

logger =  get_logger(__name__)

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
    # voor testing soms even topdesk kunnen uitzetten voor ticketing
    if not TOPDESK_ENABLED:
        logger.warning("TOPdesk uitgeschakeld: mock ticket wordt opgeslagen")
        with open('mock_tickets.jsonl',"a",encoding="utf-8") as f:
            f.write(json.dumps(data,ensure_ascii=False)+"\n")

        return {
            "number": "MOCK-1234",
            "id": "mock_id"
        }
    
    url = f"{TOPDESK_BASE_URL}/tas/api/incidents"
    payload = build_incident_payload(data)

    response = requests.post(
        url,
        json=payload,
        auth=(TOPDESK_USER,TOPDESK_SECRET),
        headers={"Content-Type": "application/json"},
        timeout = 30
    )

    if not response.ok:
        logger.error("TOPdesk error %s: %s", response.status_code, response.text)
        raise ExternalServiceError(f"TOPdesk error {response.status_code}")
    
    result = response.json()
    logger.info("TOPdesk ticket aangemaakt= %s", result.get("number"))
    return result
