import json
from utils.config_loader import resolve_env, load_source_config, save_source_config
from unittest.mock import patch, mock_open


def test_resolve_env(monkeypatch):
    class FakeSettings:
        MY_KEY_ID = "real_value"

    monkeypatch.setattr("utils.config_loader.settings", FakeSettings)

    config = {"key": "MY_KEY_ID"}

    result = resolve_env(config)

    assert result["key"] == "real_value"


def test_resolve_env_no_match(monkeypatch):
    class FakeSettings:
        pass

    monkeypatch.setattr("utils.config_loader.settings", FakeSettings)

    config = {"key": "MY_KEY_ID"}

    result = resolve_env(config)

    assert result["key"] == "MY_KEY_ID"


def test_resolve_env_no_id_suffix():
    config = {"a": "normal_value", "b": 123, "c": True}

    result = resolve_env(config)

    assert result == config


def test_load_source_config_basic(monkeypatch):

    fake_data = [{"type": "topdesk", "config": {}}]

    m = mock_open(read_data=json.dumps(fake_data))

    with patch("utils.config_loader.open", m):
        result = load_source_config(resolve=False)

    assert len(result) == 1
    assert result[0]["type"] == "topdesk"


def test_load_source_config_adds_id(monkeypatch):
    fake_data = [{"type": "topdesk", "config": {}}]

    m = mock_open(read_data=json.dumps(fake_data))

    monkeypatch.setattr("utils.config_loader.uuid.uuid4", lambda: "fixed_id")

    with patch("utils.config_loader.open", m):
        result = load_source_config(resolve=False)

    assert result[0]["id"] == "fixed_id"


def test_load_source_config_resolve(monkeypatch):
    fake_data = [{"id": "1", "type": "topdesk", "config": {"key": "VALUE_ID"}}]

    m = mock_open(read_data=json.dumps(fake_data))

    monkeypatch.setattr(
        "utils.config_loader.resolve_env", lambda cfg: {"key": "resolved"}
    )

    with patch("utils.config_loader.open", m):
        result = load_source_config(resolve=True)

    assert result[0]["config"]["key"] == "resolved"


def test_load_source_config_exception():
    with patch("utils.config_loader.open", side_effect=Exception("fail")):
        result = load_source_config()

    assert result == []


def test_save_source_config_exception():
    with patch("utils.config_loader.open", side_effect=Exception("fail")):
        save_source_config([{"a": 1}])
