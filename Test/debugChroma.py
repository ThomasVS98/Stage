import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_collection("docs")

results = collection.get(
    include=["documents","metadatas"],
    limit=5
)

documents = results["documents"]
metadatas = results["metadatas"]

for i in range(len(documents)):
    print("\n==============================")
    print("CHUNK", i+1)
    print("==============================")

    print("\nTekst:")
    print(documents[i][:500])

    print("\nMetadata:")
    print(metadatas[i])