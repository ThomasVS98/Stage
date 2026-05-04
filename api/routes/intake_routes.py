from fastapi import APIRouter
from pydantic import BaseModel
from services.intake.intake_service import start as start_service
from services.intake.intake_service import answer as answer_service


router = APIRouter()


class IntakeStartRequest(BaseModel):
    """
    Model voor het starten van een intakeprocedure.

    Attributes:
        original_question (str): De originele vraag van de gebruiker.
    """

    original_question: str


class IntakeAnswerRequest(BaseModel):
    """
    Model voor een antwoord binnen de intakeprocedure.

    Attributes:
        session_id (str): Unieke identifier voor de intake sessie.
        answer (str): Antwoord van de gebruiker op de gestelde intake vraag.
    """

    session_id: str
    answer: str


@router.post("/intake/start")
def start_intake(payload: IntakeStartRequest) -> dict:
    """
    Start een nieuwe intakeprocedure op basis van een gebruikersvraag.

    Args:
        payload (IntakeStartRequest): Bevat de originele vraag van de gebruiker.

    Returns:
        dict: Resultaat van de intake start (bv. eerste vraag en sessie ID).
    """
    return start_service(payload.original_question)


@router.post("/intake/answer")
def answer_intake(payload: IntakeAnswerRequest) -> dict:
    """
    Verwerkt een antwoord binnen een lopende intakeprocedure.

    Args:
        payload (IntakeAnswerRequest): Bevat het antwoord en de sessie ID van de gebruiker.

    Returns:
        dict: Resultaat van de intake stap (volgende vraag of afronding).
    """
    return answer_service(payload.model_dump())
