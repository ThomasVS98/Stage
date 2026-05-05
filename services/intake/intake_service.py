from utils.exceptions import AppValidationError, ExternalServiceError
from services.intake.intake_state import INTAKE_QUESTIONS
from services.intake.validation import validate_answer, is_relevant
from clients.topdesk_client import create_incident
from stores.session_store import session_store
from rag.ticket_matcher import find_similar_ticket
from langfuse import observe
import uuid
from utils.logging import get_logger
from typing import Any

logger = get_logger(__name__)


@observe(name="intake_start")
def start(original_question: str) -> dict[str, str]:
    """
    Start een nieuwe intake sessie.

    Initialiseert een nieuwe sessie en retourneert de eerste vraag
    uit de intake flow

    Args:
        original_question (str): De originele vraag van de gebruiker.

    Returns:
        dict[str, str]: Bevat session_id en eerste vraag van de intake.
    """
    session_id = str(uuid.uuid4())
    session_store.create(session_id)

    session_store.update(session_id, "original_question", original_question)
    _, question = INTAKE_QUESTIONS[0]
    return {"session_id": session_id, "question": question}


@observe(name="intake_answer")
def answer(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Verwerkt een antwoord binnen een intake sessie.

    - valideert input
    - bewaart antwoord in sessie
    - bepaalt volgende stap of finale verwerking
    - voert matching uit of maakt een ticket aan

    Args:
        payload (dict[str, Any]): Input met session_id en answer.

    Returns:
        - tijdens intake: {"done": False, "question": str}
        - bij afronding:
            * met match: {"done": True, "data": ..., "similar_ticket": ...}
            * met ticket: {"done": True, "data": ..., "ticket": {...}}
            * bij fout: {"done": True, "error": str}

    Raises:
        AppValidationError: Bij ontbrekende of ongeldige sessie/inputs.
        ExternalServiceError: Bij falen van ticket creatie.
    """
    session_id = payload.get("session_id")
    answer = payload.get("answer")

    if not session_id or not answer:
        raise AppValidationError("Missing session_id or answer")
    session = session_store.get(session_id)

    if not session:
        raise AppValidationError("Invalid session")
    step = session["step"]
    key, _ = INTAKE_QUESTIONS[step]

    answer = validate_answer(key, answer)
    session_store.update(session_id, key, answer)
    session = session_store.get(session_id)  # session data vernieuwen na elke update
    if step + 1 >= len(INTAKE_QUESTIONS):
        data = session["data"]
        original_question = session["data"].get("original_question")

        if not original_question:
            logger.warning("Geen originele vraag gevonden in sessie %s", session_id)
        else:
            if not is_relevant(original_question, data):
                logger.info("Intake niet relevant voor sessie %s", session_id)
                return {
                    "done": True,
                    "error": "De gegeven antwoorden lijken niet overeen te komen met je oorspronkelijke vraag.",
                }

        logger.info("Intake data voor sessie %s: %s", session_id, data)
        try:
            match = find_similar_ticket(data)
        except Exception as e:
            logger.exception("Matching error in sessie %s: %s", session_id, e)
            match = None

        if match and match.get("text"):
            logger.info("Gelijkaardig ticket gevonden voor sessie %s", session_id)
            return {"done": True, "data": data, "similar_ticket": match}

        try:
            ticket = create_incident(data)
        except ExternalServiceError:
            logger.exception("Fout bij aanmaken van ticket in sessie %s", session_id)
            raise

        logger.info(
            "Nieuw ticket aangemaakt voor sessie %s: %s",
            session_id,
            ticket.get("number"),
        )

        return {
            "done": True,
            "data": data,
            "ticket": {"number": ticket.get("number"), "id": ticket.get("id")},
        }
    next_step = step + 1
    session_store.increment_step(session_id)
    _, next_question = INTAKE_QUESTIONS[next_step]

    logger.info("Intake sessie %s naar stap %s", session_id, next_step)

    return {"done": False, "question": next_question}
