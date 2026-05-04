import os
import psutil
import gc
import uuid
from ingestion.ingest_pipeline import (
    load_all_data,
    build_index,
    load_source_config,
    cleanup_temp_files,
)
from ingestion.ingest_tickets import build_ticket_index
from ingestion.loader_registry import get_schema
from rag.vector_store import reload_index
from utils.logging import get_logger
from utils.exceptions import IngestionError, SourceConfigError, ExternalServiceError
from api.models.source_model import SourceModel

logger = get_logger(__name__)


def get_folder_size(path):
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total += os.path.getsize(fp)
    return total / (1024 * 1024)  # Return size in MB


def run_full_ingestion():
    logger.info("Ingestie gestart...")

    try:
        process = psutil.Process(os.getpid())
        logger.info(f"RAM start: {process.memory_info().rss / 1024**2:.2f} MB")

        documents = load_all_data()

        process = psutil.Process(os.getpid())
        logger.info(
            f"RAM na aanmaken load generator: {process.memory_info().rss / 1024**2:.2f} MB"
        )

        doc_count = build_index(documents)
        del documents
        gc.collect()

        if isinstance(doc_count, int) and doc_count > 0:
            logger.info("%s docs geindexeerd", doc_count)
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

        _, ticket_count = build_ticket_index(limit=ticket_limit)
        process = psutil.Process(os.getpid())
        logger.info(f"RAM na tickets: {process.memory_info().rss / 1024**2:.2f} MB")
        logger.info("Tickets geïndexeerd: %s", ticket_count)

        cleanup_temp_files()

        reload_index("docs")
        reload_index("tickets")

        size = get_folder_size("./chroma_db")
        logger.info(f"ChromaDB grootte: {size:.2f} MB")

        return {"docs_indexed": doc_count, "tickets_indexed": ticket_count}

    except IngestionError:
        raise

    except ExternalServiceError as e:
        logger.exception("Externe service fout tijdens ingestie")
        raise IngestionError(str(e)) from e

    except Exception as e:
        logger.exception("Onverwachte fout tijdens ingestie")
        raise IngestionError(str(e)) from e


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
        raise SourceConfigError(f"Onbekend bron type: {source.type}")
    validated_config = {}

    for key in source.config.keys():
        if key not in schema:
            raise SourceConfigError(
                f"Onbekend veld '{key}' in config voor type '{source.type}'"
            )

    for field, rules in schema.items():
        value = source.config.get(field)

        # Controleer op verplichte velden
        is_required = rules.get("required", False)
        if is_required and (
            value is None or (isinstance(value, str) and not value.strip())
        ):
            raise SourceConfigError(
                f"Veld '{field}' is verplicht voor type '{source.type}'"
            )

        if value is None:
            value = rules.get("default")

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
                        raise SourceConfigError(f"Fout in veld '{field}' (type bool)")
                else:
                    value = bool(value)

            elif field_type == "int":
                value = int(value) if value is not None else 0
            elif field_type in ["str", "string"]:
                value = str(value) if value is not None else ""

        except SourceConfigError:
            raise
        except (ValueError, TypeError):
            raise SourceConfigError(f"Fout in veld '{field}' (type {field_type})")

        validated_config[field] = value

    return {
        "id": source.id,
        "type": source.type,
        "enabled": source.enabled,
        "config": validated_config,
    }
