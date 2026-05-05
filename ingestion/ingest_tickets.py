import chromadb
from ingestion.loaders.topdesk_loader import (
    fetch_topdesk_incidents,
    incidents_to_documents,
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from rag.embedding import get_embed_model
from utils.logging import get_logger
from utils.exceptions import ExternalServiceError
from llama_index.core import Document
from typing import Any

logger = get_logger(__name__)


def fetch_ticket_documents(limit: int = 300) -> list[Document]:
    """
    Haalt TOPdesk tickets op en zet deze om naar Document objecten.

    Args:
        limit (int): Maximum aantal tickets om op te halen.

    Returns:
        list[Document]: Lijst van Documenten gebaseerd op tickets.

    Raises:
        ExternalServiceError: Bij fouten tijdens ophalen van tickets.
    """
    logger.info("Topdesk tickets ophalen...")

    try:
        items = fetch_topdesk_incidents(limit=limit)
    except ExternalServiceError:
        logger.exception("Fout bij ophalen van Topdesk tickets")
        raise

    logger.info("%s tickets opgehaald", len(items))

    documents = incidents_to_documents(items)
    logger.info("%s documenten gemaakt", len(documents))

    return documents


def create_ticket_index() -> tuple[VectorStoreIndex, Any]:
    """
    Initialiseert een aparte vector index voor tickets.

    Verwijdert bestaande 'tickets' collectie en maakt een nieuwe aan
    in ChromaDB.

    Returns:
        tuple: (VectorStoreIndex, collection)
    """
    chroma_client = chromadb.PersistentClient(path="./chroma_db")

    try:
        chroma_client.delete_collection("tickets")
        logger.info("Bestaande tickets collectie verwijderd")
    except Exception:
        logger.info("Geen tickets collectie om te verwijderen")

    collection = chroma_client.get_or_create_collection(
        name="tickets", metadata={"hnsw:space": "cosine"}
    )

    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex(
        nodes=[],
        storage_context=storage_context,
        embed_model=get_embed_model(),
        show_progress=True,
    )
    return index, collection


def build_ticket_index(limit: int = 300) -> tuple[VectorStoreIndex, int]:
    """
    Bouwt een vector index op basis van TOPdesk tickets.

    Haalt tickets op, splitst ze in chunks en indexeert ze in batches.

    Args:
        limit (int): Maximum aantal tickets om te verwerken.

    Returns:
        tuple: (VectorStoreIndex, aantal geïndexeerde documenten)
    """
    documents = fetch_ticket_documents(limit)
    logger.info("Indexeren...")
    index, collection = create_ticket_index()

    splitter = SentenceSplitter(chunk_size=2000, chunk_overlap=0)

    BATCH_SIZE = 50
    count = 0

    for item in range(0, len(documents), BATCH_SIZE):
        batch = documents[item : item + BATCH_SIZE]
        nodes = splitter.get_nodes_from_documents(batch)
        index.insert_nodes(nodes)
        count += len(batch)

        logger.info("Tickets voortgang: %s/%s geïndexeerd", count, len(documents))

    logger.info("Klaar. %s documenten geïndexeerd", count)
    logger.info("Klaar. Aantal vectors: %s", collection.count())

    return index, count
