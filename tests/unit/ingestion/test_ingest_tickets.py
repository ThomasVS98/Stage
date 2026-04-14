import pytest
from unittest.mock import patch, MagicMock
from ingestion.ingest_tickets import (
    create_ticket_index,
    build_ticket_index,
    fetch_ticket_documents
)
from utils.exceptions import ExternalServiceError

@patch("ingestion.ingest_tickets.incidents_to_documents")
@patch("ingestion.ingest_tickets.fetch_topdesk_incidents")
def test_fetch_ticket_documents(mock_fetch, mock_transform):
    mock_fetch.return_value = ["incident1", "incident2"]
    mock_transform.return_value = ["doc1", "doc2", "doc3"]

    result = fetch_ticket_documents(limit=5)

    mock_fetch.assert_called_once_with(limit=5)
    mock_transform.assert_called_once_with(["incident1", "incident2"])
    assert result == ["doc1", "doc2", "doc3"]

@patch("ingestion.ingest_tickets.fetch_topdesk_incidents")
def test_fetch_ticket_documents_raises(mock_fetch):
    mock_fetch.side_effect = ExternalServiceError("fail")

    with pytest.raises(ExternalServiceError):
        fetch_ticket_documents()

@patch("ingestion.ingest_tickets.VectorStoreIndex")
@patch("ingestion.ingest_tickets.get_embed_model")
@patch("ingestion.ingest_tickets.SentenceSplitter")
@patch("ingestion.ingest_tickets.chromadb.PersistentClient")
def test_create_ticket_index_success(
    mock_chroma_client,
    mock_splitter,
    mock_embed,
    mock_index_class
):
    mock_collection = MagicMock()

    mock_client_instance = MagicMock()
    mock_client_instance.get_or_create_collection.return_value = mock_collection
    mock_chroma_client.return_value = mock_client_instance

    mock_index_instance = MagicMock()
    mock_index_class.return_value = mock_index_instance

    index, collection = create_ticket_index()

    mock_chroma_client.assert_called_once()
    mock_client_instance.delete_collection.assert_called_once()
    mock_client_instance.get_or_create_collection.assert_called_once()

    mock_index_class.assert_called_once()

    assert index == mock_index_instance
    assert collection == mock_collection

@patch("ingestion.ingest_tickets.VectorStoreIndex")
@patch("ingestion.ingest_tickets.get_embed_model")
@patch("ingestion.ingest_tickets.SentenceSplitter")
@patch("ingestion.ingest_tickets.chromadb.PersistentClient")
def test_create_ticket_index_delete_fails(
    mock_chroma_client,
    mock_splitter,
    mock_embed,
    mock_index_class,
):
    mock_collection = MagicMock()

    mock_client_instance = MagicMock()
    mock_client_instance.delete_collection.side_effect = Exception("fail")
    mock_client_instance.get_or_create_collection.return_value = mock_collection
    mock_chroma_client.return_value = mock_client_instance

    mock_index_class.return_value = MagicMock()

    index, collection = create_ticket_index()

    mock_client_instance.get_or_create_collection.assert_called_once()
    assert collection == mock_collection

@patch("ingestion.ingest_tickets.create_ticket_index")
@patch("ingestion.ingest_tickets.fetch_ticket_documents")
def test_build_ticket_index_success(
    mock_fetch,
    mock_create
):
    mock_docs = ["doc1", "doc2"]
    mock_fetch.return_value = mock_docs

    mock_index = MagicMock()
    mock_collection = MagicMock()
    mock_create.return_value = (mock_index, mock_collection)

    mock_splitter = type(
        "MockSplitter",
        (),
        {"get_nodes_from_documents": lambda self, docs: docs}
    )()

    patcher = patch("ingestion.ingest_tickets.SentenceSplitter", return_value=mock_splitter)
    patcher.start()

    result = build_ticket_index(limit=10)

    mock_fetch.assert_called_once_with(10)
    mock_create.assert_called_once()
    assert mock_index.insert_nodes.call_count == 1
    assert result[1] == 2


@patch("ingestion.ingest_tickets.create_ticket_index")
@patch("ingestion.ingest_tickets.fetch_ticket_documents")
def test_build_ticket_index_multiple_batches(
    mock_fetch,
    mock_create
):
    docs = list(range(120))
    mock_fetch.return_value = docs

    mock_index = MagicMock()
    mock_collection = MagicMock()
    mock_create.return_value = (mock_index, mock_collection)

    mock_splitter = type(
        "MockSplitter",
        (),
        {"get_nodes_from_documents": lambda self, docs: docs}
    )()

    patcher = patch("ingestion.ingest_tickets.SentenceSplitter", return_value=mock_splitter)
    patcher.start()

    _, count = build_ticket_index(limit=200)

    assert mock_index.insert_nodes.call_count == 3
    assert count == 120