import torch
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from utils.logging import get_logger

logger = get_logger(__name__)

_embed_model = None

def get_embed_model():
    global _embed_model
    if _embed_model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"Embedding draait op: {device}")

        _embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            normalize=True,
            device=device
        )
    return _embed_model