"""Tests for ML model metrics API."""

from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from app.config import get_settings


def test_get_model_metrics_available(client: TestClient) -> None:
    """Verify metrics endpoint returns actual trained metrics when file exists."""
    settings = get_settings()
    if not settings.resolved_metrics_path.is_file():
        pytest.skip("metrics.json does not exist yet. Run training to test metrics.")

    response = client.get("/api/model/metrics")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "available"
    assert data["metrics"] is not None
    m = data["metrics"]
    assert m["accuracy"] == 0.9836
    assert m["precision"] == 0.9018
    assert m["recall"] == 0.7113
    assert m["f1_score"] == 0.7953
    assert m["pr_auc"] == 0.8787
    assert "confusion_matrix" in m
    assert m["confusion_matrix"]["true_negatives"] == 3017
    assert m["confusion_matrix"]["true_positives"] == 101


def test_get_model_metrics_unavailable(client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Ensure endpoint handles missing metrics gracefully with status='unavailable'."""
    settings = get_settings()
    fake_metrics_path = tmp_path / "non_existent_metrics.json"

    monkeypatch.setattr(settings, "metrics_path", str(fake_metrics_path))

    response = client.get("/api/model/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unavailable"
    assert data["metrics"] is None
    assert "train" in data["message"].lower()

