import re
from utils.exceptions import AppValidationError
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from utils.logging import get_logger

logger = get_logger(__name__)

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")

def is_relevant(original_question:str, intake_data:dict, threshold: float = 0.5):
    combined = f"""
    Probleem: {intake_data.get("beschrijving")}
    Context: {intake_data.get("context")}
    Doel: {intake_data.get("doel")}
    """
    emb1 = model.encode([original_question])
    emb2 = model.encode([combined])

    score = cosine_similarity(emb1, emb2)[0][0]
    logger.info("similarity met orignele vraag: %.3f", score)

    return score >= threshold

def validate_answer(key: str, answer: str)->str:
    if not isinstance(answer, str):
        raise AppValidationError("Antwoord moet tekst zijn.")
    
    answer = answer.strip()

    answer = re.sub(r"<.*?>","",answer)

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

