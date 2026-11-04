"""Pydantic schemas for VerifAI API requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

VERIFAI_DISCLAIMER = (
    "VerifAI provides automated risk assessments based on submitted content. "
    "It does not verify employer identity or establish that an organisation is fraudulent. "
    "Always independently verify recruitment opportunities before sharing money or sensitive information."
)


class TextAnalysisRequest(BaseModel):
    """Payload for text analysis endpoint."""

    text: str = Field(
        ...,
        min_length=15,
        max_length=50000,
        description="The recruitment advertisement, description, or offer letter text to analyze.",
        examples=["Earn $5000 per week working 2 hours a day. Pay registration fee of $100."],
    )


class DetectedIndicator(BaseModel):
    """Detailed metadata for a detected risk rule indicator."""

    indicator_name: str = Field(..., description="Human-readable title of the detected rule")
    severity: str = Field(..., description="Risk severity: LOW, MEDIUM, HIGH, or CRITICAL")
    explanation: str = Field(..., description="Explanation of why this pattern is suspicious")
    matched_evidence: str = Field(..., description="Exact extracted sentence or context from input text")


class AnalysisResponse(BaseModel):
    """Standard analysis result schema for text and PDF analysis."""

    id: int = Field(..., description="Unique analysis record ID")
    submission_type: str = Field(..., description="Type of submission: text or pdf")
    prediction: str = Field(..., description="Binary ML prediction outcome: SUSPICIOUS or LEGITIMATE")
    model_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated ML probability score (0.0 to 1.0)")
    rule_risk_score: float = Field(..., ge=0.0, le=1.0, description="Deterministic rule-based risk score (0.0 to 1.0)")
    risk_level: str = Field(..., description="Composite risk level: LOW, MODERATE, or HIGH")
    detected_indicators: List[DetectedIndicator] = Field(
        default_factory=list,
        description="List of suspicious indicators triggered by the rule engine",
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="List of extracted evidence sentences from the document",
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable guidance and verification steps for the candidate",
    )
    disclaimer: str = Field(
        default=VERIFAI_DISCLAIMER,
        description="Mandatory legal disclaimer on automated risk evaluation",
    )
    created_at: datetime = Field(..., description="Timestamp of when the analysis was performed")


class AnalysisSummaryResponse(BaseModel):
    """Summary of an analysis record for history listings."""

    id: int
    submission_type: str
    submitted_text_preview: str
    prediction: str
    model_score: float
    rule_risk_score: float
    risk_level: str
    indicator_count: int
    created_at: datetime


class AnalysisDetailResponse(AnalysisResponse):
    """Detailed record including preview information from database storage."""

    submitted_text_preview: str
    text_length: int


class AnalysisListResponse(BaseModel):
    """Paginated list of historical analysis records."""

    total: int
    limit: int
    offset: int
    items: List[AnalysisSummaryResponse]


class HealthResponse(BaseModel):
    """Health check endpoint response schema."""

    status: str
    database: str
    ml_model: str
    model_details: Optional[Dict[str, Any]] = None


class ModelMetricsResponse(BaseModel):
    """Model evaluation metrics schema."""

    status: str
    metrics: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
