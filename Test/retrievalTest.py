import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
client = chromadb.Client(
    chromadb.config.Settings(
        persist_directory="./chroma_db"
    )
)
collection = client.create_collection(
    name = "test",
    metadata={"hnsw:space": "cosine"})
docs = [
    "Kaltura is een videoplatform voor onderwijs.",
    "Proctorio monitort online examens via webcam.",
    "Canvas is een learning management system."
]

embeddings = model.encode(docs).tolist()

collection.add(
    documents = docs,
    embeddings = embeddings,
    ids = ["1", "2", "3"]
)

query = "Wat doet Proctorio?"
query_embedding = model.encode([query]).tolist()
results = collection.query(
    query_embeddings=query_embedding,
    n_results=2
)

print(collection.metadata)
print("Query:", query)
print("Results:")
print(results["documents"])
print("Distances:", results["distances"])