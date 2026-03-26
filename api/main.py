from fastapi import FastAPI
from api.routes.intake_routes import router as intake_router
from api.routes.rag_routes import router as rag_router
from api.routes.admin_routes import router as admin_router

app = FastAPI()

app.include_router(intake_router)
app.include_router(rag_router)
app.include_router(admin_router)

@app.get("/")
def root():
    return {"message": "RAG API running"}