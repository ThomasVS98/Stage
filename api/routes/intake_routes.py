from fastapi import APIRouter
from services.intake_service import start as start_service
from services.intake_service import answer as answer_service


router = APIRouter()

@router.post("/intake/start")
def start_intake():
    return start_service()
@router.post("/intake/answer")
def answer_intake(payload:dict):
    return answer_service(payload)

