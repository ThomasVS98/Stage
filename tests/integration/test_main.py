import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from api.main import app as main_app
from utils.exceptions import (
    AppValidationError,
    SourceConfigError,
    ExternalServiceError,
    IngestionError,
)


def create_test_app():
    test_app = FastAPI()

    for exc, handler in main_app.exception_handlers.items():
        test_app.add_exception_handler(exc, handler)

    @test_app.get("/test-validation-error")
    def raise_validation():
        raise AppValidationError("Test fout")

    @test_app.get("/test-source-error")
    def raise_source():
        raise SourceConfigError("Config fout")

    @test_app.get("/test-external-error")
    def raise_external():
        raise ExternalServiceError("API down")

    @test_app.get("/test-ingestion-error")
    def raise_ingestion():
        raise IngestionError("Ingestie mislukt")

    return test_app


@pytest.fixture
def test_client():
    app = create_test_app()
    return TestClient(app)


def test_validation_exception_handler(test_client):
    response = test_client.get("/test-validation-error")
    assert response.status_code == 400
    assert "Validatiefout" in response.json()["detail"]


def test_source_exception_handler(test_client):
    response = test_client.get("/test-source-error")
    assert response.status_code == 400
    assert "Bron fout" in response.json()["detail"]


def test_external_exception_handler(test_client):
    response = test_client.get("/test-external-error")
    assert response.status_code == 502
    assert "Fout bij externe dienst" in response.json()["detail"]


def test_ingestion_exception_handler(test_client):
    response = test_client.get("/test-ingestion-error")
    assert response.status_code == 500
    assert "Ingestie fout" in response.json()["detail"]
