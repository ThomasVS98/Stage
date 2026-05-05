import re


def clean_text(text: str) -> str:
    """
    Voert basis opschoning uit op tekst.

    - normaliseert spaties en tabs
    - reduceert meerdere lege lijnen

    Args:
        text (str): Inkomende tekst.

    Returns:
        str: Opgeschoonde tekst.
    """
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()


def clean_markdown(text: str) -> str:
    """
    Verwijdert ongewenste Markdown elementen en normaliseert witruimte.

    Args:
        text (str): Inkomende Markdown tekst.

    Returns:
        str: Opgeschoonde Markdown tekst.
    """
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"<!-- image -->", "", text)
    return text.strip()


def clean_topdesk_text(text: str) -> str:
    """
    Specifieke opschoning voor TOPdesk ticket content.

    Verwijdert o.a. datum-prefixen en overtollige witruimtes.

    Args:
        text (str): Ruwe TOPdesk tekst.

    Returns:
        str: Opgeschoonde tekst.
    """
    if not text:
        return ""
    text = re.sub(r"^\d{2}-\d{2}-\d{4}.*?Topdesk:\s*", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def normalize_text(text: str) -> str:
    """
    Normaliseert tekst naar een consistente vorm.

    - zet alle line endings om naar "\\n"
    - verwijdert overtollige spaties
    - reduceert lege lijnen

    Args:
        text (str): Inkomende tekst.

    Returns:
        str: Genormaliseerde tekst.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+\n", "\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
