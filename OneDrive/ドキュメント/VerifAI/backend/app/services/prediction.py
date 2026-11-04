"""Machine learning prediction service for VerifAI."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Tuple

from fastapi import HTTPException, status
import joblib

from app.config import get_settings
from ml.preprocess import clean_text

logger = logging.getLogger("VerifAI.ML.PredictionService")


class ModelUnavailableError(HTTPException):
    """Raised when the trained machine learning model cannot be loaded."""

    def __init__(
        self,
        detail: str = (
            "Machine learning model artifact is not available. Please ensure the model "
            "has been trained using 'python ml/train.py' before invoking prediction."
        ),
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )


class PredictionService:
    """Manages model loading, caching, and genuine real-time inference."""

    _instance: PredictionService | None = None

    def __init__(self, model_path: Path | None = None) -> None:
        settings = get_settings()
        self.model_path: Path = model_path or settings.resolved_model_path
        self.model: Any = None
        self._load_model_if_needed()

    @classmethod
    def get_instance(cls) -> PredictionService:
        """Singleton accessor for the prediction service."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton for testing."""
        cls._instance = None

    def _load_model_if_needed(self) -> None:
        """Attempt to load the trained model pipeline into memory."""
        if self.model is not None:
            return

        if self.model_path is None or not self.model_path.is_file():
            logger.warning(
                "Model file not found at %s. ML inference will return 503 until trained.",
                self.model_path,
            )
            self.model = None
            return

        try:
            logger.info("Loading ML model artifact from %s...", self.model_path)
            self.model = joblib.load(self.model_path)
            logger.info("ML model successfully loaded into memory: %s", type(self.model))
        except Exception as e:
            logger.error("Failed to deserialize model at %s: %s", self.model_path, e, exc_info=True)
            self.model = None

    @property
    def is_available(self) -> bool:
        """Check if model is currently loaded and ready for inference."""
        if self.model is None:
            self._load_model_if_needed()
        return self.model is not None

    def predict(self, raw_text: str) -> Tuple[str, float]:
        """Execute genuine inference on input recruitment text.

        Args:
            raw_text: Raw advertisement or letter text.

        Returns:
            Tuple of (prediction_label, model_score).
            prediction_label: "SUSPICIOUS" or "LEGITIMATE"
            model_score: Calibrated float between 0.0 and 1.0 (fraud risk probability).

        Raises:
            ModelUnavailableError: If model is not loaded.
            HTTPException: If text is empty or invalid.
        """
        if not self.is_available:
            raise ModelUnavailableError()

        cleaned = clean_text(raw_text)
        if not cleaned or len(cleaned.strip()) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Input text must contain at least 10 non-whitespace characters for analysis.",
            )

        try:
            pred_class = int(self.model.predict([cleaned])[0])

            if hasattr(self.model, "predict_proba"):
                probs = self.model.predict_proba([cleaned])[0]
                model_score = float(probs[1])
            elif hasattr(self.model, "decision_function"):
                decision = float(self.model.decision_function([cleaned])[0])
                model_score = 1.0 / (1.0 + (2.718281828459045 ** (-decision)))
            else:
                model_score = float(pred_class)

            model_score = round(model_score, 4)
            prediction_label = "SUSPICIOUS" if pred_class == 1 else "LEGITIMATE"

            return prediction_label, model_score

        except Exception as err:
            logger.error("Inference execution failed: %s", err, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error executing ML inference pipeline: {str(err)}",
            )
