"""Tests for system health and diagnostics endpoints."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient) -> None:
    """Ensure root path returns API metadata and documentation link."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "VerifAI API"
    assert data["tagline"] == "Verify opportunities. Protect your future."
    assert "/docs" in data["documentation"]
    assert "/api/health" in data["health"]


def test_health_check_endpoint(client: TestClient) -> None:
    """Verify health endpoint reports backend status, database, and model info."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["ml_model"] in ("loaded", "not_loaded")
    assert "model_details" in data
    assert "model_exists" in data["model_details"]
