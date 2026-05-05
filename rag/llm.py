from llama_index.llms.ollama import Ollama

_llm = None


def get_llm() -> Ollama:
    """
    Initialiseert en retourneert het LLM model.

    Het model wordt slechts één keer geladen
    en hergebruikt voor alle LLM calls.

    Configuratie:
    - model: lokaal Ollama model
    - temperature: 0 voor deterministische antwoorden (geen randomisatie)
    - context_window: maximale contextlengte

    Returns:
        Ollama: Geconfigureerde LLM instantie.
    """
    global _llm
    if _llm is None:
        _llm = Ollama(
            model="llama3.2:3b",
            request_timeout=300,
            context_window=6140,
            temperature=0,
        )
    return _llm
