from fastapi import APIRouter
from pydantic import BaseModel
from services.qa_service import answer

router = APIRouter()

class Question(BaseModel):
    question: str

@router.post("/ask")
def ask(q:Question):
    result = answer(q.question)
    return result