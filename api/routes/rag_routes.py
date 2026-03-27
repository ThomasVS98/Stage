from fastapi import APIRouter
from pydantic import BaseModel
from services.orchestrator.orchestrator import answer

router = APIRouter()

class AskRequest(BaseModel):
    question: str

@router.post("/ask")
def ask(payload: AskRequest):
    return answer(payload.question)