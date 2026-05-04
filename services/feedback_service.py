import json
from datetime import datetime, timezone
from utils.logging import get_logger

logger = get_logger(__name__)

def save_feedback(query: str, answer: str, score: str):
    try:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "answer": answer,
            "score": score
        }

        with open("feedback.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    except Exception:
        logger.exception("Failed to save feedback")


