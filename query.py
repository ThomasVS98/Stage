from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
import chromadb
import re


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
        [DOCUMENT]
        Bron: {source}      
        Titel: {title}

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
    5.GEEF EEN VOLLEDIG ANTWOORD: Noem specifieke voorbeelden, knoppen of situaties die in de tekst staan (zoals apparaten, bestandstypes of specifieke scenario's).
    6.BELANGRIJK: De onderstaande context bevat informatie uit MEERDERE documenten. Scan ALLE documenten hieronder om een compleet overzicht te geven.

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


_DUTCH_STOPWORDS = {
    "de","het","een","en","of","voor","van","op","in","met","naar","aan","bij","door","over",
    "ik","je","jij","u","uw","we","wij","ze","zij","mijn","me","maar","niet","wel",
    "hoe","wat","waar","wanneer","waarom","kan","kun","kunnen","is","zijn","worden","doen",
    "vandaag","graag","even"
}

def _tokens(s: str) -> set[str]:
    parts = re.findall(r"[a-zA-Z0-9]+", (s or "").lower())
    return {p for p in parts if len(p) >= 3 and p not in _DUTCH_STOPWORDS}

def lexical_overlap_count(query: str, nodes, max_nodes: int = 10) -> int:
    q = _tokens(query)
    if not q:
        return 0
    text = " ".join(n.node.get_text().lower() for n in nodes[:max_nodes])
    t = _tokens(text)
    return len(q.intersection(t))


def main():

    index = load_index()
    llm = Ollama(
        model="llama3.2:3b", #mistral:7b
        request_timeout=120,
        context_window=4096
    )


    while True:

        query = input("\nVraag: ")
        log(f"Vraag: {query}")

        if query == "exit":
            break

        service = detect_service(query)
        log(f"Service filter: {service if service else 'geen'}")

        retriever = index.as_retriever(
            similarity_top_k=12,
            #vector_store_query_mode="mmr",
            #mmr_threshold=0.5,
            # filters=MetadataFilters(
            #     filters=[ExactMatchFilter(key="service", value=service)]
            # ) if service else None
        )
            
        all_nodes = retriever.retrieve(query)
        log(f"Opgehaalde blokken: {len(all_nodes)}")

        print("\nDEBUG scores:")
        for node in all_nodes[:5]:
            print(node.score, node.node.metadata.get("source_file"))

        if not all_nodes:
            print("\nIk heb niet genoeg informatie om deze vraag te beantwoorden.\n")
            continue

        scores = [n.score for n in all_nodes if n.score is not None]
        if not scores:
            print("\nIk heb niet genoeg informatie om deze vraag te beantwoorden.\n")
            continue

        best_score = min(scores)
        avg_score = sum(scores[:5]) / min(len(scores), 5)
        log(f"Beste score: {best_score:.3f}")
        log(f"Gemiddelde score (top5): {avg_score:.3f}")

        if best_score >= 0.70:
            log("Geen antwoord: beste score boven threshold.")
            print("\nIk heb niet genoeg informatie om deze vraag te beantwoorden.\n")
            continue

        if avg_score >= 0.75:
            log("Geen antwoord: gemiddelde score te hoog.")
            print("\nIk heb niet genoeg informatie om deze vraag te beantwoorden.\n")
            continue

        overlap = lexical_overlap_count(query, all_nodes, max_nodes=10)
        log(f"Lexical overlap: {overlap}")

        if overlap < 1:
            log("Geen antwoord: geen of te weinig overlap.")
            print("\nIk heb niet genoeg informatie om deze vraag te beantwoorden.\n")
            continue


        valid_nodes = [n for n in all_nodes if n.score is not None and n.score < 0.70]
        log(f"Valide blokken onder threshold < 0.70: {len(valid_nodes)}")

        min_node_count = 6

        if len(valid_nodes) < min_node_count:
            log("Geen antwoord: onvoeldoende relevante blokken gevonden.")
            print(f"\nDEBUG: Slechts {len(valid_nodes)} relevant(e) blok(ken) gevonden. Dit is onvoldoende.")
            continue
        
        valid_nodes.sort(key=lambda n: n.score if n.score is not None else 1.0)
        valid_nodes = valid_nodes[:6]
        log("Chunks gebruikt for het antwoord:")
        for node in valid_nodes:
            source = node.node.metadata.get("source_file")
            log(f"score {node.score:.3f} | {source}")

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
