import chromadb
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from utils.logging import get_logger
from rag.embedding import get_embed_model
from typing import Optional, Dict

logger = get_logger(__name__)

cache: Dict[str, Optional[VectorStoreIndex]] = {}


def load_collection_index(collection_name: str) -> Optional[VectorStoreIndex]:
    """
    Laadt een vector index uit een bestaande ChromaDB collectie.

    Args:
        collection_name (str): Naam van de collectie.

    Returns:
        Optional[VectorStoreIndex]: Geladen index of None indien collectie niet bestaat.
    """
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    try:
        chroma_collection = chroma_client.get_collection(collection_name)
    except Exception:
        logger.warning(
            "Geen collectie gevonden: %s. Voer eerst ingest uit", collection_name
        )
        return None

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    index = VectorStoreIndex.from_vector_store(
        vector_store, embed_model=get_embed_model()
    )

    logger.info(
        "Collectie '%s' geladen met %s vectors",
        collection_name,
        chroma_collection.count(),
    )
    return index


def get_index(collection_name: str) -> Optional[VectorStoreIndex]:
    """
    Haalt een index op uit de cache of laadt deze indien nodig.

    Args:
        collection_name (str): Naam van de collectie.

    Returns:
        Optional[VectorStoreIndex]: De index uit cache or nieuw geladen.
    """
    if collection_name not in cache or cache[collection_name] is None:
        cache[collection_name] = load_collection_index(collection_name)
    return cache[collection_name]


def reload_index(collection_name: str) -> None:
    """
    Forceert het herladen van een index in de cache.

    Args:
        collection_name (str): Naam van de collectie.
    """
    logger.info("Index wordt herladen voor collectie: %s", collection_name)
    cache[collection_name] = load_collection_index(collection_name)
    logger.info("Index succesvol herladen voor collectie: %s", collection_name)
