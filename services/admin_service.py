import os, psutil, gc
from ingestion.ingest_pipeline import load_all_data, build_index, load_source_config, cleanup_temp_files
from ingestion.ingest_tickets import build_ticket_index
from rag.vector_store import reload_index
from utils.logging import get_logger

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
    logger.info(f"RAM na load: {process.memory_info().rss / 1024**2:.2f} MB")

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