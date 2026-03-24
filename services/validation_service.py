import re
from fastapi import HTTPException

def validate_answer(key: str, answer: str)->str:
    answer = answer.strip()

    answer = re.sub(r"<.*?>","",answer)

    if not answer:
        raise ValueError("Antwoord mag niet leeg zijn.")
    if key == "beschrijving":
        if len(answer) < 5:
            raise HTTPException(status_code=400, detail="Beschrijving is te kort.")
        if len(answer) > 80:
            raise HTTPException(
                status_code=400,
                detail="Beschrijving mag maxiumum 80 karakters bevatten."
            )

    elif key == "context":
        if len(answer) < 5:
            raise HTTPException(status_code=400, detail="Context is te kort.")
    elif key == "doel":
        if len(answer) < 5:
            raise HTTPException(status_code=400, detail="Doel is te kort.")
        
    return answer