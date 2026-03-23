from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core import QueryBundle

reranker = SentenceTransformerRerank(
    model="BAAI/bge-reranker-v2-m3",
    top_n=5
)

# reranker = SentenceTransformerRerank(
#     model="cross-encoder/ms-marco-MiniLM-L12-v2",
#     top_n=6
# )

def rerank_nodes(nodes,query:str):
    reranked = reranker.postprocess_nodes(
        nodes,
        query_bundle=QueryBundle(query_str=query)
    )

    reranked = [
        n for n in reranked
        if n.score is not None and n.score >= 0.30
    ]

    return reranked