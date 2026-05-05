import re
from utils.exceptions import AppValidationError
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from langfuse import observe
from utils.logging import get_logger
from typing import Mapping, Any

logger = get_logger(__name__)

_model = None


def get_model() -> SentenceTransformer:
    """
    Initialiseert en cachet het SentenceTransformer model.

    Het model wordt éénmalig geladen en hergebruikt
    voor alle relevantie checks

    Returns:
        SentenceTransformer: Geconfigureerd embedding model.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        )
    return _model


@observe(name="is_relevant")
def is_relevant(
    original_question: str, intake_data: Mapping[str, Any], threshold: float = 0.5
) -> bool:
    """
    Bepaalt of intake antwoorden relevant zijn t.o.v. de originele vraag.

    Combineert intake velden en vergelijkt deze semantisch
    met de oorspronkelijke vraag via embeddings en cosine similarity.

    Args:
        original_question (str): De oorspronkelijke gebruikersvraag.
        intake_data (dict[str, str]): Intake antwoorden (beschrijving, context, doel).
        threshold (float): Minimale similarity score om als relevant te gelden.

    Returns:
        bool: True indien relevant, anders False.
    """
    combined = f"""
    Probleem: {intake_data.get("beschrijving") or ""}
    Context: {intake_data.get("context") or ""}
    Doel: {intake_data.get("doel") or ""}
    """

    model = get_model()

    emb1 = model.encode([original_question])
    emb2 = model.encode([combined])

    score = cosine_similarity(emb1, emb2)[0][0]
    logger.info("similarity met originele vraag: %.3f", score)

    return score >= threshold


def validate_answer(key: str, answer: str) -> str:
    """
    Valideert en normaliseert een intake antwoord.

    - verwijdert HTML tags
    - trimt whitespace
    - controleert minimum/maximum lengte per veld

    Args:
        key (str): Intake veld (beschrijving, context, doel).
        answer (str): Ingevoerde waarde.

    Returns:
        str: Opgeschoond en gevalideerd antwoord.

    Raises:
        AppValidationError: Bij ongeldige input.
    """
    if not isinstance(answer, str):
        raise AppValidationError("Antwoord moet tekst zijn.")

    answer = answer.strip()

    answer = re.sub(r"<.*?>", "", answer)

    answer = answer.strip()

    if not answer:
        raise AppValidationError("Antwoord mag niet leeg zijn.")
    if key == "beschrijving":
        if len(answer) < 5:
            raise AppValidationError("Beschrijving is te kort.")
        if len(answer) > 80:
            raise AppValidationError("Beschrijving mag maximum 80 karakters bevatten.")

    elif key == "context":
        if len(answer) < 5:
            raise AppValidationError("Context is te kort.")
    elif key == "doel":
        if len(answer) < 5:
            raise AppValidationError("Doel is te kort.")

    return answer
