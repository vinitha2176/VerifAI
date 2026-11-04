"""PDF document validation and text extraction service using PyMuPDF."""

from __future__ import annotations

import io
from pathlib import Path
from typing import BinaryIO

import pymupdf as fitz
from fastapi import HTTPException, status

# PDF file magic bytes signature
PDF_MAGIC_HEADER = b"%PDF-"


# Modern and backward-compatible Starlette status codes
HTTP_413 = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413)
HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


class PDFExtractionError(HTTPException):
    """Custom exception for PDF processing errors."""

    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


def validate_pdf_content(file_bytes: bytes, max_size_bytes: int = 10 * 1024 * 1024) -> None:
    """Validate PDF file header magic bytes and enforce size constraints.

    Args:
        file_bytes: Raw binary content of the uploaded file.
        max_size_bytes: Maximum allowed file size in bytes (defaults to 10MB).

    Raises:
        PDFExtractionError: If size limit is exceeded or file is not a valid PDF.
    """
    if not file_bytes:
        raise PDFExtractionError("The uploaded file is empty.", status_code=status.HTTP_400_BAD_REQUEST)

    if len(file_bytes) > max_size_bytes:
        mb_size = len(file_bytes) / (1024 * 1024)
        max_mb = max_size_bytes / (1024 * 1024)
        raise PDFExtractionError(
            f"File size ({mb_size:.1f} MB) exceeds maximum allowed limit of {max_mb:.0f} MB.",
            status_code=HTTP_413,
        )

    # Validate PDF signature (magic bytes)
    if not file_bytes.startswith(PDF_MAGIC_HEADER):
        raise PDFExtractionError(
            "Unsupported file format: File header does not match standard PDF signature (%PDF-). "
            "Please upload a valid PDF document.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


def extract_text_from_pdf_bytes(file_bytes: bytes, max_size_bytes: int = 10 * 1024 * 1024) -> str:
    """Extract textual content from raw PDF bytes safely in memory.

    Args:
        file_bytes: Raw bytes of the uploaded PDF document.
        max_size_bytes: Maximum permissible file size in bytes.

    Returns:
        Extracted and sanitized text content.

    Raises:
        PDFExtractionError: When PDF is corrupted, empty, or scanned without extractable text.
    """
    validate_pdf_content(file_bytes, max_size_bytes=max_size_bytes)

    try:
        # Open PDF from in-memory stream without persisting to disk
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise PDFExtractionError(
            f"Corrupted or unreadable PDF document. Could not parse PDF structure: {str(e)}",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        if doc.page_count == 0:
            raise PDFExtractionError(
                "The uploaded PDF document contains no pages.",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        extracted_pages = []
        for page_idx in range(doc.page_count):
            try:
                page = doc.load_page(page_idx)
                page_text = page.get_text("text")
                if page_text and page_text.strip():
                    extracted_pages.append(page_text.strip())
            except Exception as page_err:
                # Log page failure and continue to salvage remaining pages
                continue

        full_text = "\n\n".join(extracted_pages).strip()

        if not full_text:
            raise PDFExtractionError(
                "No extractable text found in the PDF. Scanned or image-only documents "
                "require OCR, which is not supported in this phase. "
                "Please submit a digital text-based PDF or paste the text directly.",
                status_code=HTTP_422,
            )

        return full_text

    finally:
        doc.close()
