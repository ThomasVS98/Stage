import os
import re
import chromadb
from dotenv import load_dotenv
from llama_index.core import Document, SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter, HierarchicalNodeParser, get_leaf_nodes
from sharepoint_fetcher import fetch_all_sharepoint_pages, fetch_sharepoint_files, download_sharepoint_file
import shutil

load_dotenv()

LMS_SITE_ID = os.getenv("LMS_SITE_ID")
SERVICE_CATALOG_ID = os.getenv("SERVICE_CATALOG_ID")

def clean_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n", "\n", text) 
    return text.strip()

def extract_urls(text):
    """Haalt URLs uit platte tekst (vooral nuttig voor SharePoint PDF/Docs)."""
    url_pattern = r"https?://[^\s]+"
    urls = re.findall(url_pattern, text)
    return [url.rstrip(".,;:!?)\"'") for url in urls]

def load_all_sharepoint_data():
    all_docs = []
    print("Sharepoint pagina's ophalen")
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
            new_doc.excluded_llm_metadata_keys = ["url", "source_id", "file_name"]
            all_docs.append(new_doc)
        else:
            print(f"Geen pagina's gevonden voor {label}")

    print("Sharepoint bestanden ophalen")
    sp_files = fetch_sharepoint_files(LMS_SITE_ID, "LMS Files")
    temp_dir = "./temp_sharepoint"
    os.makedirs(temp_dir, exist_ok=True)

    if sp_files:
        for file in sp_files:
            meta = file["metadata"]
            filename = meta["filename"]
            dl_url = meta["download_url"]
            file_path = os.path.join(temp_dir, filename)

            print(f"Bezig met ophalen: {filename}...")
            if download_sharepoint_file(dl_url, file_path):
                reader = SimpleDirectoryReader(input_files=[file_path])
                file_docs = reader.load_data()

                full_content = "\n\n".join([d.text for d in file_docs])
                full_content = clean_text(full_content)

                clean_meta = meta.copy()
                clean_meta.pop("download_url", None)
                
                new_doc = Document(
                    text = full_content,
                    metadata = clean_meta
                )
                new_doc.metadata["source_type"] = "sharepoint_file"
                new_doc.excluded_embed_metadata_keys = ["url", "download_url", "source_id"]
                new_doc.excluded_llm_metadata_keys = ["url", "source_id", "filename"]
                all_docs.append(new_doc)
            else:
                print(f"Download mislukt voor {filename}")
        
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

    # index = VectorStoreIndex.from_documents(
    #     documents,
    #     storage_context=storage_context,
    #     embed_model=embed_model,
    #     transformations=[SentenceSplitter(chunk_size=550, chunk_overlap=80)],
    #     show_progress=True
    # )

    node_parser = HierarchicalNodeParser.from_defaults(
        chunk_sizes=[1200,350]
    )

    nodes = node_parser.get_nodes_from_documents(documents)
    leaf_nodes = get_leaf_nodes(nodes)

    storage_context.docstore.add_documents(nodes)

    index = VectorStoreIndex(
        leaf_nodes,
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=True
    )

    storage_context.persist(persist_dir="./storage")

    print(f"\n Indexering klaar")
    print(f"Totaal aantal chuncks in vector store: {chroma_collection.count()}")
    print("Docstore size:", len(storage_context.docstore.docs))

    return index

def cleanup_temp_files(temp_dir="./temp_sharepoint"):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        print(f"Tijdelijke map {temp_dir} verwijderd.")

if __name__ == "__main__":

    docs = load_all_sharepoint_data()
    if docs:
        build_index(docs)
        cleanup_temp_files()
    else:
        print("Geen documenten gevonden om te verwerken")