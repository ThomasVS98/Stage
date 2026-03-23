import re


def clean_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()

def clean_markdown(text:str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"<!-- image -->", "", text)
    return text.strip()