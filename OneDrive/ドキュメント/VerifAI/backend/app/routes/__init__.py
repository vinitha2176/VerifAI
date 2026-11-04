"""API Routes package for VerifAI."""

from app.routes.analyze import router as analyze_router
from app.routes.history import router as history_router
from app.routes.metrics import router as metrics_router

__all__ = ["analyze_router", "history_router", "metrics_router"]
