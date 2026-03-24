from llama_index.llms.ollama import Ollama

llm = Ollama(
    model="mistral:7b", #llama3.2:3b
    request_timeout=300,
    context_window=10000, #6140
    temperature=0
)