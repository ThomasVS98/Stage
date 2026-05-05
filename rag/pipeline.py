from rag.vector_store import get_index
from rag.retriever import retrieve_nodes
from rag.reranker import rerank_nodes
from rag.context_builder import build_context
from rag.prompts import generate_answer
from rag.llm import get_llm
from langfuse import observe
from utils.logging import get_logger
from typing import Tuple, List, Any

logger = get_logger(__name__)


@observe(name="rag_pipeline")
def run_rag(
    query: str, collection: str = "docs", debug: bool = False
) -> Tuple[List[Any] | None, str | None, str | None]:
    """
    Voert de volledige RAG pipeline uit.

    Stappen:
    - ophalen van relevante documenten (retrieval)
    - herordenen op relevantie (reranking)
    - bouwen van context
    - genereren van antwoord via LLM

    Args:
        query (str): De gebruikersvraag
        collection (str): Naam van de vector store collectie
        debug (bool): Indien True, extra logging

    Returns:
        tuple: (nodes, answer, context)
    """
    idx = get_index(collection)

    if idx is None:
        return None, None, None

    nodes = retrieve_nodes(idx, query)

    if debug:
        logger.info("Opgehaalde blokken: %s", len(nodes))
        for node in nodes:
            logger.info("Retrieved node: %s", node.node.metadata.get("title"))

    if not nodes:
        return [], None, None

    valid_nodes = rerank_nodes(nodes, query)

    if debug:
        logger.info("Chunks geselecteerd door Reranker:")
        for node in valid_nodes:
            logger.info("score %.3f | %s", node.score, node.node.metadata.get("title"))

    if not valid_nodes:
        return [], None, None

    if debug:
        best_score = valid_nodes[0].score
        logger.info("Relevantie gevonden! Best score: %.4f", best_score)
        logger.info(
            "Top bron: %s -  titel: %s",
            valid_nodes[0].node.metadata.get("url"),
            valid_nodes[0].node.metadata.get("title"),
        )

    context = build_context(valid_nodes)

    if debug:
        logger.info(
            "\n================ CONTEXT NAAR LLM ================\n%s\n=================================================\n",
            context,
        )

    answer_text = generate_answer(get_llm(), context, query)

    return valid_nodes, answer_text, context
