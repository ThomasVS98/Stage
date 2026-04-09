import chromadb
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from utils.logging import get_logger
from rag.embedding import get_embed_model

logger = get_logger(__name__)

cache = {}

def load_collection_index(collection_name:str):

    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    try:
        chroma_collection = chroma_client.get_collection(collection_name)
    except Exception:
        logger.warning("Geen collectie gevonden: %s. Voer eerst ingest uit", collection_name)
        return None  

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=get_embed_model()
    ) 

    logger.info("Collectie '%s' geladen met %s vectors", collection_name, chroma_collection.count())
    return index

def get_index(collection_name:str):
    if collection_name not in cache or cache[collection_name] is None:
        cache[collection_name] = load_collection_index(collection_name)
    return cache[collection_name]

def reload_index(collection_name:str):
    logger.info("Index wordt herladen voor collectie: %s", collection_name)
    cache[collection_name] = load_collection_index(collection_name)
    logger.info("Index succesvol herladen voor collectie: %s", collection_name)