from rag.retriever import retrieve_nodes
from rag.reranker import rerank_nodes
from rag.vector_store import get_index
from langfuse import observe
from utils.logging import get_logger

SIMILARITY_THRESHOLD = 0.65

logger = get_logger(__name__)


@observe(name="find_similar_ticket")
def find_similar_ticket(data: dict):
    query = f"""
    Probleem: {data.get("beschrijving")}
    Context: {data.get("context")}
    Doel: {data.get("doel")}
    """
    index = get_index("tickets")

    if index is None:
        logger.warning("Ticket index niet geladen")
        return None

    nodes = retrieve_nodes(index, query)
    nodes = rerank_nodes(nodes, query, threshold=0.40)

    if not nodes:
        return None

    best = nodes[0]
    logger.info("Beste score: %.3f", best.score)

    if best.score >= SIMILARITY_THRESHOLD:
        return {"score": float(best.score), "text": best.node.get_content()}
    return None
