from fastapi import APIRouter, HTTPException, Body
from utils.config_loader import load_source_config, save_source_config
from utils.logging import get_logger
from services.admin_service import run_full_ingestion, process_sources
from api.models.source_model import SourceModel

router = APIRouter()
logger = get_logger(__name__)

@router.post("/ingest")
async def trigger_ingest():
    logger.info("Ingestie verzoek ontvangen via API")

    doc_count = run_full_ingestion()
    return {
        "status": "success", 
        "message": f"Succes! {doc_count} documenten geïndexeerd en tickets geïndexeerd."
        }
    
@router.get("/sources")
async def get_sources():
    return load_source_config(resolve=False)

@router.post("/sources")
async def update_sources(sources: list[SourceModel] = Body(...)):
    validated_sources = process_sources(sources)
    save_source_config(validated_sources)

    return {
        "status": "success",
        "message": "Bronconfiguratie bijgewerkt."
    }
