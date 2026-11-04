"""VerifAI - AI-Powered Job & Internship Scam Risk Detection Platform.

Tagline: Verify opportunities. Protect your future.

FastAPI main application entrypoint providing RESTful endpoints for recruitment
risk analysis, PDF document parsing, ML model metrics, and analysis history.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.database import get_db, init_db
from app.routes.analyze import router as analyze_router
from app.routes.history import router as history_router
from app.routes.metrics import router as metrics_router
from app.schemas.analysis import HealthResponse
from app.services.prediction import PredictionService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle handler."""
    # Initialize SQLite database schema
    init_db()
    yield


settings = get_settings()

app = FastAPI(
    title="VerifAI API",
    description=(
        "VerifAI is an AI-powered recruitment scam risk detection platform. "
        "Verify opportunities. Protect your future. "
        "It analyzes job descriptions, internships, and offer letters using genuine "
        "machine learning models trained on the EMSCAD dataset alongside an "
        "independent contextual risk rule engine."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for future React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(analyze_router)
app.include_router(history_router)
app.include_router(metrics_router)


@app.get(
    "/api/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["System Health"],
    summary="System health and component status check",
)
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Verify backend responsiveness, SQLite database access, and ML model state."""
    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as db_err:
        db_status = f"unavailable: {str(db_err)}"

    # Check ML model status
    pred_service = PredictionService.get_instance()
    ml_status = "loaded" if pred_service.is_available else "not_loaded"

    return HealthResponse(
        status="healthy",
        database=db_status,
        ml_model=ml_status,
        model_details={
            "model_path": str(settings.resolved_model_path),
            "model_exists": settings.resolved_model_path.is_file(),
            "metrics_exists": settings.resolved_metrics_path.is_file(),
        },
    )


@app.get("/", include_in_schema=False)
def root_redirect() -> dict:
    """Friendly root endpoint pointing to Swagger documentation."""
    return {
        "name": "VerifAI API",
        "tagline": "Verify opportunities. Protect your future.",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/api/health",
    }
