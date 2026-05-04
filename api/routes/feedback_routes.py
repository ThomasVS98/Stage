from fastapi import APIRouter
from pydantic import BaseModel
from services.feedback_service import save_feedback
from typing import Literal

router = APIRouter()


class FeedbackRequest(BaseModel):
    """
    Model voor gebruikersfeedback op gegenereerde antwoorden.

    Attributes:
        query (str): De originele gebruikersvraag.
        answer (str): Het gegenereerde antwoord van de LLM.
        score (Literal["up", "down"]): Positieve ("up") of negatieve ("down") feedback.
    """

    query: str
    answer: str
    score: Literal["up", "down"]


@router.post("/feedback")
def submit_feedback(request: FeedbackRequest) -> dict:
    """
    Slaat gebruikersfeedback op voor een gegeven vraag en antwoord.

    Args:
        request (FeedbackRequest): Feedbackgegevens van de gebruiker.

    Returns:
        dict: Bevestiging dat de feedback succesvol werd opgeslagen.
    """
    save_feedback(query=request.query, answer=request.answer, score=request.score)

    return {"status": "ok"}
