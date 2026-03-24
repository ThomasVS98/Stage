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
