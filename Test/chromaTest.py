import chromadb

client = chromadb.Client()
collection = client.create_collection("test")

collection.add(
    documents=[
        "Kaltura is a video platform",
        "Proctorio monitort online examens",
        "Canvas is een LMS systeem"
    ],
    ids=["1", "2", "3"]
)

results = collection.query(
    query_texts=["Wat is proctorio?"],
    n_results=1
)

print(results)