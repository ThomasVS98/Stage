from rag.retriever import retrieve_nodes
from rag.reranker import rerank_nodes
from rag.prompts import detect_intent, generate_answer
from rag.llm import llm
from query import get_index, log


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


#functie voor FastAPI
def answer(query: str, debug: bool = False):

    log(f"[API] Ontvangen vraag: {query}")

    idx = get_index()

    if idx is None:
        return {
            "answer": "De database is nog niet geïnitialiseerd. Eerst ingest.",
            "sources": []
        }
    
    all_nodes = retrieve_nodes(idx,query)

    if debug:
        log(f"Opgehaalde blokken: {len(all_nodes)}")
        for node in all_nodes:
            log(f"Retrieved node: {node.node.metadata.get('title')}")

    if not all_nodes:
        return {
            "answer": "Ik heb niet genoeg informatie.",
            "sources": []
        }
    
    valid_nodes = rerank_nodes(all_nodes, query)

    if debug:
        log("Chunks geselecteerd door Reranker:")
        for node in valid_nodes:
            log(f"score {node.score:.3f} | {node.node.metadata.get('title')}")

    if not valid_nodes:
        intent = detect_intent(llm, query)
        log(f"[INTENT] {intent}")
        log(f"[API] Geen relevante resultaten na reranking.")

        if intent == "SUPPORT":
            return {
                "answer": "Er is momenteel nog niet genoeg informatie hierover. Ik zal enkele vragen stellen om een ticket te kunnen aanmaken.",
                "sources": [],
                "action": "INTAKE"
            }
        elif intent == "ALGEMEEN":
            return {
                "answer": "Er is momenteel nog niet genoeg informatie hierover.",
                "sources": []
            }
        elif intent == "IRRELEVANT":
            return {
                "answer": "Deze vraag lijkt niet relevant. Ik kan hier helaas niet mee helpen.",
                "sources": []
            }
        else:
            return {
                "answer": "Ik kon de vraag niet goed interpreteren.",
                "sources": []
            }

    best_score = valid_nodes[0].score
    log(f"[API] Relevantie gevonden! Best score: {best_score:.4f}")
    log(f"[API] Top bron: {valid_nodes[0].node.metadata.get('url')} title: {valid_nodes[0].node.metadata.get('title')}")

    context = build_context(valid_nodes)
    if debug:
        print("\n================ CONTEXT NAAR LLM ================\n")
        print(context)
        print("\n=================================================\n")


    response = generate_answer(llm, context, query)

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
