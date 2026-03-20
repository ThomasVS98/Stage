from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from query import ask_question, reload_index
from ingest import build_index, load_all_data, cleanup_temp_files


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
