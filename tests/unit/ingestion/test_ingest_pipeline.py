import pytest
from ingestion.ingest_pipeline import (
    load_all_data, 
    build_index,
    cleanup_temp_files
    )
from utils.exceptions import ExternalServiceError

class Doc:
    def __init__(self, metadata=None):
        self.metadata = metadata or {}
        self.doc_id = None

def test_load_all_data_no_sources(monkeypatch):
    monkeypatch.setattr(
        "ingestion.ingest_pipeline.load_source_config",
        lambda: []
    )

    result = list(load_all_data())

    assert result == []

def test_load_all_data_skips_disabled_source(monkeypatch):
    monkeypatch.setattr(
        "ingestion.ingest_pipeline.load_source_config",
        lambda: [
            {"type": "sharepoint", "enabled": False, "config": {}}
        ]
    )

    called = []

    def fake_loader(config):
        called.append(True)
        return []
    
    monkeypatch.setattr(
        "ingestion.ingest_pipeline.get_loader",
        lambda _: fake_loader
    )

    result = list(load_all_data())

    assert result == []
    assert not called

def test_load_all_data_calls_loader(monkeypatch):
    monkeypatch.setattr(
        "ingestion.ingest_pipeline.load_source_config",
        lambda: [
            {"type": "sharepoint", "enabled": True, "config": {"a": "1"}}
        ]
    )

    def fake_loader(config):
        assert config == {"a": "1"}
        yield "doc1"
        yield "doc2"

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.get_loader",
        lambda _: fake_loader
    )

    result = list(load_all_data())

    assert result == ["doc1", "doc2"]

def test_load_all_data_no_loader(monkeypatch):
    monkeypatch.setattr(
        "ingestion.ingest_pipeline.load_source_config",
        lambda: [
            {"type": "unknown", "enabled": True, "config": {}}
        ]
    )

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.get_loader",
        lambda _: None
    )

    result = list(load_all_data())

    assert result == []

def test_load_all_data_raises_external_service_error(monkeypatch):
    monkeypatch.setattr(
        "ingestion.ingest_pipeline.load_source_config",
        lambda: [
            {"type": "test", "enabled": True, "config": {}}
        ]
    )

    def failing_loader(config):
        raise ExternalServiceError("fail")

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.get_loader",
        lambda _: failing_loader
    )

    with pytest.raises(ExternalServiceError, match="fail"):
        list(load_all_data())

def test_load_all_data_handles_generic_exception(monkeypatch):
    monkeypatch.setattr(
        "ingestion.ingest_pipeline.load_source_config",
        lambda: [
            {"type": "test", "enabled": True, "config": {}}
        ]
    )

    def failing_loader(config):
        raise Exception("boom")

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.get_loader",
        lambda _: failing_loader
    )

    result = list(load_all_data())

    assert result == []

def test_build_index_inserts_documents(monkeypatch):
    docs = [Doc(), Doc()]     
    inserted = []

    class MockIndex:
        def insert_nodes(self, nodes):
            inserted.extend(nodes)

    mock_collection = type("Collection", (), {"count": lambda self: 2})()

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.create_index",
        lambda: (MockIndex(), mock_collection)
    )

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.SentenceSplitter",
        lambda *args, **kwargs: type(
            "MockSplitter",
            (),
            {"get_nodes_from_documents": lambda self, docs: docs}
        )()
    )

    count = build_index(iter(docs))

    assert count == 2
    assert len(inserted) == 2

def test_build_index_sets_doc_id(monkeypatch):
    doc = Doc(metadata={"source_id": "123"})

    class MockIndex:
        def insert_nodes(self, nodes):
            pass

    mock_collection = type("Collection", (), {"count": lambda self: 1})()

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.create_index",
        lambda: (MockIndex(), mock_collection)
    )

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.SentenceSplitter",
        lambda *args, **kwargs: type(
            "MockSplitter",
            (),
            {"get_nodes_from_documents": lambda self, docs: docs}
        )()
    )

    build_index(iter([doc]))

    assert doc.doc_id == "123"

def test_build_index_handles_missing_collection(monkeypatch):
    class MockIndex:
        def insert(self, d):
            pass

    mock_collection = type("Collection", (), {"count": lambda self: 0})()

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.create_index",
        lambda: (MockIndex(), mock_collection)
    )

    count = build_index(iter([]))

    assert count == 0

def test_build_index_triggers_gc(monkeypatch):
    docs = [Doc() for _ in range(40)]

    gc_calls = []

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.gc.collect",
        lambda: gc_calls.append(True)
    )

    class MockIndex:
        def insert_nodes(self, nodes): pass

    mock_collection = type("Collection", (), {"count": lambda self: 40})()

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.create_index",
        lambda: (MockIndex(), mock_collection)
    )

    monkeypatch.setattr(
    "ingestion.ingest_pipeline.SentenceSplitter",
    lambda *args, **kwargs: type(
        "MockSplitter",
        (),
        {"get_nodes_from_documents": lambda self, docs: docs}
        )()
    )

    build_index(iter(docs))

    assert len(gc_calls) == 2

def test_build_index_no_gc_below_threshold(monkeypatch):
    docs = [Doc() for _ in range(19)]

    gc_calls = []

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.gc.collect",
        lambda: gc_calls.append(True)
    )

    class MockIndex:
        def insert_nodes(self, nodes): pass

    mock_collection = type("Collection", (), {"count": lambda self: 19})()

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.create_index",
        lambda: (MockIndex(), mock_collection)
    )

    monkeypatch.setattr(
    "ingestion.ingest_pipeline.SentenceSplitter",
    lambda *args, **kwargs: type(
        "MockSplitter",
        (),
        {"get_nodes_from_documents": lambda self, docs: docs}
        )()
    )


    build_index(iter(docs))

    assert len(gc_calls) == 0

def test_cleanup_temp_files_removes_existing_dirs(monkeypatch):
    removed = []

    def fake_exists(path):
        return True
    
    def fake_rmtree(path):
        removed.append(path)
    
    monkeypatch.setattr(
        "ingestion.ingest_pipeline.os.path.exists",
        fake_exists
    )

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.shutil.rmtree",
        fake_rmtree
    )

    cleanup_temp_files()
    
    assert removed == ["./temp_sharepoint", "./temp_onedrive"]

def test_cleanup_temp_files_skips_missing_dirs(monkeypatch):
    monkeypatch.setattr(
        "ingestion.ingest_pipeline.os.path.exists",
        lambda path: False
    )

    removed = []

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.shutil.rmtree",
        lambda path: removed.append(path)
    )

    cleanup_temp_files()

    assert removed == []

def test_process_documents_batches(monkeypatch):
    from ingestion.ingest_pipeline import process_documents

    docs = [Doc() for _ in range(25)]
    inserted = []

    class MockIndex:
        def insert_nodes(self, nodes):
            inserted.extend(nodes)

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.SentenceSplitter",
        lambda *args, **kwargs: type(
            "MockSplitter",
            (),
            {"get_nodes_from_documents": lambda self, docs: docs}
        )()
    )

    count = process_documents(MockIndex(), iter(docs))

    assert count == 25
    assert len(inserted) == 25

def test_process_documents_only_small_batch(monkeypatch):
    from ingestion.ingest_pipeline import process_documents

    docs = [Doc() for _ in range(5)]
    inserted = []

    class MockIndex:
        def insert_nodes(self, nodes):
            inserted.extend(nodes)

    monkeypatch.setattr(
        "ingestion.ingest_pipeline.SentenceSplitter",
        lambda *args, **kwargs: type(
            "MockSplitter",
            (),
            {"get_nodes_from_documents": lambda self, docs: docs}
        )()
    )

    count = process_documents(MockIndex(), iter(docs))

    assert count == 5
    assert len(inserted) == 5
