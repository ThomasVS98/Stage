from concurrent.futures import ThreadPoolExecutor
from rag.prompts import detect_intent, judge_answer
from rag.llm import get_llm
from rag.pipeline import run_rag
from langfuse import observe
from utils.logging import get_logger

logger = get_logger(__name__)
executor = ThreadPoolExecutor(max_workers=2)

@observe(name="intake_trigger")
def handle_no_results(query: str):
    intent = detect_intent(get_llm(), query)
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
        source = meta.get("source")

        if source == "topdesk":
            sources.append(f"{title} (TOPdesk)")
        else:
            sources.append(f"{title}: {url}")

    return sources


def run_judge_async(llm, query, context, answer_text):
    try:
        judge = judge_answer(
            llm,
            query=query,
            context=context,
            answer=answer_text
        )

        logger.info("JUDGE: %s", judge)

    except Exception:
        logger.exception("Judge failed")

@observe(name="answer")
def answer(query: str, debug: bool = True):

    logger.info("Ontvangen vraag: %s", query)
    nodes, answer_text, context = run_rag(query,debug=debug)

    if nodes is None:
        return {
            "answer": "De database is nog niet geïnitialiseerd. Eerst ingest.",
            "sources": []
        }
    if nodes == []:
        return handle_no_results(query)
    
    sources = extract_sources(nodes)


    llm = get_llm()

    executor.submit(
        run_judge_async, 
        llm, query, context, answer_text
    )


    return {
        "answer": answer_text,
        "sources": sources
    }