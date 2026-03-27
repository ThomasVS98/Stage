from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
from utils.logging import get_logger

logger = get_logger(__name__)

def load_index():

    embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        normalize=True
        )
    
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    try:
        chroma_collection = chroma_client.get_collection("docs")
    except Exception:
        logger.warning("Geen collectie gevonden. Voer eerst ingest uit")
        return None
    
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)


    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=embed_model
    )

    return index

index = None

def get_index():
    global index
    if index is None:
        index = load_index()
    return index

def reload_index():
    """Forceert het herladen van de index na een ingestie."""
    global index
    logger.info("Index wordt herladen...")
    index = load_index()
    logger.info("Index succesvol herladen.")