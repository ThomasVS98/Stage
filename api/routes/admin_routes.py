from fastapi import APIRouter, HTTPException, Body
from ingestion.ingest_pipeline import build_index, load_all_data, cleanup_temp_files
from ingestion.ingest_tickets import build_ticket_index
from rag.index_store import reload_index
from utils.config_loader import load_source_config, save_source_config
from utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

@router.post("/ingest")
async def trigger_ingest():
    try:
        logger.info("Ingestie gestart...")
        documents = load_all_data()
        if documents:
            build_index(documents)
            logger.info("%s docs geindexeerd", len(documents))
        else:
            logger.info("Geen docs gevonden")
            
        logger.info("Start tickets ingestie...")    
        build_ticket_index(limit=200)
        logger.info("Tickets geïndexeerd.")

        cleanup_temp_files()

        reload_index("docs")  # Zorg ervoor dat de query module de nieuwe index gebruikt
        reload_index("tickets")
        return {
            "status": "success", 
            "message": f"Succes! {len(documents)} documenten geïndexeerd en tickets geïndexeerd."
            }
    except Exception as e:
        logger.exception("Fout tijdens ingestie: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/sources")
async def get_sources():
    return load_source_config()

@router.post("/sources")
async def update_sources(sources: list = Body(...)):
    save_source_config(sources)
    return {"status": "ok", "message": "Bronconfiguratie bijgewerkt."}