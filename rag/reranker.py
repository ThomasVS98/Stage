from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core import QueryBundle

_reranker = None

def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = SentenceTransformerRerank(
            model="BAAI/bge-reranker-v2-m3",
            top_n=5
        )
    return _reranker

def rerank_nodes(nodes,query:str,threshold: float = 0.50):
    reranker = get_reranker()
    
    reranked = reranker.postprocess_nodes(
        nodes,
        query_bundle=QueryBundle(query_str=query)
    )

    reranked = [
        n for n in reranked
        if n.score is not None and n.score >= threshold
    ]

    return reranked