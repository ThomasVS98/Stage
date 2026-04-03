import os, psutil, gc, uuid
from ingestion.ingest_pipeline import load_all_data, build_index, load_source_config, cleanup_temp_files
from ingestion.ingest_tickets import build_ticket_index
from ingestion.loader_registry import get_schema
from rag.vector_store import reload_index
from utils.logging import get_logger
from fastapi import HTTPException
from api.models.source_model import SourceModel

logger = get_logger(__name__)

def get_folder_size(path):
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total += os.path.getsize(fp)
    return total/ (1024*1024)  # Return size in MB

def run_full_ingestion():
    logger.info("Ingestie gestart...")

    process = psutil.Process(os.getpid())
    logger.info(f"RAM start: {process.memory_info().rss / 1024**2:.2f} MB")

    documents = load_all_data()

    process = psutil.Process(os.getpid())
    logger.info(f"RAM na aanmaken load generator: {process.memory_info().rss / 1024**2:.2f} MB")

    doc_count = build_index(documents)
    del documents
    gc.collect()
    
    if isinstance(doc_count, int) and doc_count > 0:
        logger.info("%s docs geindexeerd", doc_count)
        process = psutil.Process(os.getpid())
        logger.info(f"RAM na indexeren: {process.memory_info().rss / 1024**2:.2f} MB")
    else:
        logger.info("Geen docs gevonden")
        
    logger.info("Start tickets ingestie...") 
    process = psutil.Process(os.getpid())
    logger.info(f"RAM voor tickets: {process.memory_info().rss / 1024**2:.2f} MB")

    sources = load_source_config()
    ticket_limit = 200

    for src in sources:
        if src.get("type") == "topdesk" and src.get("enabled"):
            cfg = src.get("config", {})
            ticket_limit = cfg.get("incident_limit", 200)
            break

    build_ticket_index(limit=ticket_limit)
    process = psutil.Process(os.getpid())
    logger.info(f"RAM na tickets: {process.memory_info().rss / 1024**2:.2f} MB")
    logger.info("Tickets geïndexeerd.")

    cleanup_temp_files()

    reload_index("docs")  # Zorg ervoor dat de query module de nieuwe index gebruikt
    reload_index("tickets")

    size = get_folder_size("./chroma_db")
    logger.info(f"ChromaDB grootte: {size:.2f} MB")

    return doc_count

def process_sources(sources: list[SourceModel]):
    validated_sources = []

    for src in sources:
        validated = validate_source(src)

        if not validated.get("id"):
            validated["id"] = str(uuid.uuid4())
            
        validated_sources.append(validated)
    
    return validated_sources

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

        #Controleer op verplichte velden
        is_required = rules.get("required", False)
        if is_required and (value is None or (isinstance(value, str) and not value.strip())):
            raise HTTPException(
                status_code=400,
                detail=f"Veld '{field}' is verplicht voor type '{source.type}'"
            )
        
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
                value = int(value) if value is not None else 0
            elif field_type == "str":
                value = str(value) if value is not None else ""

        except Exception:
            raise HTTPException(
                status_code=400,
                detail=f"Fout in veld '{field}' (type {field_type})"
            )
        
        validated_config[field] = value

    return {
        "id": source.id,
        "type": source.type,
        "enabled": source.enabled,
        "config": validated_config
    }