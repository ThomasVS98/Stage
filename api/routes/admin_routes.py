from fastapi import APIRouter, HTTPException
from ingestion.ingest_pipeline import build_index, load_all_data, cleanup_temp_files
from ingestion.ingest_tickets import build_ticket_index
from rag.ticket_index import reload_ticket_index
from rag.query import reload_index


router = APIRouter()

@router.post("/ingest")
async def trigger_ingest():
    try:
        print("[API] Ingestie gestart...")
        documents = load_all_data()
        if documents:
            build_index(documents)
            print(f"[API] {len(documents)} docs geïndexeerd")
        else:
            print("[API] Geen docs gevonden")
            
        print("[API] Start tickets ingestie...")    
        build_ticket_index(limit=200)
        print("[API] Tickets geïndexeerd.")

        cleanup_temp_files()

        reload_index()  # Zorg ervoor dat de query module de nieuwe index gebruikt
        reload_ticket_index()
        return {
            "status": "success", 
            "message": f"Succes! {len(documents)} documenten geïndexeerd en tickets geïndexeerd."
            }
    except Exception as e:
        print(f"[API] Fout tijdens ingestie: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))