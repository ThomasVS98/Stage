import os, psutil, shutil, gc
import chromadb
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.node_parser import SentenceSplitter
from ingestion.loader_registry import get_loader
from rag.embedding import embed_model
from utils.logging import get_logger, setup_logging
from utils.config_loader import load_source_config
import ingestion.loaders.sharepoint_loader
import ingestion.loaders.topdesk_loader
import ingestion.loaders.onedrive_loader

load_dotenv()
setup_logging()

logger = get_logger(__name__)

def load_all_data():
    # all_docs = []

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
            # docs = loader(config)
            # count = 0
            for doc in loader(config): #docs:
                #all_docs.append(doc)
                #count += 1
                yield doc
            #logger.info("Aantal docs van %s: %s", source_type, count) #len(docs))
            # all_docs.extend(docs)
        except Exception as e:
            logger.exception("Fout bij laden van %s: %s", source_type, e)
        
    #logger.info("Totaal aantal documenten: %s", len(all_docs))

    #return all_docs
    
#def build_index(documents):
def build_index(document_generator):
    # if not documents:
    #     logger.warning("Geen documenten om te indexeren")
    #     return
    
    # for doc in documents:
    #     if "source_id" in doc.metadata:
    #         doc.doc_id = doc.metadata["source_id"]
            
    # logger.info("Indexeren van %s documenten naar ChromaDB...", len(documents))

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

    # index = VectorStoreIndex.from_documents(
    #     documents,
    #     storage_context=storage_context,
    #     embed_model=embed_model,
    #     transformations=[SentenceSplitter(chunk_size=700, chunk_overlap=100)],
    #     show_progress=True
    # )
    index = VectorStoreIndex(
        nodes=[],
        storage_context=storage_context,
        embed_model=embed_model,
        transformations=[SentenceSplitter(chunk_size=700, chunk_overlap=100)],
        show_progress=True
    )

    count = 0
    for doc in document_generator:
        if "source_id" in doc.metadata:
            doc.doc_id = doc.metadata["source_id"]
        
        index.insert(doc)
        count += 1

        if count % 20 == 0:
            gc.collect()
            logger.info("Progress: %s docs geïndexeerd. RAM: %.2f MB", count, psutil.Process().memory_info().rss / 1024**2)

    logger.info("Indexering klaar")
    gc.collect()
    logger.info("Totaal aantal chuncks in vector store: %s", chroma_collection.count())

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