import chromadb
from ingestion.loaders.topdesk_fetcher import fetch_topdesk_incidents, incidents_to_documents
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from utils.logging import get_logger

logger = get_logger(__name__)

def build_ticket_index(limit=200):
    logger.info("Topdesk tickets ophalen...")

    items = fetch_topdesk_incidents(limit=limit)
    logger.info("%s tickets opgehaald", len(items))

    documents = incidents_to_documents(items)
    logger.info("%s documenten gemaakt", len(documents))

    embed_model = HuggingFaceEmbedding(
        model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        normalize=True
    )

    chroma_client = chromadb.PersistentClient(path="./chroma_db")

    try:
        chroma_client.delete_collection("tickets")
        logger.info("Bestaande tickets collectie verwijderd")
    except Exception as e:
        logger.info("Geen bestaande tickets collectie om te verwijderen: %s", e)

    collection = chroma_client.get_or_create_collection(
        name = "tickets",
        metadata={"hnsw:space": "cosine"}
    )

    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    logger.info("Indexeren...")

    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=embed_model,
        transformations=[SentenceSplitter(chunk_size=2000, chunk_overlap=0)],
        show_progress=True
    )

    logger.info("Klaar. Aantal vectors: %s", collection.count())
    return index

if __name__ == "__main__":
    build_ticket_index(limit=200)