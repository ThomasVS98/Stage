from rag.vector_store import get_index
from rag.retriever import retrieve_nodes
from rag.reranker import rerank_nodes
from rag.context_builder import build_context
from rag.prompts import generate_answer
from rag.llm import llm
from utils.logging import get_logger

logger = get_logger(__name__)


def run_rag(query: str, collection: str = "docs", debug: bool = False):
    idx = get_index(collection)

    if idx is None:
        return None, None
    
    nodes = retrieve_nodes(idx, query)

    if debug:
        logger.info("Opgehaalde blokken: %s", len(nodes))
        for node in nodes:
            logger.info("Retrieved node: %s", node.node.metadata.get('title'))

    if not nodes:
        return [], None
    
    valid_nodes = rerank_nodes(nodes, query)

    if debug:
        logger.info("Chunks geselecteerd door Reranker:")
        for node in valid_nodes:
            logger.info("score %.3f | %s", node.score, node.node.metadata.get('title'))

    if not valid_nodes:
        return [], None
    
    if debug:
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

    return valid_nodes, answer_text