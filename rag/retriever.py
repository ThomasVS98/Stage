from langfuse import observe
from llama_index.core.schema import NodeWithScore
from llama_index.core import VectorStoreIndex


@observe(name="retrieve")
def retrieve_nodes(index: VectorStoreIndex, query: str) -> list[NodeWithScore]:
    """
    Haalt relevante nodes op uit de vector index op basis van een query.

    Gebruikt similarity search om de meest relevante documenten te selecteren.

    Args:
        index (VectorStoreIndex): De vector index.
        query (str): De gebruikersvraag.

    Returns:
        list[NodeWithScore]: Lijst van opgehaalde nodes met relevantiescore.
    """
    retriever = index.as_retriever(
        similarity_top_k=25,
        filters=None,
    )

    nodes = retriever.retrieve(query)
    return nodes
