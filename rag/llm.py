from llama_index.llms.ollama import Ollama
from dotenv import load_dotenv
import os

load_dotenv()

SERVER_URL = os.getenv("SERVER_URL")

llm = Ollama(
    model="llama3.2:3b", #mistral:7b
    #base_url=SERVER_URL,
    request_timeout=300,
    context_window=6140, #6140
    temperature=0
)