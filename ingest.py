from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
import chromadb
import re


# functie om urls te halen uit documenten
def extract_urls(text):
    url_pattern = r"https?://[^\s]+"
    urls = re.findall(url_pattern, text)

    clean_urls = []
    for url in urls:
        url = url.rstrip(".,;:!?)\"'")  # Verwijder trailing leestekens
        clean_urls.append(url)

    return clean_urls

def clean_text(text: str) -> str:
    text = re.sub(r"\n{3,}","\n\n",text)
    text = re.sub(r"[ \t]{2,}"," ",text)
    text = text.strip()
    return text

def extract_title(text):
    lines = text.split("\n")

    for line in lines:
        line = line.strip()
        if len(line) > 5:
            return line[:120]
        
    return "Geen titel in document"

# functie om documenten te laden
def load_documents():

    documents = SimpleDirectoryReader(
        input_dir="./data",
        recursive=True
    ).load_data()

    print("Aantal documenten: ", len(documents))

    for doc in documents:

        text = clean_text(doc.text)
        urls = extract_urls(text)
        doc.metadata["urls"] = " | ".join(urls) if urls else None
        doc.metadata["url_count"] = len(urls)

        file_path = doc.metadata.get("file_path", "").lower()
        if "kaltura" in file_path:
            doc.metadata["service"] = "kaltura"
        elif "proctorio" in file_path:
            doc.metadata["service"] = "proctorio"
        else:
            doc.metadata["service"] = "unknown"

        file_name = doc.metadata.get("file_name", "").lower()
        if file_name.endswith(".pdf"):
            doc.metadata["file_type_simple"] = "pdf"
        elif file_name.endswith(".docx"):
            doc.metadata["file_type_simple"] = "word"
        elif file_name.endswith(".txt"):
            doc.metadata["file_type_simple"] = "text"
        else:
            doc.metadata["file_type_simple"] = "unknown"

        doc.metadata["source_file"] = doc.metadata.get("file_name")
        doc.doc_id = doc.metadata.get("file_name") or doc.id_

        title = extract_title(text)
        doc.metadata["title"] = title
        # new_content = f"Titel: {title}\n\n{text}"
        # doc.set_content(new_content)

        if urls:
            print(f"URLs gevonden in {doc.metadata['file_name']}:")
            for url in urls:
                print(" ",url)
   
    return documents

# functie om te indexeren ahv chroma vector store en mpnet embedding
def build_index(documents):

    # embedding model definiëren
    embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2" #intfloat/multilingual-e5-base
    )

    # chroma
    chroma_client = chromadb.PersistentClient(path="./chroma_db")

    try:
        chroma_client.delete_collection("docs")
    except:
        pass

    chroma_collection = chroma_client.get_or_create_collection(
        name = "docs",
        metadata={"hnsw:space": "cosine"},
        )

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    storage_context = StorageContext.from_defaults(vector_store=vector_store)


    # index maken
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_model=embed_model,
        transformations=[SentenceSplitter(chunk_size=500, chunk_overlap=75)],
        show_progress=True
    )

    print("index gemaakt")
    print("Aantal vectors in database",chroma_collection.count())
    
    return index

def main():
    documents = load_documents()
    build_index(documents)

if __name__ == "__main__":
    main()





