"""Endpoints for serving trained model evaluation metrics."""

from fastapi import APIRouter, status
from app.config import get_settings
from app.schemas.analysis import ModelMetricsResponse
from ml.evaluate import load_metrics_from_json

router = APIRouter(prefix="/api/model", tags=["Model Metrics"])


@router.get(
    "/metrics",
    response_model=ModelMetricsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ML model evaluation metrics",
    description=(
        "Returns the actual, verifiable evaluation metrics (Accuracy, Precision, Recall, "
        "F1-score, PR-AUC, Confusion Matrix) calculated on the held-out EMSCAD test split."
    ),
)
def get_model_metrics() -> ModelMetricsResponse:
    """Return trained model evaluation metrics from saved metrics.json artifact."""
    settings = get_settings()
    metrics = load_metrics_from_json(settings.resolved_metrics_path)

    if metrics is None:
        return ModelMetricsResponse(
            status="unavailable",
            metrics=None,
            message=(
                "Model evaluation metrics are not available. Please train the model "
                "by executing 'python ml/train.py'."
            ),
        )

    return ModelMetricsResponse(
        status="available",
        metrics=metrics,
        message=None,
    )

