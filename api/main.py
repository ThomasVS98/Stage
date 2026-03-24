from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from query import reload_index
from services.rag_service import answer
from ingestion.ingest_pipeline import build_index, load_all_data, cleanup_temp_files
from api.routes.intake_routes import router as intake_router

app = FastAPI()
app.include_router(intake_router)


class Question(BaseModel):
    question: str

@app.get("/")
def root():
    return {"message": "RAG API running"}

@app.post("/ask")
def ask(q:Question):
    result = answer(q.question)
    return result

# @app.post("/intake/start")
# def start_intake():
#     session_id = str(uuid.uuid4())
#     intake_sessions[session_id] = {
#         "step": 0,
#         "data": {}
#     }
#     key, question = INTAKE_QUESTIONS[0]
#     return{
#         "session_id": session_id,
#         "question": question
#     }

# @app.post("/intake/answer")
# def answer_intake(payload:dict):
#     session_id = payload.get("session_id")
#     answer = payload.get("answer")

#     if not session_id or not answer:
#         raise HTTPException(status_code=400, detail="Missing session_id or answer")
#     session = intake_sessions.get(session_id)

#     if not session:
#         raise HTTPException(status_code=404, detail="Invalid session")
#     step = session["step"]
#     key,_ = INTAKE_QUESTIONS[step]

#     answer = validate_answer(key, answer)
#     session["data"][key] = answer
#     session["step"] += 1

#     if session["step"] >= len(INTAKE_QUESTIONS):
#         try:
#             ticket = create_incident(session["data"])

#             return {
#                 "done": True,
#                 "data": session["data"],
#                 "ticket":{
#                     "number": ticket.get("number"),
#                     "id": ticket.get("id")
#                 }
#             }
#         except Exception as e:
#             return {
#                 "done": True,
#                 "data": session["data"],
#                 "error": str(e)
#             }
        
#     next_key, next_question = INTAKE_QUESTIONS[session["step"]]

#     return {
#         "done": False,
#         "question": next_question
#     }

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
