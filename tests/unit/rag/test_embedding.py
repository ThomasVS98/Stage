import pytest
import torch
import rag.embedding as embedding
from rag.embedding import get_embed_model
from unittest.mock import patch

@pytest.fixture(autouse=True)
def reset_embed_model():
    embedding._embed_model = None

def test_get_embed_model_creates_model_once():
    with patch("rag.embedding.HuggingFaceEmbedding") as mock_model:
        instance = mock_model.return_value
        
        model1 = get_embed_model()
        model2 = get_embed_model()

        assert model1 is instance
        assert model2 is instance

        mock_model.assert_called_once()

@patch("rag.embedding.HuggingFaceEmbedding")
def test_get_embed_model_returns_same_instance(_):
    model1 = get_embed_model()
    model2 = get_embed_model()

    assert model1 is model2

def test_get_embed_model_configuration():
    with patch("rag.embedding.HuggingFaceEmbedding") as mock_model:
        get_embed_model()

        _, kwargs = mock_model.call_args
       
        assert kwargs.get("model_name") == "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        assert kwargs.get("normalize")

        expected_device = "cuda" if torch.cuda.is_available() else "cpu"
        assert kwargs.get("device") == expected_device