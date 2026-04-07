from llama_index.llms.ollama import Ollama

llm = Ollama(
    model="llama3.2:3b", #mistral:7b
    request_timeout=300,
    context_window=6140, #6140
    temperature=0
)