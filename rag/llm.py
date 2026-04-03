from llama_index.llms.ollama import Ollama
from config.settings import settings

SERVER_URL = settings.API_BASE_URL

llm = Ollama(
    model="llama3.2:3b", #mistral:7b
    #base_url=SERVER_URL,
    request_timeout=300,
    context_window=6140, #6140
    temperature=0
)