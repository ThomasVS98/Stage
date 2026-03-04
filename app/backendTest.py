from fastapi import FastAPI
import chromadb
from sentence_transformers import SentenceTransformer
from llama_index.llms.ollama import Ollama

app = FastAPI()

# LLM
llm = Ollama(
    model="llama3.2:3b",
    request_timeout=120,
    context_window=4096
)

# Embedding model
embedding_model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
)

# Chroma
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="test",
    metadata={"hnsw:space": "cosine"}
)


@app.get("/chat")
def ask(query: str):

    query_embedding = embedding_model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=2
    )

    best_distance = results["distances"][0][0]

    if best_distance > 0.75:
        return {"answer": "Er is onvoldoende informatie beschikbaar."}

    docs = results["documents"][0]

    context = "\n".join(docs)

    prompt = f"""
Gebruik enkel de onderstaande context om de vraag te beantwoorden.

Context:
{context}

Vraag:
{query}
"""

    response = llm.complete(prompt)

    return {"answer": response.text}

# test 1 met: http://127.0.0.1:8000/chat?query=Wat%20doet%20Proctorio
# test 2 met: http://127.0.0.1:8000/chat?query=Wat%20is%20Microsoft%20Teams