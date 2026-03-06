from fastapi import FastAPI
from pydantic import BaseModel
from query import load_index,detect_service,ask_llm,build_context
from query import lexical_overlap_count
from llama_index.llms.ollama import Ollama

app = FastAPI()

index = load_index()

llm = Ollama(
    model = "llama3.2:3b",
    request_timeout=180,
    context_window=4096
)

class Question(BaseModel):
    question: str

@app.post("/ask")

def ask_question(q:Question):

    query = q.question
    service = detect_service(query)

    retriever = index.as_retriever(
        similarity_top_k=12,

        
    )

