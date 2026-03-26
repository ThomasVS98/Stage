from fastapi import HTTPException
from services.intake.intake_state import INTAKE_QUESTIONS
from services.intake.validation import validate_answer
from services.topdesk_ticket_service import create_incident
from services.session_store import session_store
from services.ticket_match_service import find_similar_ticket
from services.intake.validation import is_relevant
import uuid

def start(original_question:str):
    session_id = str(uuid.uuid4())
    session_store.create(session_id)

    session_store.update(session_id, "original_question", original_question)
    _ , question = INTAKE_QUESTIONS[0]
    return{
        "session_id": session_id,
        "question": question
    }

def answer(payload:dict):
    session_id = payload.get("session_id")
    answer = payload.get("answer")

    if not session_id or not answer:
        raise HTTPException(status_code=400, detail="Missing session_id or answer")
    session = session_store.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Invalid session")
    step = session["step"]
    key, _ = INTAKE_QUESTIONS[step]

    answer = validate_answer(key, answer)
    session_store.update(session_id, key, answer)
    session = session_store.get(session_id) # session data vernieuwen na elke update
    if step + 1 >= len(INTAKE_QUESTIONS):
        data = session["data"]
        original_question = session["data"].get("original_question")

        if not original_question:
            print("Geen originele vraag gevonden in sessie")
        else:
            if not is_relevant(original_question, data):
                return {
                    "done": True,
                    "error": "De gegeven antwoorden lijken niet overeen te komen met je oorspronkelijke vraag."
                }

        print("intake data: ", data)
        try:
            match = find_similar_ticket(data)
        except Exception as e:
            print("❌ Matching error:", e)
            match = None
        if match and match.get("text"):
            return {
                "done": True,
                "data": data,
                "similar_ticket": match
            }
        ticket = create_incident(data)
        return {
            "done": True,
            "data": data,
            "ticket": {
                "number": ticket.get("number"),
                "id": ticket.get("id")
            }
        }
    next_step = step + 1
    session_store.increment_step(session_id)
        
    _ , next_question = INTAKE_QUESTIONS[next_step]

    return {
        "done": False,
        "question": next_question
    }