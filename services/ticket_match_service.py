from rag.retriever import retrieve_nodes
from rag.reranker import rerank_nodes
from rag.ticket_index import get_ticket_index

SIMILARITY_THRESHOLD = 0.65

def find_similar_ticket(data:dict):
    query = f"""
    Probleem: {data.get("beschrijving")}
    Context: {data.get("context")}
    Doel: {data.get("doel")}
    """
    index = get_ticket_index()

    if index is None:
        print("Ticket index niet geladen")
        return None
    
    nodes = retrieve_nodes(index,query)
    nodes = rerank_nodes(nodes,query,threshold=0.40)
    
    if not nodes:
        return None
    best = nodes[0]
    print(f"[MATCH] Beste score: {best.score:.3f}")
    if best.score >= SIMILARITY_THRESHOLD:
        return {
            "score": float(best.score),
            "text": best.node.get_content()
        }
    return None
