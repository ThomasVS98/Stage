import requests
import json
from utils.logging import get_logger
from config.settings import settings
from langfuse import observe
from utils.exceptions import ExternalServiceError

logger = get_logger(__name__)


def build_incident_payload(data: dict) -> dict:
    """
    Bouwt de payload voor het aanmaken van een TOPdesk ticket.

    Args:
        data (dict): Gegevens van de intake (beschrijving, context, doel).

    Returns:
        dict: JSON payload volgens TOPdesk API formaat.
    """
    return {
        "briefDescription": (data.get("beschrijving") or "")[:80],
        "request": f"""
Context: {data.get("context")}

Doel: {data.get("doel")}
""".strip(),
        "caller": {"dynamicName": "Test user"},
    }


def write_mock_ticket(data: dict):
    """
    Schrijft een mock ticket naar een lokaal bestand voor testing.

    Args:
        data (dict): Ticketgegevens.
    """
    with open("mock_tickets.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def create_topdesk_incident(data: dict) -> dict:
    """
    Maakt een nieuw ticket aan in TOPdesk via de API.

    Args:
        data (dict): Gegevens van de intake.

    Returns:
        dict: Response van TOPdesk met o.a. ticketnummer en ID.

    Raises:
        ExternalServiceError: Bij ontbrekende configuratie of mislukte API call.
    """
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
    """
    Maakt een ticket aan, of schrijft een mock ticket indien TOPdesk is uitgeschakeld.

    Wordt gebruikt als wrapper rond de TOPdesk integratie om eenvoudig
    te kunnen schakelen tussen echte en mock tickets.

    Args:
        data (dict): Gegevens van de intake.
        writer (callable, optional): Custom functie om mock tickets op te slaan.

    Returns:
        dict: Ticketinformatie (mock of echte response).
    """
    if not settings.TOPDESK_ENABLED:
        logger.warning("TOPdesk uitgeschakeld: mock ticket wordt opgeslagen")

        if writer is not None:
            writer(data)
        else:
            write_mock_ticket(data)

        return {"number": "MOCK-1234", "id": "mock_id"}

    return create_topdesk_incident(data)
