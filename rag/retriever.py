from langfuse import observe

@observe(name="retrieve")
def retrieve_nodes(index, query:str):
    retriever = index.as_retriever(
        similarity_top_k = 25,
        # vector_store_query_mode="mmr",
        # mmr_threshold=0.3,
        filters = None
    )

    nodes = retriever.retrieve(query)
    return nodes