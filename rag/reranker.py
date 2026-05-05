from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core import QueryBundle
from llama_index.core.schema import NodeWithScore
from langfuse import observe

_reranker = None


def get_reranker() -> SentenceTransformerRerank:
    """
    Initialiseert en cachet de reranker instantie.

    Laadt het SentenceTransformer reranker model éénmalig
    en hergebruikt het voor alle reranking operaties.

    Returns:
        SentenceTransformerRerank: Geconfigureerde reranker.
    """
    global _reranker
    if _reranker is None:
        _reranker = SentenceTransformerRerank(model="BAAI/bge-reranker-v2-m3", top_n=3)
    return _reranker


@observe(name="rerank")
def rerank_nodes(
    nodes: list[NodeWithScore], query: str, threshold: float = 0.5
) -> list[NodeWithScore]:
    """
    Herordent en filtert opgehaalde nodes op relevantie.

    Gebruikt een SentenceTransformer reranker om nodes te scoren
    en verwijdert resultaten onder een bepaalde drempel.

    Args:
        nodes (list[NodeWithScore]): Opgehaalde nodes uit retrieval.
        query (str): De gebruikersvraag.
        threshold (float): Minimum score om een node te behouden.

    Returns:
        list[NodeWithScore]: Gefilterde en gerankte nodes.
    """
    reranker = get_reranker()

    reranked = reranker.postprocess_nodes(
        nodes, query_bundle=QueryBundle(query_str=query)
    )

    reranked = [n for n in reranked if n.score is not None and n.score >= threshold]

    return reranked
