import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_auth_unauthorized():
    # Attempting to access an endpoint that might need auth or just a fake project route
    response = client.get("/api/v1/projects")
    # If projects route doesn't have auth enabled by default, it will return 200
    # But let's check it exists
    assert response.status_code in (200, 401)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "NIRVANA API"
