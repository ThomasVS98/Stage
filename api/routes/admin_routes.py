from fastapi import APIRouter, HTTPException, Body
from ingestion.ingest_pipeline import build_index, load_all_data, cleanup_temp_files
from ingestion.ingest_tickets import build_ticket_index
from rag.index_store import reload_index
from utils.config_loader import load_source_config, save_source_config
from utils.logging import get_logger
from pydantic import BaseModel
from typing import Dict, Any
from ingestion.loader_registry import get_schema

router = APIRouter()
logger = get_logger(__name__)

class SourceModel(BaseModel):
    type: str
    enabled: bool = True
    config: Dict[str, Any]

def validate_source(source: SourceModel):
    schema = get_schema(source.type)

    if not schema:
        raise HTTPException(
            status_code=400, 
            detail=f"Onbekend bron type: {source.type}"
        )
    validated_config = {}

    for key in source.config.keys():
        if key not in schema:
            raise HTTPException(
                status_code=400,
                detail=f"Onbekend veld '{key}' voor type '{source.type}'"
            )
    
    for field, rules in schema.items():
        value = source.config.get(field)

        if value is None:
            value = rules.get('default')
        
        field_type = rules.get("type")

        try:
            if field_type == "bool":
                if isinstance(value, bool):
                    pass
                elif isinstance(value, str):
                    if value.lower() in ["true", "1", "yes"]:
                        value = True
                    elif value.lower() in ["false", "0", "no"]:
                        value = False
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Fout in veld '{field}' (type bool)"
                        )
                else:
                    value = bool(value)

            elif field_type == "int":
                value = int(value)
            elif field_type == "str":
                value = str(value) if value is not None else ""

        except Exception:
            raise HTTPException(
                status_code=400,
                detail=f"Fout in veld '{field}' (type {field_type})"
            )
        
        validated_config[field] = value

    return {
        "type": source.type,
        "enabled": source.enabled,
        "config": validated_config
    }

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

        sources = load_source_config()
        ticket_limit = 200  

        for src in sources:
            if src.get("type") == "topdesk" and src.get("enabled"):
                cfg = src.get("config", {})
                ticket_limit = cfg.get("incident_limit", 200)
                break

        build_ticket_index(limit=ticket_limit)
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
async def update_sources(sources: list[SourceModel] = Body(...)):
    validated_sources = []

    for src in sources:
        validated = validate_source(src)
        validated_sources.append(validated)

    save_source_config(validated_sources)

    return {"status": "ok",
            "message": "Bronconfiguratie bijgewerkt."
        }