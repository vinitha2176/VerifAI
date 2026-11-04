"""Tests for the ML PredictionService."""

from pathlib import Path
import pytest
from fastapi import HTTPException

from app.services.prediction import ModelUnavailableError, PredictionService
from ml.preprocess import clean_text


def test_clean_text_normalization() -> None:
    """Verify text preprocessing strips HTML, emails, and excessive whitespace."""
    raw = "<p>Join our <b>team</b>! Email hr@scam.com. Visit https://fake.link   today!   </p>"
    cleaned = clean_text(raw)
    assert "<p>" not in cleaned
    assert "<b>" not in cleaned
    assert "hr@scam.com" not in cleaned
    assert "https://" not in cleaned
    assert "join our team" in cleaned


def test_prediction_service_valid_prediction() -> None:
    """Validate genuine model inference on recruitment text."""
    service = PredictionService.get_instance()

    if not service.is_available:
        pytest.skip("ML model artifact not found. Train model to run real inference test.")

    legitimate_text = (
        "Senior Software Engineer needed for a reputable enterprise cloud software provider. "
        "Candidates must have at least 5 years experience in Python and distributed systems. "
        "Full-time role offering standard salary, equity, and healthcare."
    )
    label, score = service.predict(legitimate_text)

    assert label in ("LEGITIMATE", "SUSPICIOUS")
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_prediction_service_empty_input_rejected() -> None:
    """Ensure empty or whitespace-only inputs are rejected with 400 Bad Request."""
    service = PredictionService.get_instance()
    if not service.is_available:
        pytest.skip("ML model artifact not found.")

    with pytest.raises(HTTPException) as exc_info:
        service.predict("   \n\t   ")
    assert exc_info.value.status_code == 400


def test_missing_model_handling(tmp_path: Path) -> None:
    """Verify that pointing to a missing model file raises ModelUnavailableError."""
    non_existent = tmp_path / "does_not_exist.joblib"
    isolated_service = PredictionService(model_path=non_existent)

    assert not isolated_service.is_available
    with pytest.raises(ModelUnavailableError) as exc_info:
        isolated_service.predict("Some job description text that cannot be analyzed.")
    assert exc_info.value.status_code == 503

