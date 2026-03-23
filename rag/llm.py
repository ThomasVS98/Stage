from llama_index.llms.ollama import Ollama

llm = Ollama(
    model="llama3.2:3b", #mistral:7b
    request_timeout=300,
    context_window=6144,
    temperature=0
)