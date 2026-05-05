import json
from datetime import datetime, timezone
from utils.logging import get_logger

logger = get_logger(__name__)


def save_feedback(query: str, answer: str, score: str) -> None:
    """
    Slaat gebruikersfeedback op in een JSONL bestand.

    Elke feedback entry bevat:
    - timestamp (UTC)
    - query (gebruikersvraag)
    - answer (gegenereerd antwoord)
    - score (duimpje omhoog ("up") of omlaag ("down"))

    Args:
        query (str): De oorspronkelijke gebruikersvraag.
        answer (str): Het gegenereerde antwoord.
        score (str): De feedbackscore ("up" of "down").
    """
    try:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "answer": answer,
            "score": score,
        }

        with open("feedback.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    except Exception:
        logger.exception("Failed to save feedback")
