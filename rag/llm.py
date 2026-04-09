from llama_index.llms.ollama import Ollama

_llm = None

def get_llm():
    global _llm
    if _llm is None:
        _llm = Ollama(
            model="llama3.2:3b", #mistral:7b
            request_timeout=300,
            context_window=6140, #6140
            temperature=0
        )
    return _llm