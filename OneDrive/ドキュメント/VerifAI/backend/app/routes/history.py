"""Endpoints for managing and querying analysis history."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.models.database import get_db
from app.schemas.analysis import (
    AnalysisDetailResponse,
    AnalysisListResponse,
    AnalysisSummaryResponse,
    VERIFAI_DISCLAIMER,
)

router = APIRouter(prefix="/api/history", tags=["Analysis History"])


@router.get(
    "",
    response_model=AnalysisListResponse,
    summary="List past analysis evaluations",
    description="Returns recorded analysis entries ordered by most recent first.",
)
def get_analysis_history(
    limit: int = Query(default=20, ge=1, le=100, description="Number of entries to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
) -> AnalysisListResponse:
    """Retrieve paginated historical analysis records."""
    total = db.scalar(select(func.count(Analysis.id))) or 0

    stmt = (
        select(Analysis)
        .order_by(Analysis.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    records = db.scalars(stmt).all()

    items = [
        AnalysisSummaryResponse(
            id=r.id,
            submission_type=r.submission_type,
            submitted_text_preview=r.submitted_text_preview,
            prediction=r.prediction,
            model_score=r.model_score,
            rule_risk_score=r.rule_risk_score,
            risk_level=r.risk_level,
            indicator_count=len(r.detected_indicators) if isinstance(r.detected_indicators, list) else 0,
            created_at=r.created_at,
        )
        for r in records
    ]

    return AnalysisListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items,
    )


@router.get(
    "/{analysis_id}",
    response_model=AnalysisDetailResponse,
    summary="Get single analysis details",
    description="Retrieve full details and detected indicators for a given analysis ID.",
)
def get_analysis_detail(
    analysis_id: int,
    db: Session = Depends(get_db),
) -> AnalysisDetailResponse:
    """Fetch complete metadata for an individual analysis."""
    record = db.get(Analysis, analysis_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis record with ID {analysis_id} was not found.",
        )

    evidence_list = [
        ind.get("matched_evidence")
        for ind in record.detected_indicators
        if isinstance(ind, dict) and ind.get("matched_evidence")
    ]

    return AnalysisDetailResponse(
        id=record.id,
        submission_type=record.submission_type,
        prediction=record.prediction,
        model_score=record.model_score,
        rule_risk_score=record.rule_risk_score,
        risk_level=record.risk_level,
        detected_indicators=record.detected_indicators,
        evidence=evidence_list,
        recommendations=record.recommendations,
        disclaimer=VERIFAI_DISCLAIMER,
        created_at=record.created_at,
        submitted_text_preview=record.submitted_text_preview,
        text_length=record.text_length,
    )


@router.delete(
    "/{analysis_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an analysis record",
    description="Permanently deletes an analysis record from history.",
)
def delete_analysis_record(
    analysis_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Delete an analysis record by ID."""
    record = db.get(Analysis, analysis_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis record with ID {analysis_id} was not found.",
        )

    db.delete(record)
    db.commit()

    return {
        "status": "success",
        "message": f"Analysis record with ID {analysis_id} has been permanently deleted.",
        "id": analysis_id,
    }
