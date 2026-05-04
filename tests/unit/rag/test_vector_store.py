import pytest
from unittest.mock import patch, MagicMock
from rag.vector_store import (
    load_collection_index,
    get_index,
    reload_index
)
import rag.vector_store as vs

@pytest.fixture(autouse=True)
def reset_cache():
    vs.cache.clear()

@patch("rag.vector_store.get_embed_model")
@patch("rag.vector_store.VectorStoreIndex.from_vector_store")
@patch("rag.vector_store.ChromaVectorStore")
@patch("rag.vector_store.chromadb.PersistentClient")
def test_load_collection_index_success(
    mock_client_cls,
    mock_vector_cls,
    mock_index_cls,
    mock_embed
):
    mock_client = MagicMock()
    mock_collection = MagicMock()

    mock_client_cls.return_value = mock_client
    mock_client.get_collection.return_value = mock_collection
    mock_collection.count.return_value = 10

    mock_vector_store = MagicMock()
    mock_vector_cls.return_value = mock_vector_store

    mock_index = MagicMock()
    mock_index_cls.return_value = mock_index

    mock_embed.return_value = "embed_model"

    result = load_collection_index("docs")

    assert result == mock_index
    mock_embed.assert_called_once()

@patch("rag.vector_store.chromadb.PersistentClient")
def test_load_collection_index_no_collection(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    mock_client.get_collection.side_effect = Exception("Collection not found")

    result = load_collection_index("docs")

    assert result is None

@patch("rag.vector_store.load_collection_index")
def test_get_index_caches_result(mock_load):
    mock_load.return_value = "index"

    result1 = get_index("docs")
    result2 = get_index("docs")

    assert result1 == "index"
    assert result2 == "index"

    mock_load.assert_called_once_with("docs")

@patch("rag.vector_store.load_collection_index")
def test_reload_index_updates_cache(mock_load):
    mock_load.return_value = "new_index"

    reload_index("docs")

    from rag.vector_store import cache
    assert cache["docs"] == "new_index"

@patch("rag.vector_store.load_collection_index")
def test_get_index_reload_if_none(mock_load):
    from rag.vector_store import cache

    cache["docs"] = None
    mock_load.return_value = "index"

    result = get_index("docs")

    assert result == "index"


