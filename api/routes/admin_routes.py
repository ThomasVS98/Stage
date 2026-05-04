from fastapi import APIRouter, Body
from utils.config_loader import load_source_config, save_source_config
from utils.logging import get_logger
from services.admin_service import run_full_ingestion, process_sources
from api.models.source_model import SourceModel

router = APIRouter()
logger = get_logger(__name__)


@router.post("/ingest")
async def trigger_ingest():
    logger.info("Ingestie verzoek ontvangen via API")

    result = run_full_ingestion()
    return {
        "status": "success",
        "docs_indexed": result["docs_indexed"],
        "tickets_indexed": result["tickets_indexed"],
        "message": f"Succes! {result['docs_indexed']} documenten en {result['tickets_indexed']} tickets geïndexeerd.",
    }


@router.get("/sources")
async def get_sources():
    return load_source_config(resolve=False)


@router.post("/sources")
async def update_sources(sources: list[SourceModel] = Body(...)):
    validated_sources = process_sources(sources)
    save_source_config(validated_sources)

    return {"status": "success", "message": "Bronconfiguratie bijgewerkt."}
