from fastapi import FastAPI
from llama_index.llms.ollama import Ollama

app = FastAPI()

llm = Ollama(
    model="llama3.2:3b",
    request_timeout=120,
    context_window=4096
)

@app.get("/")
def root():
    return {"message": "backend running"}

@app.get("/chat")
def chat(query: str):
    response = llm.complete(query)
    return {"response": response.text}
