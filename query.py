from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
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

def build_context(nodes):

    context = ""

    for node in nodes:

        text = node.node.get_text()
        metadata = node.node.metadata

        title = metadata.get("title")
        source = metadata.get("source_file")

        context += f"""
        Bron: {source}      
        Titel: {title}

        {text}
        ------------------------------
        """
    return context

def ask_llm(llm, context, query):

    prompt = f"""

    Je bent een IT-assistent voor de medewerkers van de Thomas More hogeschool.

    Gebruik uitsluitend de onderstaande context om de vraag te beantwoorden.
    Als het antwoord niet in de context staat, antwoor dan EXACT het volgende
    zonder nog iets toe te voegen: "ik heb niet genoeg informatie".

    Context:
    {context}

    Vraag:
    {query}

    Antwoord: 
    """

    return llm.stream_complete(prompt)

def show_sources(nodes):
    print("\nBronnen:\n")

    shown = set()

    for node in nodes:
        
        metadata = node.node.metadata
        source = metadata.get("source_file")
        urls = metadata.get("urls")

        if source and source not in shown:

            print(source)
            if urls:
                for url in urls.split(" | "):
                    print(url)
            print()

            shown.add(source)

def detect_service(query):

    query = query.lower()

    if "kaltura" in query:
        return "kaltura"
    
    if "proctorio" in query:
        return "proctorio"

    return None

def main():

    print("Index laden...")
    index = load_index()

    llm = Ollama(
        model = "llama3.2:3b", # mistral:7b voor alternatief zwaarder model
        request_timeout=120,
        context_window=4096
    )


    while True:

        query = input("\nVraag: ")

        if query == "exit":
            break

        service = detect_service(query)
        if service:
            filters = MetadataFilters(filters=[ExactMatchFilter(key="service", value=service)])
            retriever = index.as_retriever(similarity_top_k=3,filters=filters)
        else:
            retriever = index.as_retriever(similarity_top_k=3)

        nodes = retriever.retrieve(query)

        valid_nodes = [n for n in nodes if n.score < 0.45]

        min_node_count = 3

        if len(valid_nodes) < min_node_count:
            print(f"\nDEBUG: Slechts {len(valid_nodes)} relevant(e) blok(ken) gevonden. Dit is onvoldoende.")
            continue

        context = build_context(valid_nodes)[:3000]

        print("\nAntwoord:\n")

        response_total = ask_llm(llm, context, query)

        for response in response_total:
            print(response.delta, end="", flush=True)
        print("\n")
        show_sources(valid_nodes)


if __name__ == "__main__":
    main()
