from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.schema import QueryBundle
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.schema import NodeWithScore
import chromadb
import re
from sentence_transformers import CrossEncoder


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
    chroma_collection = chroma_client.get_collection("docs")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    
    storage_context = StorageContext.from_defaults(
        vector_store=vector_store,
        persist_dir="./storage"
        )

    index = load_index_from_storage(
        storage_context=storage_context,
        embed_model=embed_model
    )

    # index = VectorStoreIndex.from_vector_store(
    #     vector_store,
    #     embed_model=embed_model
    # )

    print("Docstore size:", len(storage_context.docstore.docs))

    return index

index = load_index()

def reload_index():
    """Forceert het herladen van de index na een ingestie."""
    global index
    index = load_index()
    print("[QUERY] Index succesvol herladen.")

llm = Ollama(
    model="llama3.2:3b", #mistral:7b
    request_timeout=300,
    context_window=6144,
    temperature=0
)

reranker = SentenceTransformerRerank(
    model="BAAI/bge-reranker-v2-m3",
    top_n=3
)

# reranker = SentenceTransformerRerank(
#     model="cross-encoder/ms-marco-MiniLM-L12-v2",
#     top_n=6
# )

def build_context(nodes):

    context = ""

    for node in nodes:

        text = node.node.get_content()
        metadata = node.node.metadata

        title = metadata.get("title", "Geen titel")
        source = metadata.get("source", "Geen bron")
        url = metadata.get("url", "Geen URL")

        context += f"""
        [DOCUMENT]
        Bron: {source}      
        Titel: {title}
        URL: {url}

        Tekst:
        {text}
        [/DOCUMENT]
        """
    return context


def ask_llm(llm, context, query):

    prompt = f"""

    Je bent een IT-assistent voor de medewerkers van de Thomas More hogeschool.

    RICHTLIJNEN:
    1.Antwoord uitsluitend op basis van de onderstaande context.
    2.Gebruik enkel expliciete informatie; maak onder geen omstandigheden aannames of eigen interpretaties.
    3.Als een specifiek detail (zoals een knopnaam of URL) niet in de tekst staat, verzin deze dan niet.
    4.Alleen als er TOTAAL geen informatie over het onderwerp in de context staat, zeg je: "ik heb niet genoeg informatie".
    5.Gebruik GEEN verwijzingen naar documenten, titels of bronnen in je antwoord.
    6.Noem tijdslimieten, aantallen, voorwaarden en volgorde precies zoals ze in de context staan. Geef procedures en deadlines letterlijk weer.
    7.Schrijf een direct antwoord voor de gebruiker. Gebruik NOOIT formuleringen zoals "volgens de context", "in de tekst staat", "het document zegt" of gelijkaardige bronverwijzingen.
    8.Geef NOOIT je eigen mening of interpretaties. Volg de informatie van de context.

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
        
        meta = node.node.metadata
        title = meta.get("title", "Geen titel")
        url = meta.get("url")

        identifier = url if url else title
        if identifier not in shown:
            print(f"- {title}")
            if url:
                print(f"  Link: {url}")
            shown.add(identifier)

#functie voor FastAPI
def ask_question(query: str):

    log(f"[API] Ontvangen vraag: {query}")

    base_retriever = index.as_retriever(
        similarity_top_k=20,
        #vector_store_query_mode="mmr",
        #mmr_threshold=0.5,
        filters=None
    )

    retriever = AutoMergingRetriever(
        base_retriever,
        storage_context=index.storage_context,
        verbose=True
    )

    all_nodes = retriever.retrieve(query)

    if not all_nodes:
        return {
            "answer": "Ik heb niet genoeg informatie.",
            "sources": []
        }
    
    valid_nodes = reranker.postprocess_nodes(
            all_nodes,
            query_bundle=QueryBundle(query_str=query)
        )
    
    if not valid_nodes or valid_nodes[0].score < 0.30:
        log(f"[API] Geen relevante resultaten na reranking. Best score: {valid_nodes[0].score if valid_nodes else 'None'}")
        return {
            "answer": "Ik heb niet genoeg informatie om deze vraag te beantwoorden. Er is mogelijk een intake noodzakelijk.",
            "sources": []
        }

    best_score = valid_nodes[0].score
    log(f"[API] Relevantie gevonden! Best score: {best_score:.4f}")
    log(f"[API] Top bron: {valid_nodes[0].node.metadata.get('url')}")

    context = build_context(valid_nodes)

    response = ask_llm(llm, context, query)

    answer = ""
    for token in response:
        answer += token.delta

    sources = []

    for node in valid_nodes:
        meta = node.node.metadata
        title = meta.get("title")
        url = meta.get("url")
        source_str = f"{title} ({url})" if url else title
        if source_str and source_str not in sources:
            sources.append(source_str)
        
    return {
        "answer": answer,
        "sources": sources
    }

def main():
    while True:

        query = input("\nVraag: ")

        log(f"Vraag: {query}")

        if query == "exit":
            break

        # retriever = index.as_retriever(
        #     similarity_top_k=20,
        #     #vector_store_query_mode="mmr",
        #     #mmr_threshold=0.5,
        #     filters=None
        # )

        base_retriever = index.as_retriever(
            similarity_top_k=30,
            filters=None
        )

        retriever = AutoMergingRetriever(
            base_retriever,
            storage_context=index.storage_context,
            verbose=True
        )
            
        all_nodes = retriever.retrieve(query)
        log(f"Opgehaalde blokken: {len(all_nodes)}")

        for node in all_nodes:
            log(f"Retrieved node: {node.node.metadata.get('title')}")
            log(f"Node ID: {node.node.node_id} | Text length: {len(node.node.get_content())}")

        valid_nodes = reranker.postprocess_nodes(
            all_nodes,
            query_bundle=QueryBundle(query_str=query)
        )

        if not valid_nodes or valid_nodes[0].score < 0.18:
            log(f"Geen relevante resultaten na reranking. Best score: {valid_nodes[0].score if valid_nodes else 'None'}")
            print("\nIk heb niet genoeg informatie om deze vraag te beantwoorden. Intake opstarten...\n")
            continue
                
        log("Chunks geselecteerd door Reranker:")
        for node in valid_nodes:
            log(f"score {node.score:.3f} | {node.node.metadata.get('url')}")

        context = build_context(valid_nodes)
        debug_context(context)

        print("\nAntwoord:\n")

        response_total = ask_llm(llm, context, query)

        for response in response_total:
            print(response.delta, end="", flush=True)
        print("\n")
        show_sources(valid_nodes)


if __name__ == "__main__":
    main()
