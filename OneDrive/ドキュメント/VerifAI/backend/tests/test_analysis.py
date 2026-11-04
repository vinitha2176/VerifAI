"""Tests for recruitment risk analysis endpoints and PDF extraction service."""

import io
from fastapi.testclient import TestClient

from app.schemas.analysis import VERIFAI_DISCLAIMER


def test_analyze_text_legitimate(client: TestClient) -> None:
    """Submit legitimate recruitment notice and verify response structure and disclaimer."""
    payload = {
        "text": (
            "Seeking an experienced Senior DevOps Engineer. You will manage Kubernetes "
            "clusters and Terraform infrastructure. We offer a competitive salary, "
            "comprehensive health insurance, and 401(k) matching."
        )
    }
    response = client.post("/api/analyze/text", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "id" in data
    assert data["submission_type"] == "text"
    assert data["prediction"] in ("LEGITIMATE", "SUSPICIOUS")
    assert 0.0 <= data["model_score"] <= 1.0
    assert 0.0 <= data["rule_risk_score"] <= 1.0
    assert data["risk_level"] in ("LOW", "MODERATE", "HIGH")
    assert data["disclaimer"] == VERIFAI_DISCLAIMER
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) > 0


def test_analyze_text_scam_high_risk(client: TestClient) -> None:
    """Submit overt scam job notice and verify HIGH risk tier classification."""
    payload = {
        "text": (
            "DIRECT SELECTION! You are hired without interview! "
            "Pay ₹2,500 registration fee urgently within 24 hours to book your seat. "
            "Deposit ₹5,000 for training laptop. Earn $5,000 daily!"
        )
    }
    response = client.post("/api/analyze/text", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["risk_level"] == "HIGH"
    assert len(data["detected_indicators"]) >= 2
    assert any("Registration" in ind["indicator_name"] for ind in data["detected_indicators"])


def test_analyze_text_negation_awareness_api(client: TestClient) -> None:
    """Verify endpoint suppresses false alarms when fees are explicitly negated in text."""
    payload = {
        "text": (
            "Welcome to our Graduate Engineering Program at Tata Consultancy Services. "
            "Disclaimer: There is no registration fee or application fee for this process. "
            "Selected candidates will undergo formal technical assessments."
        )
    }
    response = client.post("/api/analyze/text", json=payload)
    assert response.status_code == 200
    data = response.json()
    indicator_names = [ind["indicator_name"] for ind in data["detected_indicators"]]
    assert not any("Registration" in name for name in indicator_names)
    assert not any("Processing" in name for name in indicator_names)


def test_analyze_text_too_short(client: TestClient) -> None:
    """Verify input validation fails on overly brief text (fewer than 15 chars)."""
    response = client.post("/api/analyze/text", json={"text": "Short"})
    assert response.status_code == 422  # Pydantic validation error


def test_analyze_text_empty(client: TestClient) -> None:
    """Verify input validation fails on empty text."""
    response = client.post("/api/analyze/text", json={"text": ""})
    assert response.status_code == 422


def test_analyze_text_exceeding_max_length(client: TestClient) -> None:
    """Verify input validation fails when text exceeds 50,000 characters."""
    oversized_text = "A" * 50001
    response = client.post("/api/analyze/text", json={"text": oversized_text})
    assert response.status_code == 422


def test_analyze_pdf_valid(client: TestClient, sample_valid_pdf_bytes: bytes) -> None:
    """Upload a valid PDF document and verify successful text extraction and analysis."""
    files = {"file": ("offer_letter.pdf", sample_valid_pdf_bytes, "application/pdf")}
    response = client.post("/api/analyze/file", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["submission_type"] == "pdf"
    assert "Software Engineer" in str(data) or data["risk_level"] in ("LOW", "MODERATE")
    assert data["disclaimer"] == VERIFAI_DISCLAIMER


def test_analyze_pdf_scam(client: TestClient, sample_scam_pdf_bytes: bytes) -> None:
    """Upload a scam PDF document and verify red flag detection."""
    files = {"file": ("urgent_offer.pdf", sample_scam_pdf_bytes, "application/pdf")}
    response = client.post("/api/analyze/file", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["submission_type"] == "pdf"
    assert data["risk_level"] == "HIGH"
    assert len(data["detected_indicators"]) >= 1


def test_analyze_pdf_empty_pages(client: TestClient, sample_empty_pdf_bytes: bytes) -> None:
    """Verify empty/scanned PDF returns unprocessable entity 422 explaining OCR limitation."""
    files = {"file": ("empty.pdf", sample_empty_pdf_bytes, "application/pdf")}
    response = client.post("/api/analyze/file", files=files)
    assert response.status_code == 422
    assert "OCR" in response.json()["detail"]


def test_analyze_pdf_corrupted_file(client: TestClient) -> None:
    """Ensure corrupted PDF file returns 400 Bad Request."""
    corrupted_bytes = b"%PDF-corrupted-content-invalid-data-truncated"
    files = {"file": ("corrupted.pdf", corrupted_bytes, "application/pdf")}
    response = client.post("/api/analyze/file", files=files)
    assert response.status_code == 400
    assert "Corrupted" in response.json()["detail"]


def test_analyze_pdf_unsupported_file_type(client: TestClient) -> None:
    """Ensure non-PDF files (e.g. .exe or .txt disguised as .pdf) are rejected."""
    # Disguised .txt file
    fake_pdf = b"This is plain text pretending to be a PDF."
    files = {"file": ("fake.pdf", fake_pdf, "application/pdf")}
    response = client.post("/api/analyze/file", files=files)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]

    # Wrong extension
    files_wrong_ext = {"file": ("file.docx", b"some bytes", "application/msword")}
    response2 = client.post("/api/analyze/file", files=files_wrong_ext)
    assert response2.status_code == 400


def test_analyze_pdf_oversized_file(client: TestClient) -> None:
    """Verify files exceeding 10MB are rejected with 413 Entity Too Large."""
    # 11MB pseudo-PDF
    huge_bytes = b"%PDF-" + (b"0" * (11 * 1024 * 1024))
    files = {"file": ("huge.pdf", huge_bytes, "application/pdf")}
    response = client.post("/api/analyze/file", files=files)
    assert response.status_code == 413
