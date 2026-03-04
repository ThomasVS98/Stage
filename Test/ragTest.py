import chromadb
from sentence_transformers import SentenceTransformer
from llama_index.llms.ollama import Ollama

#LLM
llm = Ollama(model="llama3.2:3b",
                request_timeout=120,
                context_window=4096)

#embedding model
embedding_model = SentenceTransformer(
    'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
    )

#ChromaDB
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name = "test",
    metadata={"hnsw:space": "cosine"}
)

if collection.count() == 0:
    docs = [
        "Kaltura is een videoplatform voor onderwijs.",
        "Proctorio monitort online examens via webcam.",
        "Canvas is een learning management system."
    ]

    embeddings = embedding_model.encode(docs).tolist()

    collection.add(
        documents=docs,
        embeddings=embeddings,
        ids=["1", "2", "3"]
    )

    print("Test documenten toegevoegd.")
    print("Docs in database:", collection.count())

# Query
query1 = "Wat doet proctorio?"
query2 = "Wat is Microsoft Teams?"

queries = [
    "Wat doet Proctorio?",
    "Wat is Kaltura?",
    "Wat is Canvas?",
    "Wat is Microsoft Teams?"
]

def judge_answer(query, context, answer):
    judge_prompt = f"""
        Je bent een evaluator voor een RAG systeem.

        Controleer of het antwoord volledig gebaseerd is op de gegeven context.

        Vraag:
        {query}

        Context:
        {context}

        Antwoord:
        {answer}

        Antwoord enkel met één woord:

        PASS  → antwoord is correct gebaseerd op de context
        FAIL  → antwoord bevat informatie die niet in de context staat
        """
 
    result = llm.complete(judge_prompt)

    return result.text

for query in queries:
    query_embedding = embedding_model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=2
    )

    print(results["documents"])
    print(results["distances"])

    best_distance = results["distances"][0][0]

    # if best_distance > 0.75:
    #     print("Er is onvoldoende informatie beschikbaar.")
    #     exit()

    docs = results["documents"][0]

    #Context
    context = "\n".join(docs)

    prompt = f"""
    Gebruik enkel de onderstaande context om de vraag te beantwoorden.
    Als de context onvoldoende informatie bevat, zeg:
    "Er is onvoldoende informatie beschikbaar."

    Context:
    {context}

    Vraag:
    {query}
    """

    #LLM response
    response =  llm.complete(prompt)

    answer = response.text

    judge_result = judge_answer(query, context, answer)

    #Output
    print("\n Query")
    for doc, dist in zip(results["documents"][0],results["distances"][0]):
        print(f"Document: {doc} - Distance: {dist}")

    print("\n LLM Response")
    print(response.text)

    print("Judge:", judge_result)

