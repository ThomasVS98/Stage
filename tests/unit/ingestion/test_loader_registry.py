import pytest
import ingestion.loader_registry as registry

@pytest.fixture(autouse=True)
def clear_registry():
    registry.LOADERS.clear()
    registry.SCHEMAS.clear()

def test_register_loader():
    from ingestion.loader_registry import register_loader, get_loader

    @register_loader("test")
    def dummy():
        return "ok"
    
    loader = get_loader("test")

    assert loader is not None
    assert loader() == "ok"

def test_get_available_loaders():
    from ingestion.loader_registry import register_loader, get_available_loaders

    @register_loader("test2")
    def dummy():
        pass

    loaders = get_available_loaders()

    assert "test2" in loaders

def test_register_loader_with_schema():
    from ingestion.loader_registry import register_loader, get_schema

    schema = {"field": "value"}

    @register_loader("test3", schema=schema)
    def dummy():
        pass

    result = get_schema("test3")

    assert result == schema

def test_get_loader_not_found():
    from ingestion.loader_registry import get_loader
    assert get_loader("non_existent") is None

def test_get_schema_empty_default():
    from ingestion.loader_registry import register_loader, get_schema

    @register_loader("no_schema")
    def dummy():
        pass

    assert get_schema("no_schema") == {}
    assert get_schema("completely_unknown") == {}