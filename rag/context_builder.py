from langfuse import observe
from typing import Iterable


@observe(name="build_context")
def build_context(nodes: Iterable) -> str:
    """
    Bouwt een contextstring op basis van opgehaalde nodes.

    Combineert tekst en metadata van documenten in een gestructureerd formaat
    dat gebruikt wordt als input voor de LLM.

    Args:
        nodes (Iterable): Verzameling van opgehaalde nodes.

    Returns:
        str: Samengevoegde contextstring voor de LLM.
    """

    context = ""

    for node in nodes:
        text = node.node.get_content()
        metadata = node.node.metadata

        title = metadata.get("title", "Geen titel")
        source = metadata.get("source", "Geen bron")
        url = metadata.get("url", "Geen URL")

        context += f"""[DOCUMENT]
Bron: {source}   
Titel: {title}
URL: {url}

Tekst:
{text}
[/DOCUMENT]"""
    return context
