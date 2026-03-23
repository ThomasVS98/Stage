from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from query import ask_question, reload_index
from ingest import build_index, load_all_data, cleanup_temp_files
from topdesk_ticket import create_incident
import uuid
import re

INTAKE_QUESTIONS = [
    ("beschrijving", "Beschrijf heel beknopt het probleem:"),
    ("context", "Geef context aan je probleem/aanvraag:"),
    ("doel", "Wat werkt er niet of wat wil je bereiken?:")
]

intake_sessions = {} 

def validate_answer(key: str, answer: str)->str:
    answer = answer.strip()

    answer = re.sub(r"<.*?>","",answer)

    if not answer:
        raise ValueError("Antwoord mag niet leeg zijn.")
    if key == "beschrijving":
        if len(answer) < 5:
            raise HTTPException(status_code=400, detail="Beschrijving is te kort.")
        if len(answer) > 80:
            raise HTTPException(
                status_code=400,
                detail="Beschrijving mag maxiumum 80 karakters bevatten."
            )

    elif key == "context":
        if len(answer) < 5:
            raise HTTPException(status_code=400, detail="Context is te kort.")
    elif key == "doel":
        if len(answer) < 5:
            raise HTTPException(status_code=400, detail="Doel is te kort.")
        
    return answer



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

@app.post("/intake/start")
def start_intake():
    session_id = str(uuid.uuid4())
    intake_sessions[session_id] = {
        "step": 0,
        "data": {}
    }
    key, question = INTAKE_QUESTIONS[0]
    return{
        "session_id": session_id,
        "question": question
    }

@app.post("/intake/answer")
def answer_intake(payload:dict):
    session_id = payload.get("session_id")
    answer = payload.get("answer")

    if not session_id or not answer:
        raise HTTPException(status_code=400, detail="Missing session_id or answer")
    session = intake_sessions.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Invalid session")
    step = session["step"]
    key,_ = INTAKE_QUESTIONS[step]

    answer = validate_answer(key, answer)
    session["data"][key] = answer
    session["step"] += 1

    if session["step"] >= len(INTAKE_QUESTIONS):
        try:
            ticket = create_incident(session["data"])

            return {
                "done": True,
                "data": session["data"],
                "ticket":{
                    "number": ticket.get("number"),
                    "id": ticket.get("id")
                }
            }
        except Exception as e:
            return {
                "done": True,
                "data": session["data"],
                "error": str(e)
            }
        
    next_key, next_question = INTAKE_QUESTIONS[session["step"]]

    return {
        "done": False,
        "question": next_question
    }

@app.post("/ingest")
async def trigger_ingest():
    try:
        print("[API] Ingestie gestart...")
        documents = load_all_data()
        if not documents:
            return {"status": "warning", "message": "Geen documenten gevonden om te indexeren"}

        build_index(documents)
        cleanup_temp_files()
        reload_index()  # Zorg ervoor dat de query module de nieuwe index gebruikt
        return {
            "status": "success", 
            "message": f"Succes! {len(documents)} documenten geïndexeerd vanuit SharePoint."
            }
    except Exception as e:
        print(f"[API] Fout tijdens ingestie: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
