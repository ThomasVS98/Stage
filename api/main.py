from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from langfuse import get_client
from dotenv import load_dotenv
from api.routes.intake_routes import router as intake_router
from api.routes.rag_routes import router as rag_router
from api.routes.admin_routes import router as admin_router
from api.routes.feedback_routes import router as feedback_router
from utils.logging import setup_logging
from utils.exceptions import (
    AppValidationError,
    SourceConfigError,
    ExternalServiceError,
    IngestionError,
)
from services.qa_service import executor
from contextlib import asynccontextmanager

load_dotenv()
setup_logging()

LlamaIndexInstrumentor().instrument()
langfuse = get_client()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    executor.shutdown(wait=False)


app = FastAPI(lifespan=lifespan)


@app.exception_handler(AppValidationError)
async def validation_exception_handler(request: Request, exc: AppValidationError):
    return JSONResponse(
        status_code=400, content={"detail": f"Validatiefout: {str(exc)}"}
    )


@app.exception_handler(SourceConfigError)
async def source_config_exception_handler(request: Request, exc: SourceConfigError):
    return JSONResponse(status_code=400, content={"detail": f"Bron fout: {str(exc)}"})


@app.exception_handler(ExternalServiceError)
async def external_service_exception_handler(
    request: Request, exc: ExternalServiceError
):
    return JSONResponse(
        status_code=502, content={"detail": f"Fout bij externe dienst: {str(exc)}"}
    )


@app.exception_handler(IngestionError)
async def ingestion_exception_handler(request: Request, exc: IngestionError):
    return JSONResponse(
        status_code=500, content={"detail": f"Ingestie fout: {str(exc)}"}
    )


app.include_router(intake_router)
app.include_router(rag_router)
app.include_router(admin_router)
app.include_router(feedback_router)


@app.get("/")
def root():
    return {"message": "RAG API running"}
