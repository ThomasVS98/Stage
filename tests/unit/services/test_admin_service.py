import pytest
from services.admin_service import (
    get_folder_size,
    run_full_ingestion,
    process_sources,
    validate_source 
)
from unittest.mock import patch
from utils.exceptions import SourceConfigError, ExternalServiceError, IngestionError

def test_get_folder_size(monkeypatch):
    files = [
        ("/dir", [], ["a.text", "b.text"]), 
    ]

    monkeypatch.setattr("services.admin_service.os.walk", lambda path: files)
    monkeypatch.setattr("services.admin_service.os.path.getsize", lambda path: 1024 * 1024)

    size = get_folder_size("dummy")

    assert size == 2

def test_validate_source_valid(monkeypatch):
    class FakeSource:
        def __init__(self):
            self.id = "1"
            self.type = "topdesk"
            self.enabled = True
            self.config = {
                "include_kb": True,
                "incident_limit": 100
            }

    monkeypatch.setattr(
        "services.admin_service.get_schema",
        lambda _: {
            "include_kb": {"type": "bool", "default": True},
            "incident_limit": {"type": "int", "default": 200}
        }
    )

    result = validate_source(FakeSource())

    assert result["config"]["include_kb"] is True
    assert result["config"]["incident_limit"] == 100

def test_validate_source_unknown_field(monkeypatch):
    class FakeSource:
        def __init__(self):
            self.id = "1"
            self.type = "topdesk"
            self.enabled = True
            self.config = {
                "unknown_field": "value"
            }

    monkeypatch.setattr(
        "services.admin_service.get_schema",
        lambda _: {
            "include_kb": {"type": "bool", "default": True}
        }
    )

    with pytest.raises(SourceConfigError, match="Onbekend veld"):
        validate_source(FakeSource())

def test_validate_source_required_field(monkeypatch):
    class FakeSource:
        def __init__(self):
            self.id = "1"
            self.type = "topdesk"
            self.enabled = True
            self.config = {
                "include_kb": None
            }
    monkeypatch.setattr(
        "services.admin_service.get_schema",
        lambda _: {
            "include_kb": {"type": "bool", "required": True}
        }
    )

    with pytest.raises(SourceConfigError, match="is verplicht"):
        validate_source(FakeSource())

def test_validate_source_bool_parsing(monkeypatch):
    class FakeSource:
        def __init__(self, value):
            self.id = "1"
            self.type = "topdesk"
            self.enabled = True
            self.config = {
                "include_kb": value
            }

    monkeypatch.setattr(
        "services.admin_service.get_schema",
        lambda _: {
            "include_kb": {"type": "bool", "default": True}
        }
    )

    assert validate_source(FakeSource("true"))["config"]["include_kb"] is True
    assert validate_source(FakeSource("1"))["config"]["include_kb"] is True
    assert validate_source(FakeSource("yes"))["config"]["include_kb"] is True

    assert validate_source(FakeSource("false"))["config"]["include_kb"] is False
    assert validate_source(FakeSource("0"))["config"]["include_kb"] is False
    assert validate_source(FakeSource("no"))["config"]["include_kb"] is False

def test_validate_source_invalid_bool(monkeypatch):
    from utils.exceptions import SourceConfigError

    class FakeSource:
        def __init__(self):
            self.id = "1"
            self.type = "topdesk"
            self.enabled = True
            self.config = {
                "include_kb": "notabool"
            }

    monkeypatch.setattr(
        "services.admin_service.get_schema",
        lambda _: {
            "include_kb": {"type": "bool", "default": True}
        }
    )

    with pytest.raises(SourceConfigError, match="type bool"):
        validate_source(FakeSource())

def test_process_sources_adds_id(monkeypatch):
    class FakeSource:
        def __init__(self):
            self.id = None
            self.type = "topdesk"
            self.enabled = True
            self.config = {}

    monkeypatch.setattr(
        "services.admin_service.validate_source",
        lambda src: {
            "id": src.id,
            "type": src.type,
            "enabled": src.enabled,
            "config": {}
        }
    )

    result = process_sources([FakeSource()])

    assert result[0]["id"] is not None

@patch("services.admin_service.reload_index")
@patch("services.admin_service.cleanup_temp_files")
@patch("services.admin_service.build_ticket_index")
@patch("services.admin_service.build_index")
@patch("services.admin_service.load_all_data")
@patch("services.admin_service.load_source_config")
@patch("services.admin_service.get_folder_size", return_value=10)
def test_run_full_ingestion_success(
    mock_size,
    mock_sources,
    mock_load,
    mock_build,
    mock_ticket,
    mock_cleanup,
    mock_reload
):
    mock_load.return_value = ["doc1", "doc2"]
    mock_build.return_value = 2
    mock_sources.return_value = [
        {"type": "topdesk", "enabled": True, "config": {"incident_limit": 50}}
    ]
    mock_ticket.return_value = ("index", 5)

    result = run_full_ingestion()

    assert result["docs_indexed"] == 2
    assert result["tickets_indexed"] == 5

    mock_build.assert_called_once()
    mock_ticket.assert_called_once_with(limit=50)
    assert mock_reload.call_count == 2

@patch("services.admin_service.load_all_data")
def test_run_full_ingestion_external_error(mock_load):

    mock_load.side_effect = ExternalServiceError("fail")

    with pytest.raises(IngestionError, match="fail"):
        run_full_ingestion()

@patch("services.admin_service.reload_index")
@patch("services.admin_service.cleanup_temp_files")
@patch("services.admin_service.build_ticket_index", return_value=("idx", 0))
@patch("services.admin_service.build_index", return_value=0)
@patch("services.admin_service.load_all_data", return_value=[])
@patch("services.admin_service.load_source_config", return_value=[])
@patch("services.admin_service.get_folder_size", return_value=0)
def test_run_full_ingestion_no_docs(
    *_,
):
    result = run_full_ingestion()

    assert result["docs_indexed"] == 0

@patch("services.admin_service.load_all_data")
def test_run_full_ingestion_ingestion_error_passthrough(mock_load):

    mock_load.side_effect = IngestionError("fail")

    with pytest.raises(IngestionError):
        run_full_ingestion()

def test_validate_source_invalid_int(monkeypatch):
    from utils.exceptions import SourceConfigError

    class FakeSource:
        def __init__(self):
            self.id = "1"
            self.type = "topdesk"
            self.enabled = True
            self.config = {"limit": "notanint"}

    monkeypatch.setattr(
        "services.admin_service.get_schema",
        lambda _: {
            "limit": {"type": "int"}
        }
    )

    with pytest.raises(SourceConfigError):
        validate_source(FakeSource())

def test_validate_source_string_cast(monkeypatch):
    class FakeSource:
        def __init__(self):
            self.id = "1"
            self.type = "topdesk"
            self.enabled = True
            self.config = {"name": 123}

    monkeypatch.setattr(
        "services.admin_service.get_schema",
        lambda _: {
            "name": {"type": "str"}
        }
    )

    result = validate_source(FakeSource())

    assert result["config"]["name"] == "123"

def test_validate_source_unknown_type(monkeypatch):
    from utils.exceptions import SourceConfigError

    class FakeSource:
        def __init__(self):
            self.id = "1"
            self.type = "unknown"
            self.enabled = True
            self.config = {}

    monkeypatch.setattr(
        "services.admin_service.get_schema",
        lambda _: None
    )

    with pytest.raises(SourceConfigError, match="Onbekend bron type"):
        validate_source(FakeSource())

@patch("services.admin_service.load_all_data")
def test_run_full_ingestion_generic_exception(mock_load):

    mock_load.side_effect = Exception("boom")

    with pytest.raises(IngestionError, match="boom"):
        run_full_ingestion()

def test_validate_source_default_value(monkeypatch):
    class FakeSource:
        def __init__(self):
            self.id = "1"
            self.type = "topdesk"
            self.enabled = True
            self.config = {
                "include_kb": None
            }

    monkeypatch.setattr(
        "services.admin_service.get_schema",
        lambda _: {
            "include_kb": {"type": "bool", "default": True}
        }
    )

    result = validate_source(FakeSource())

    assert result["config"]["include_kb"] is True

def test_validate_source_bool_fallback(monkeypatch):
    class FakeSource:
        def __init__(self):
            self.id = "1"
            self.type = "topdesk"
            self.enabled = True
            self.config = {
                "include_kb": 123  # geen bool, geen string → fallback
            }

    monkeypatch.setattr(
        "services.admin_service.get_schema",
        lambda _: {
            "include_kb": {"type": "bool"}
        }
    )

    result = validate_source(FakeSource())

    assert result["config"]["include_kb"] is True

