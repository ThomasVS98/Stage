import chromadb
from ingestion.loaders.topdesk_loader import fetch_topdesk_incidents, incidents_to_documents
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter

def build_ticket_index(limit=200):
    print("Topdesk tickets ophalen...")

    items = fetch_topdesk_incidents(limit=limit)
    print(f"{len(items)} tickets opgehaald")

    documents = incidents_to_documents(items)
    print(f"{len(documents)} documenten gemaakt")

    embed_model = HuggingFaceEmbedding(
        model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        normalize=True
    )

    chroma_client = chromadb.PersistentClient(path="./chroma_db")

    try:
        chroma_client.delete_collection("tickets")
        print("Bestaande tickets collectie verwijderd")
    except:
        pass

    collection = chroma_client.get_or_create_collection(
        name = "tickets",
        metadata={"hnsw:space": "cosine"}
    )

    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    print("Indexeren...")

    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=embed_model,
        transformations=[SentenceSplitter(chunk_size=2000, chunk_overlap=0)],
        show_progress=True
    )

    print(f"Klaar. Aantal vectors: {collection.count()}")
    return index

if __name__ == "__main__":
    build_ticket_index(limit=200)