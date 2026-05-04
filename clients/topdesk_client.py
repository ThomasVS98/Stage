import requests
import json
from utils.logging import get_logger
from config.settings import settings
from langfuse import observe
from utils.exceptions import ExternalServiceError

logger = get_logger(__name__)


def build_incident_payload(data: dict) -> dict:
    return {
        "briefDescription": (data.get("beschrijving") or "")[:80],
        "request": f"""
Context: {data.get("context")}

Doel: {data.get("doel")}
""".strip(),
        "caller": {"dynamicName": "Test user"},
    }


def write_mock_ticket(data: dict):
    with open("mock_tickets.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def create_topdesk_incident(data: dict) -> dict:
    if not all(
        [settings.TOPDESK_BASE_URL, settings.TOPDESK_USER, settings.TOPDESK_SECRET]
    ):
        logger.error("TOPdesk configuratie onvolledig, controleer env vars")
        raise ExternalServiceError("TOPdesk configuratie onvolledig")

    url = f"{settings.TOPDESK_BASE_URL}/tas/api/incidents"
    payload = build_incident_payload(data)

    response = requests.post(
        url,
        json=payload,
        auth=(settings.TOPDESK_USER, settings.TOPDESK_SECRET),
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    if not response.ok:
        logger.error("TOPdesk error %s: %s", response.status_code, response.text)
        raise ExternalServiceError(f"TOPdesk error {response.status_code}")

    result = response.json()
    logger.info("TOPdesk ticket aangemaakt= %s", result.get("number"))
    return result


@observe(name="create_incident")
def create_incident(data: dict, writer=None) -> dict:
    # voor testing soms even topdesk kunnen uitzetten voor ticketing
    if not settings.TOPDESK_ENABLED:
        logger.warning("TOPdesk uitgeschakeld: mock ticket wordt opgeslagen")

        if writer is not None:
            writer(data)
        else:
            write_mock_ticket(data)

        return {"number": "MOCK-1234", "id": "mock_id"}

    return create_topdesk_incident(data)
