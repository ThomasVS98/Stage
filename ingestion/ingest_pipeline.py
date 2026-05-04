import os, psutil, shutil, gc
import chromadb
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.node_parser import SentenceSplitter
from ingestion.loader_registry import get_loader
from rag.embedding import get_embed_model
from utils.logging import get_logger, setup_logging
from utils.config_loader import load_source_config
from utils.exceptions import ExternalServiceError
import ingestion.loaders.sharepoint_loader
import ingestion.loaders.topdesk_loader
import ingestion.loaders.onedrive_loader

setup_logging()

logger = get_logger(__name__)

def load_all_data():

    sources = load_source_config()
    logger.info("Aantal geconfigureerde bronnen: %s", len(sources))

    for source in sources:
        source_type = source.get("type")
        enabled = source.get("enabled", True)
        config = source.get("config", {})

        if not enabled:
            logger.info("Bron uitgeschakeld: %s", source_type)
            continue

        loader = get_loader(source_type)

        if not loader:
            logger.warning("Geen loader gevonden voor type: %s", source_type)
            continue

        logger.info("Start ingestie van bron: %s met config %s", source_type, config)
        try:
            for doc in loader(config):
                yield doc
        except ExternalServiceError:
            logger.exception("Kritische fout bij bron: %s", source_type)
            raise
        
        except Exception as e:
            logger.exception("Fout bij laden van %s: %s", source_type, e)

def create_index():
    chroma_client = chromadb.PersistentClient(path="./chroma_db")

    try:
        chroma_client.delete_collection("docs")
        logger.info("Bestaande collectie 'docs' verwijderd.")
    except Exception:
        logger.info("Geen collectie docs om te verwijderen")
        pass
    
    chroma_collection = chroma_client.get_or_create_collection(
        name = "docs",
        metadata = {"hnsw:space": "cosine"}
    )

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex(
        nodes=[],
        storage_context=storage_context,
        embed_model=get_embed_model(),
        #transformations=[SentenceSplitter(chunk_size=700, chunk_overlap=100)],
        show_progress=True
    )

    return index, chroma_collection

def process_documents(index, document_generator):
    batch = []
    BATCH_SIZE = 20
    count = 0
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=200)

    process = psutil.Process()

    for doc in document_generator:
        if "source_id" in doc.metadata:
            doc.doc_id = doc.metadata["source_id"]

        batch.append(doc)

        if len(batch) == BATCH_SIZE:
            nodes = splitter.get_nodes_from_documents(batch)
            index.insert_nodes(nodes)
            count += len(batch)
            batch = []

            gc.collect()
            logger.info(
                "Progress: %s docs geïndexeerd. RAM: %.2f MB",
                count,
                process.memory_info().rss / 1024**2
            )

    # laatste batch verwerken
    if batch:
        nodes = splitter.get_nodes_from_documents(batch)
        index.insert_nodes(nodes)
        count += len(batch)

    return count
        
def build_index(document_generator):
    index, chroma_collection = create_index()

    count =  process_documents(index, document_generator)

    logger.info("Indexering klaar")
    logger.info("Totaal aantal chunks in vector store: %s", chroma_collection.count())

    return count

def cleanup_temp_files():
    temp_dirs = [
        "./temp_sharepoint",
        "./temp_onedrive"
    ]
    
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info("Tijdelijke map %s verwijderd.", temp_dir)