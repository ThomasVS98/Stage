from rag.retriever import retrieve_nodes
from rag.reranker import rerank_nodes
from rag.prompts import detect_intent, generate_answer
from rag.llm import llm
from rag.query import get_index
from utils.logging import get_logger

logger = get_logger(__name__)


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

def handle_no_retrieval():
    return {
        "answer": "Ik heb niet genoeg informatie.",
        "sources": []
    }

def answer(query: str, debug: bool = True):

    logger.info("Ontvangen vraag: %s", query)

    idx = get_index()

    if idx is None:
        return {
            "answer": "De database is nog niet geïnitialiseerd. Eerst ingest.",
            "sources": []
        }
    
    all_nodes = retrieve_nodes(idx,query)

    if debug:
        logger.info("Opgehaalde blokken: %s", len(all_nodes))
        for node in all_nodes:
            logger.info("Retrieved node: %s", node.node.metadata.get('title'))

    if not all_nodes:
        return handle_no_retrieval()
    
    valid_nodes = rerank_nodes(all_nodes, query)

    if debug:
        logger.info("Chunks geselecteerd door Reranker:")
        for node in valid_nodes:
            logger.info("score %.3f | %s", node.score, node.node.metadata.get('title'))

    if not valid_nodes:
        return handle_no_results(query)

    best_score = valid_nodes[0].score
    logger.info("Relevantie gevonden! Best score: %.4f", best_score)
    logger.info(
        "Top bron: %s -  title: %s",
        valid_nodes[0].node.metadata.get('url'), 
        valid_nodes[0].node.metadata.get('title'))

    context = build_context(valid_nodes)
    if debug:
        logger.info(
            "\n================ CONTEXT NAAR LLM ================\n%s\n=================================================\n",
            context,
        )

    response = generate_answer(llm, context, query)

    answer_text = ""
    for token in response:
        if token.delta:
            answer_text += token.delta

    sources = extract_sources(valid_nodes)
        
    return {
        "answer": answer_text,
        "sources": sources
    }