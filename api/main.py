from fastapi import FastAPI
from pydantic import BaseModel
from query import ask_question


app = FastAPI()


class Question(BaseModel):
    question: str

@app.get("/")
def root():
    return {"message": "RAG API running"}

@app.post("/ask")
def ask(q:Question):
    result = ask_question(q.question)
    return result
