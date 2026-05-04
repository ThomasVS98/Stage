from fastapi import APIRouter, Body
from utils.config_loader import load_source_config, save_source_config
from utils.logging import get_logger
from services.admin_service import run_full_ingestion, process_sources
from api.models.source_model import SourceModel

router = APIRouter()
logger = get_logger(__name__)


@router.post("/ingest")
async def trigger_ingest() -> dict:
    """
    Start een volledige ingestie van documenten en tickets.

    Deze endpoint triggert het herindexeren van alle geconfigureerde bronnen
    en bestaande tickets (TOPdesk) in de vector database.

    Returns:
        dict: Statusinformatie met het aantal geïndexeerde documenten en tickets.
    """
    logger.info("Ingestie verzoek ontvangen via API")

    result = run_full_ingestion()
    return {
        "status": "success",
        "docs_indexed": result["docs_indexed"],
        "tickets_indexed": result["tickets_indexed"],
        "message": f"Succes! {result['docs_indexed']} documenten en {result['tickets_indexed']} tickets geïndexeerd.",
    }


@router.get("/sources")
async def get_sources() -> list[dict]:
    """
    Haalt de huidige bronconfiguratie op.

    Returns:
        list[dict]: Lijst van geconfigureerde bronnen.
    """
    return load_source_config(resolve=False)


@router.post("/sources")
async def update_sources(sources: list[SourceModel] = Body(...)) -> dict:
    """
    Update de configuratie van kennisbronnen.

    Valideert de inkomende bronconfiguratie en slaat deze op.

    Args:
        sources (list[SourceModel]): Lijst van bronconfiguraties.

    Returns:
        dict: Statusbericht van de update-operatie.

    """
    validated_sources = process_sources(sources)
    save_source_config(validated_sources)

    return {"status": "success", "message": "Bronconfiguratie bijgewerkt."}
