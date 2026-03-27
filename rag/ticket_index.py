from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
from utils.logging import get_logger

logger = get_logger(__name__)

def load_ticket_index():

    embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        normalize=True
        )
    
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    try:
        chroma_collection = chroma_client.get_collection("tickets")
    except Exception:
        logger.warning("Geen ticket collectie gevonden. Voer eerst ingest_tickets uit")
        return None
    
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)


    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=embed_model
    )

    logger.info("Aantal vectors in ticket collectie: %s", chroma_collection.count())
    return index

ticket_index = None

def get_ticket_index():
    global ticket_index
    if ticket_index is None:
        ticket_index = load_ticket_index()
    return ticket_index

def reload_ticket_index():
    """Forceert het herladen van de index na een ingestie."""
    global ticket_index
    logger.info("Index wordt herladen...")
    ticket_index = load_ticket_index()
    logger.info("Index succesvol herladen.")