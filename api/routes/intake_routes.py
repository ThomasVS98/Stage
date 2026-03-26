from fastapi import APIRouter
from services.intake.intake_service import start as start_service
from services.intake.intake_service import answer as answer_service


router = APIRouter()

@router.post("/intake/start")
def start_intake(payload:dict):
    original_question = payload.get("original_question")
    return start_service(original_question)

@router.post("/intake/answer")
def answer_intake(payload:dict):
    return answer_service(payload)

