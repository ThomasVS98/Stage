from fastapi import APIRouter
from pydantic import BaseModel
from services.intake.intake_service import start as start_service
from services.intake.intake_service import answer as answer_service


router = APIRouter()

class IntakeStartRequest(BaseModel):
    original_question: str

class IntakeAnswerRequest(BaseModel):
    session_id: str
    answer: str

@router.post("/intake/start")
def start_intake(payload: IntakeStartRequest):
    return start_service(payload.original_question)

@router.post("/intake/answer")
def answer_intake(payload: IntakeAnswerRequest):
    return answer_service(payload.model_dump())

