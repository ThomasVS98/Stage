from fastapi import APIRouter
from pydantic import BaseModel
from services.feedback_service import save_feedback
from typing import Literal

router = APIRouter()


class FeedbackRequest(BaseModel):
    query: str
    answer: str
    score: Literal["up", "down"]


@router.post("/feedback")
def submit_feedback(request: FeedbackRequest):
    save_feedback(query=request.query, answer=request.answer, score=request.score)

    return {"status": "ok"}
