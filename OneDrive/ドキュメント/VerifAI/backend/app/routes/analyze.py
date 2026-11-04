"""Endpoints for recruitment text and document risk analysis."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.schemas.analysis import AnalysisResponse, TextAnalysisRequest
from app.services.analysis_service import AnalysisService
from app.services.extraction import extract_text_from_pdf_bytes

router = APIRouter(prefix="/api/analyze", tags=["Risk Analysis"])


@router.post(
    "/text",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze recruitment text content",
    description=(
        "Performs real-time machine learning fraud classification and contextual "
        "rule engine evaluation on pasted job postings, internships, or offer emails."
    ),
)
def analyze_text(
    payload: TextAnalysisRequest,
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    """Analyze plain recruitment text and persist the result."""
    service = AnalysisService()
    return service.analyze_and_store(
        text=payload.text,
        submission_type="text",
        db=db,
    )


@router.post(
    "/file",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze PDF recruitment document or offer letter",
    description=(
        "Extracts text from an uploaded PDF document (up to 10 MB) using PyMuPDF "
        "and runs ML inference and rule-based risk evaluation."
    ),
)
async def analyze_file(
    file: UploadFile = File(..., description="PDF recruitment offer letter or advertisement"),
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    """Extract and analyze recruitment document from uploaded PDF."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents (.pdf) are supported in this phase.",
        )

    # Read binary stream in memory safely
    file_bytes = await file.read()

    # Extract text with magic bytes and size validation
    extracted_text = extract_text_from_pdf_bytes(file_bytes)

    service = AnalysisService()
    return service.analyze_and_store(
        text=extracted_text,
        submission_type="pdf",
        db=db,
    )

