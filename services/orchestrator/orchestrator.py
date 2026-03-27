from rag.prompts import detect_intent
from rag.llm import llm
from rag.pipeline import run_rag
from utils.logging import get_logger

logger = get_logger(__name__)

def handle_no_results(query: str):
    intent = detect_intent(llm, query)
    logger.info("Intent: %s", intent)
    logger.info("Geen relevante resultaten na reranking.")

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
    
def extract_sources(nodes):
    sources = []

    for node in nodes:
        meta = node.node.metadata
        title = meta.get("title")
        url = meta.get("url")
        source_str = f"{title} ({url})" if url else title
        if source_str and source_str not in sources:
            sources.append(source_str)

    return sources

def answer(query: str, debug: bool = True):

    logger.info("Ontvangen vraag: %s", query)
    nodes, answer_text = run_rag(query,debug=debug)

    if nodes is None:
        return {
            "answer": "De database is nog niet geïnitialiseerd. Eerst ingest.",
            "sources": []
        }
    if nodes == []:
        return handle_no_results(query)
    
    sources = extract_sources(nodes)

    return {
        "answer": answer_text,
        "sources": sources
    }