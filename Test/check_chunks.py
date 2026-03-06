import chromadb

def check_database_content():
    client = chromadb.PersistentClient(path="./chroma_db")
    
    collection = client.get_collection("docs")
    
    results = collection.get(limit=5)
    
    print("\n--- DATABASE CHUNK CONTROLE ---")
    for i in range(len(results['ids'])):
        content = results['documents'][i]
        metadata = results['metadatas'][i]
        
        print(f"\n[Chunk {i+1}]")
        print(f"Bronbestand: {metadata.get('source_file')}")
        print(f"Metadata Titel: {metadata.get('title')}")
        print(f"Eerste 150 karakters tekst:\n{content[:150]}...")
        print("-" * 30)

if __name__ == "__main__":
    check_database_content()