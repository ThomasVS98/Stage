import pytest
from services.intake.validation import validate_answer, is_relevant
from utils.exceptions import AppValidationError
from unittest.mock import patch

#Tests voor validate_answer
def test_validate_beschrijving_te_kort():
    with pytest.raises(AppValidationError, match ="Beschrijving is te kort."):
        validate_answer("beschrijving", "abc")

def test_validate_beschrijving_min_boundary():
    assert validate_answer("beschrijving", "abcde") == "abcde"

def test_validate_beschrijving_max_boundary():
    text = "a" * 80
    assert validate_answer("beschrijving", text) == text

def test_validate_beschrijving_te_lang():
    lang_antwoord = "a" * 81
    with pytest.raises(AppValidationError, match="Beschrijving mag maximum 80 karakters bevatten."):
        validate_answer("beschrijving", lang_antwoord)

def test_validate_html_strip():
    result = validate_answer("beschrijving", "Help! <b>Mijn</b> laptop")
    assert result == "Help! Mijn laptop"

def test_validate_html_complex():
    result = validate_answer("beschrijving", "<b>test</b><script>x</script>")
    assert result == "testx"

def test_validate_leeg_na_strip():
    with pytest.raises(AppValidationError, match="Antwoord mag niet leeg zijn."):
        validate_answer("beschrijving", "   <b>   </b>  ")

def test_validate_context_te_kort():
    with pytest.raises(AppValidationError, match="Context is te kort."):
        validate_answer("context", "abc")

def test_validate_doel_te_kort():
    with pytest.raises(AppValidationError, match="Doel is te kort."):
        validate_answer("doel", "abc")

def test_validate_success_beschrijving():
    text = "Mijn scherm flikkert continu"
    assert validate_answer("beschrijving", text) == text

def test_validate_success_context():
    text = "Dit gebeurt sinds gisteren, ik heb verder niks veranderd aan mijn laptop."
    assert validate_answer("context", text) == text

def test_validate_success_doel():
    text = "Ik wil mijn laptop laten repareren."
    assert validate_answer("doel", text) == text

def test_validate_unknown_key():
    text = "vrije tekst"
    assert validate_answer("onbekende_key", text) == text

def test_validate_non_string_input():
    with pytest.raises(AppValidationError, match="Antwoord moet tekst zijn."):
        validate_answer("beschrijving", None)

def test_validate_integer_input():
    with pytest.raises(AppValidationError, match="Antwoord moet tekst zijn."):
        validate_answer("beschrijving", 123)

# Tests voor is_relevant (met mocking van embedding model)
@patch('services.intake.validation.model.encode')
@patch('services.intake.validation.cosine_similarity')
def test_is_relevant_true(mock_cosine, mock_encode):
    mock_cosine.return_value = [[0.8]]

    data = {
        "beschrijving": "Laptop stuk",
        "context": "Op kantoor",
        "doel": "Reparatie"
    }
    assert is_relevant("Mijn laptop is kapot", data, threshold=0.5) is True

@patch('services.intake.validation.model.encode')
@patch('services.intake.validation.cosine_similarity')
def test_is_relevant_false(mock_cosine, mock_encode):
    mock_cosine.return_value = [[0.3]]

    data = {
        "beschrijving": "Laptop stuk",
        "context": "Op kantoor",
        "doel": "Reparatie"
    }
    assert is_relevant("Is het goed weer vandaag?", data, threshold=0.5) is False

@patch('services.intake.validation.model.encode')
@patch('services.intake.validation.cosine_similarity')
def test_is_relevant_calls_encode_correctly(mock_cosine, mock_encode):
    mock_cosine.return_value = [[1.0]]
    data = {"beschrijving": "Laptop stuk", "context": "Op kantoor", "doel": "Reparatie"}
    is_relevant("Mijn laptop is kapot", data)
    
    assert mock_encode.call_count == 2
    args, _ = mock_encode.call_args_list[1]
    combined_arg = args[0][0]
    assert "Probleem: Laptop stuk" in combined_arg
    assert "Context: Op kantoor" in combined_arg
    assert "Doel: Reparatie" in combined_arg