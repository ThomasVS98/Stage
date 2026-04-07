from fastapi.testclient import TestClient
from api.main import app
from utils.exceptions import (
    AppValidationError,
    SourceConfigError,
    ExternalServiceError,
    IngestionError
)

client = TestClient(app)

@app.get("/test-validation-error")
def raise_validation():
    raise AppValidationError("Test fout")

@app.get("/test-source-error")
def raise_source():
    raise SourceConfigError("Config fout")

@app.get("/test-external-error")
def raise_external():
    raise ExternalServiceError("API down")

@app.get("/test-ingestion-error")
def raise_ingestion():
    raise IngestionError("Ingestie mislukt")

def test_validation_exception_handler():
    response = client.get("/test-validation-error")
    assert response.status_code == 400
    assert "Validatiefout" in response.json()["detail"]

def test_source_exception_handler():
    response = client.get("/test-source-error")
    assert response.status_code == 400
    assert "Bron fout" in response.json()["detail"]

def test_external_exception_handler():
    response = client.get("/test-external-error")
    assert response.status_code == 502
    assert "Fout bij externe dienst" in response.json()["detail"]

def test_ingestion_exception_handler():
    response = client.get("/test-ingestion-error")
    assert response.status_code == 500
    assert "Ingestie fout" in response.json()["detail"]
