from unittest.mock import MagicMock
from rag.prompts import (
    extract_json,
    is_valid_query,
    detect_intent_prompt,
    answer_system_prompt,
    answer_user_prompt,
    detect_intent,
    generate_answer,
    parse_llm_json,
    judge_answer
)

def test_extracts_json_basic():
    text = 'some text {"intent": "SUPPORT"} more text'

    result = extract_json(text)

    assert result == '{"intent": "SUPPORT"}'

def test_extract_json_no_match():
    text = "geen json hier"

    result = extract_json(text)

    assert result is None

def test_is_valid_query_true():
    assert is_valid_query("reset password") is True

def test_is_valid_query_too_short():
    assert is_valid_query("ab") is False

def test_is_valid_query_no_letters():
    assert is_valid_query("12345") is False

def test_is_valid_query_mixed():
    assert is_valid_query("?? abc !!") is True

def test_detect_intent_prompt_contains_query():
    query = "Hoe reset ik mijn wachtwoord?"

    prompt = detect_intent_prompt(query)

    assert query in prompt

def test_detect_intent_prompt_contains_intents():
    prompt = detect_intent_prompt("test")

    assert "SUPPORT" in prompt
    assert "ALGEMEEN" in prompt
    assert "IRRELEVANT" in prompt

def test_detect_intent_prompt_contains_json_instruction():
    prompt = detect_intent_prompt("test")

    assert '{"intent": "SUPPORT"}' in prompt

def test_detect_intent_json_response():
    mock_llm = MagicMock()
    mock_llm.complete.return_value.text = '{"intent": "SUPPORT"}'

    result = detect_intent(mock_llm, "Hoe reset ik mijn wachtwoord?")

    assert result == "SUPPORT"

def test_detect_intent_raw_fallback():
    mock_llm = MagicMock()
    mock_llm.complete.return_value.text = "SUPPORT"

    result = detect_intent(mock_llm, "Hoe reset ik mijn wachtwoord?")

    assert result == "SUPPORT"

def test_detect_intent_invalid_query():
    mock_llm = MagicMock()

    result = detect_intent(mock_llm, "??")

    assert result == "IRRELEVANT"

def test_detect_intent_invalid_json_value():
    mock_llm = MagicMock()
    mock_llm.complete.return_value.text = '{"intent": "UNKNOWN}'

    result = detect_intent(mock_llm, "Hoe reset ik mijn wachtwoord?")

    assert result == "ONBEKEND"

def test_detect_intent_unparsable():
    mock_llm = MagicMock()
    mock_llm.complete.return_value.text = "random text"

    result = detect_intent(mock_llm, "Hoe reset ik mijn wachtwoord?")

    assert result == "ONBEKEND"

def test_generate_answer_calls_llm():
    mock_llm = MagicMock()
    
    mock_response = MagicMock()
    mock_response.message.content = "response"

    mock_llm.chat.return_value = mock_response

    result = generate_answer(mock_llm, "context", "query")

    assert result == "response"
    mock_llm.chat.assert_called_once()

def test_answer_system_prompt_contains_guidelines():
    prompt = answer_system_prompt()

    assert "Antwoord uitsluitend op basis van de onderstaande context" in prompt

def test_answer_user_prompt_structure():
    prompt = answer_user_prompt("ctx", "vraag")

    assert "Context:" in prompt
    assert "Vraag:" in prompt

def test_parse_llm_json_valid():
    raw = '{"faithfulness": 2}'
    result = parse_llm_json(raw, {})

    assert result["faithfulness"] == 2

def test_parse_llm_json_fallback():
    raw = "invalid"

    fallback = {"x": 1}
    result = parse_llm_json(raw, fallback)

    assert result == fallback

def test_judge_answer_parses_json():
    mock_llm = MagicMock()

    mock_response = MagicMock()
    mock_response.message.content = '{"faithfulness": 2}'
    mock_llm.chat.return_value = mock_response

    result = judge_answer(mock_llm, "context", "query", "answer")

    assert result["faithfulness"] == 2




