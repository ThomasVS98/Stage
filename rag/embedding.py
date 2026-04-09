from llama_index.embeddings.huggingface import HuggingFaceEmbedding

_embed_model = None

def get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            normalize=True
        )
    return _embed_model