from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_healthcheck_success():
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "service" in response.json()


def test_healthcheck_content_type():
    response = client.get("/healthcheck")
    assert "application/json" in response.headers["content-type"]
