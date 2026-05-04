from fastapi import APIRouter
from pydantic import BaseModel
from services.feedback_service import save_feedback

router = APIRouter()

class FeedbackRequest(BaseModel):
    query: str
    answer: str
    score: str

@router.post("/feedback")
def submit_feedback(request: FeedbackRequest):
    save_feedback(
        query=request.query,
        answer=request.answer,
        score=request.score
    )

    return {"status": "ok"}