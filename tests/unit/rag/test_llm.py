import pytest
import rag.llm as llm_module
from rag.llm import get_llm
from unittest.mock import patch

@pytest.fixture(autouse=True)
def reset_llm():
    llm_module._llm = None

def test_get_llm_created_instance_once():
    with patch("rag.llm.Ollama") as mock_ollama:
        instance = mock_ollama.return_value

        llm1 = get_llm()
        llm2 = get_llm()

        assert llm1 is instance
        assert llm2 is instance

        mock_ollama.assert_called_once()

@patch("rag.llm.Ollama")
def test_get_llm_returns_same_instance(_):
    llm1 = get_llm()
    llm2 = get_llm()

    assert llm1 is llm2

def test_get_llm_configuration():
    with patch("rag.llm.Ollama") as mock_ollama:
        get_llm()
       
        _, kwargs = mock_ollama.call_args

        assert kwargs.get("model") == "llama3.2:3b"
        assert kwargs.get("request_timeout") == 300
        assert kwargs.get("context_window") == 6140
        assert kwargs.get("temperature") == 0