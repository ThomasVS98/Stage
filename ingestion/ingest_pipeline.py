import os
import chromadb
from dotenv import load_dotenv
from llama_index.core import Document, SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
from ingestion.loaders.sharepoint_loader import fetch_all_sharepoint_pages, fetch_sharepoint_files, download_sharepoint_file
from ingestion.loaders.topdesk_fetcher import fetch_topdesk_documents
from ingestion.preprocessing.cleaning import clean_text, clean_markdown
from ingestion.preprocessing.docling_parser import extract_with_docling
import shutil

load_dotenv()

LMS_SITE_ID = os.getenv("LMS_SITE_ID")
SERVICE_CATALOG_ID = os.getenv("SERVICE_CATALOG_ID")

DEBUG_DOCLING = True
DEBUG_FILE = None

def create_document_from_file(content:str, metadata:dict):
    clean_meta = metadata.copy()
    clean_meta.pop("download_url", None)
                
    new_doc = Document(
        text = content,
        metadata = clean_meta
    )

    new_doc.metadata["source_type"] = "sharepoint_file"
    new_doc.excluded_embed_metadata_keys = ["url", "download_url", "source_id"]
    new_doc.excluded_llm_metadata_keys = ["url", "source_id", "filename"]

    return new_doc

def load_sharepoint_pages():
    docs = []

    sites = [
        (LMS_SITE_ID, "LMS Site"),
        (SERVICE_CATALOG_ID, "IT Service Catalog")
    ]

    for site_id, label in sites:
        sp_pages = fetch_all_sharepoint_pages(site_id, label)
        if sp_pages:
          for page in sp_pages:
            full_text = page["content"]
            new_doc = Document(
               text = full_text,
               metadata = page["metadata"]
            )
            new_doc.metadata["source_type"] = "sharepoint_page"
            new_doc.excluded_embed_metadata_keys = ["url","source_id"]
            new_doc.excluded_llm_metadata_keys = ["url", "source_id"]
            docs.append(new_doc)
        else:
            print(f"Geen pagina's gevonden voor {label}")
    return docs

def load_sharepoint_files():
    docs = []

    sp_files = fetch_sharepoint_files(LMS_SITE_ID, "LMS Files")
    temp_dir = "./temp_sharepoint"
    os.makedirs(temp_dir, exist_ok=True)

    if not sp_files:
        return docs
    
    for file in sp_files:
        meta = file["metadata"]
        filename = meta["filename"]
        dl_url = meta["download_url"]
        file_path = os.path.join(temp_dir, filename)

        print(f"Bezig met ophalen: {filename}...")

        if not download_sharepoint_file(dl_url, file_path):
            print(f"Download mislukt voor {filename}")
            continue
        full_content = process_file(file_path, filename)
        new_doc = create_document_from_file(full_content, meta)
        docs.append(new_doc)

    return docs
    
def process_file(file_path:str, filename:str)->str:

    if filename.lower().endswith((".pdf", ".docx")):
        print(f"[DOCLING] Verwerken met Docling: {filename}")

        full_content = extract_with_docling(file_path)
        full_content = clean_markdown(full_content)
        full_content = clean_text(full_content)
    else:
        reader = SimpleDirectoryReader(input_files=[file_path])
        file_docs = reader.load_data()
        full_content = "\n\n".join([d.text for d in file_docs])
        full_content = clean_text(full_content)

    return full_content

def load_topdesk_docs():
    try:
        topdesk_docs = fetch_topdesk_documents()
        print(f"Topdesk documenten gevonden: {len(topdesk_docs)}")
        return topdesk_docs
    except Exception as e:
        print(f"Topdesk ophalen mislukt: {e}")
        return []

def load_all_data():
    all_docs = []

    print("Sharepoint pagina's ophalen")
    all_docs.extend(load_sharepoint_pages())

    print("Sharepoint bestanden ophalen")
    all_docs.extend(load_sharepoint_files())

    print("Topdesk documenten ophalen")
    all_docs.extend(load_topdesk_docs())

    return all_docs
    
def build_index(documents):
    if not documents:
        print("Geen documenten om te indexeren")
        return
    
    for doc in documents:
        if "source_id" in doc.metadata:
            doc.doc_id = doc.metadata["source_id"]
            
    print(f"\n Indexeren van {len(documents)} documenten naar ChromaDB...")

    if os.path.exists("./storage"):
        shutil.rmtree("./storage")
        print("Bestaande storage folder verwijderd voor schone start.")


    embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        normalize=True
    )

    chroma_client = chromadb.PersistentClient(path="./chroma_db")

    try:
        chroma_client.delete_collection("docs")
        print("Bestaande collectie 'docs' verwijderd.")
    except:
        pass
    
    chroma_collection = chroma_client.get_or_create_collection(
        name = "docs",
        metadata = {"hnsw:space": "cosine"}
    )

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=embed_model,
        transformations=[SentenceSplitter(chunk_size=700, chunk_overlap=100)],
        show_progress=True
    )

    print(f"\n Indexering klaar")
    print(f"Totaal aantal chuncks in vector store: {chroma_collection.count()}")

    return index

def cleanup_temp_files(temp_dir="./temp_sharepoint"):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        print(f"Tijdelijke map {temp_dir} verwijderd.")

if __name__ == "__main__":

    docs = load_all_data()
    if docs:
        build_index(docs)
        cleanup_temp_files()
    else:
        print("Geen documenten gevonden om te verwerken")