from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb


DEBUG = True
DEBUG_CONTEXT = True

def debug_context(context):
    if DEBUG_CONTEXT:
        print("\n================ CONTEXT NAAR LLM ================\n")
        print(context)
        print("\n=================================================\n")

def log(msg):
    if DEBUG:
        print(f"[RAG] {msg}")

def load_index():

    embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        normalize=True
        )
    
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    try:
        chroma_collection = chroma_client.get_collection("docs")
    except Exception:
        print("Geen collectie gevonden. Voer eerst ingest uit")
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
    print("[QUERY] Index wordt herladen...")
    index = load_index()
    print("[QUERY] Index succesvol herladen.")

# def show_sources(nodes):
#     print("\nBronnen:\n")

#     shown = set()

#     for node in nodes:
        
#         meta = node.node.metadata
#         title = meta.get("title", "Geen titel")
#         url = meta.get("url")

#         identifier = url if url else title
#         if identifier not in shown:
#             print(f"- {title}")
#             if url:
#                 print(f"  Link: {url}")
#             shown.add(identifier)
