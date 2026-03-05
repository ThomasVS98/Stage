from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb

def load_index():

    embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    )

    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    chroma_collection = chroma_client.get_collection("docs")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=embed_model,
    )

    return index

def create_retriever(index):
    
    retriever = index.as_retriever(
        similarity_top_k=3
    )

    return retriever

def run_query(retriever, query):

    nodes = retriever.retrieve(query)

    for i,node in enumerate(nodes):

        metadata = node.node.metadata

        print("\n==========================")
        print("Resultaat", i+1)
        print("==========================")

        print("\nScore:", node.score)

        print("\nTitel:", metadata.get("title"))

        print("Service:", metadata.get("service"))

        print("Bronbestand:", metadata.get("source_file"))

        print("URLs:", metadata.get("urls"))

        print("\nTekst:\n")
        print(node.node.text[:500])

def main():
    print("Index laden...")
    index = load_index()

    retriever = create_retriever(index)

    while True:

        query = input("\nVraag: ")
        
        if query == "exit":
            break
        
        run_query(retriever, query)
    
if __name__ == "__main__":
    main()
        
