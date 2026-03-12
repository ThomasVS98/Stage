from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from query import ask_question, reload_index
from ingest import load_documents, build_index


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

@app.post("/ingest")
async def trigger_ingest():
    try:
        documents = load_documents()
        build_index(documents)
        reload_index()  # Zorg ervoor dat de query module de nieuwe index gebruikt
        return {"status": "success", "message": "Ingestie en indexering succesvol uitgevoerd"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
