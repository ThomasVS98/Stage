from fastapi import APIRouter
from pydantic import BaseModel
from services.qa_service import answer

router = APIRouter()


class AskRequest(BaseModel):
    """
    Model voor een vraag aan de RAG agent.

    Attributes:
        question (str): De vraag van de gebruiker.
    """

    question: str


@router.post("/ask")
def ask(payload: AskRequest) -> dict:
    """
    Verwerkt een gebruikersvraag via de RAG-pipeline.

    Args:
        payload (AskRequest): Bevat de vraag van de gebruiker.

    Returns:
        dict: Het gegenereerde antwoord met bijhorende bronnen en eventuele metadata.
    """
    return answer(payload.question)
