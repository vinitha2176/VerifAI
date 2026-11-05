"""Automated test suite for recruitment-content relevance validation.

Tests both unit logic and API integration across:
- The Book Thief novel
- Physics research paper
- Academic essay
- Commercial invoice
- Course completion certificate
- Resume/CV
- Genuine job offer
- Legitimate internship advertisement
- Suspicious job offer
- Suspicious internship advertisement
- Informal WhatsApp hiring message
- Short unrelated text
- Database isolation (rejected documents never create records)
- PDF upload relevance validation
"""

from __future__ import annotations

import io
import fitz
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.services.relevance_service import RelevanceValidator, validate_recruitment_relevance


# ---------------------------------------------------------------------------
# Test Data Fixtures
# ---------------------------------------------------------------------------
BOOK_THIEF_TEXT = (
    "First the colors. Then the humans. That's usually how I see things. Or at least, how I try. "
    "HERE IS A SMALL FACT: You are going to die. 1939. Nazi Germany. The country is holding its breath. "
    "Death has never been busier, and will become busier still. Liesel Meminger is a foster girl living outside of Munich, "
    "who scratches out a meager existence for herself by stealing when she encounters something she can't resist–books. "
    "With the help of her accordion-playing foster father, she learns to read and shares her stolen books with her neighbors "
    "during bombing raids as well as with the Jewish man hidden in her basement."
)

PHYSICS_PAPER_TEXT = (
    "Measurement of the Branching Fraction of B -> K* gamma Decays. "
    "Abstract: We present a measurement of the branching fraction of the radiative penguin decay B -> K* gamma. "
    "The data sample consists of 88 million BB pairs collected with the BABAR detector at the PEP-II asymmetric-energy "
    "e+e- storage ring running at the Upsilon(4S) resonance. The systematic uncertainties are dominated by particle identification "
    "and photon reconstruction efficiency. "
    "References: [1] B. Aubert et al., Phys. Rev. Lett. 87, 241803 (2001)."
)

ACADEMIC_ESSAY_TEXT = (
    "Economic Instruments in Carbon Mitigation: An Analysis of Cap-and-Trade Mechanisms. "
    "This essay examines the economic efficiency of market-based environmental policies in reducing industrial greenhouse gas emissions. "
    "By establishing a declining cap on allowable carbon output and allocating tradable permits, governments incentivize private sector innovation. "
    "In conclusion, while cap-and-trade systems offer theoretical cost-effectiveness, empirical outcomes depend heavily on baseline allocation rules "
    "and stringent penalty enforcement."
)

COMMERCIAL_INVOICE_TEXT = (
    "TAX INVOICE. Invoice No: INV-2026-0891. Date: 04/11/2026. "
    "Bill To: TechVentures Pvt Ltd, GSTIN: 29AAAAA0000A1Z5. "
    "Description: Cloud Hosting Server Infrastructure. HSN: 998313. Qty: 1. Unit Price: ₹45,000. "
    "Subtotal: ₹45,000. CGST @ 9%: ₹4,050. SGST @ 9%: ₹4,050. Total Amount Payable: ₹53,100. "
    "Bank Details: HDFC Bank, Account No: 50200012345678, IFSC: HDFC0001234. Payment Terms: Net 30 days."
)

CERTIFICATE_TEXT = (
    "CERTIFICATE OF COMPLETION. This is to certify that Rahul Sharma has successfully completed the "
    "professional development course in Full Stack Web Application Development with Python and React. "
    "Awarded on 15th October 2026. Certificate ID: CERT-89214-FS. "
    "Course Director: Dr. Alan Turing. In recognition of academic dedication and technical proficiency."
)

RESUME_TEXT = (
    "CURRICULUM VITAE - Rahul Sharma\n"
    "Email: rahul.sharma@example.com | Phone: +91 9876543210 | Bengaluru, Karnataka\n"
    "Career Objective: Enthusiastic and results-driven Software Engineer seeking a challenging position in a progressive IT organization "
    "to contribute technical expertise in Python and web development.\n"
    "Education: Bachelor of Technology in Computer Science, VTU (2020 - 2024), CGPA: 8.5/10.\n"
    "Technical Skills: Python, FastAPI, Django, React, PostgreSQL, Docker, Git.\n"
    "Projects: 1. E-Commerce Microservices Platform. 2. Real-Time Chat System.\n"
    "Declaration: I hereby declare that the details provided above are true to the best of my knowledge."
)

GENUINE_JOB_OFFER_TEXT = (
    "Senior Backend Engineer. Company: CloudScale Systems Inc. Location: Remote / Bengaluru, India. "
    "Job Description: We are seeking an experienced Backend Software Engineer with at least 4 years of experience in Python, FastAPI, "
    "and PostgreSQL. You will design reliable microservices and collaborate with distributed teams. "
    "Requirements: Bachelor's degree in CS, proficiency in Python, familiarity with Docker. "
    "Benefits: Competitive base salary, health insurance. Application: Apply directly through our career portal."
)

LEGITIMATE_INTERNSHIP_TEXT = (
    "Acme Systems - Summer Engineering Internship. "
    "We invite applications for our competitive three-month internship program in Software Engineering. "
    "Selected interns receive a ₹10,000 monthly stipend and work directly with senior architects. "
    "Candidates must complete a technical interview and practical assessment. "
    "No registration fee, security deposit, or application fee is required at any point in our hiring process. "
    "Apply via our official corporate careers portal."
)

SUSPICIOUS_JOB_OFFER_TEXT = (
    "Apex Technologies - Junior Software Developer. "
    "We are pleased to inform you of your guaranteed selection without an interview for the Junior Software Developer position. "
    "To confirm your acceptance, a refundable registration fee of ₹2,500 must be paid immediately. "
    "Immediate payment requirement applies to secure your placement in this cohort."
)

SUSPICIOUS_INTERNSHIP_TEXT = (
    "Global Infotech Internship Program. "
    "Congratulations! You have received guaranteed selection without an interview for our 2026 Developer Internship. "
    "A non-refundable onboarding charge of ₹1,999 is required to initiate your profile. "
    "Additionally, a mandatory ₹4,000 training charge must be paid for the induction module. "
    "Please submit your identity documents and bank details via Telegram to our HR coordinator (@InfotechHR). "
    "This offer expires within a 2-hour deadline, so payment must be transferred immediately."
)

INFORMAL_WHATSAPP_TEXT = (
    "Urgent requirement! Looking for 5 Data Entry Operators to work from home. "
    "Flexible timing 2-3 hours daily. Earn ₹15,000 - ₹25,000 per month. Freshers can apply. "
    "No experience needed. Contact HR on WhatsApp +91 9876543210 to apply now."
)

SHORT_UNRELATED_TEXT = "Quick team sync scheduled at 4 PM in room 302."


def _create_pdf_bytes(text: str) -> bytes:
    """Helper to convert text into valid in-memory PDF bytes."""
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ---------------------------------------------------------------------------
# Unit Tests for RelevanceValidator
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "text,expected_code",
    [
        (BOOK_THIEF_TEXT, "UNRELATED_DOCUMENT"),
        (PHYSICS_PAPER_TEXT, "UNRELATED_DOCUMENT"),
        (ACADEMIC_ESSAY_TEXT, "UNRELATED_DOCUMENT"),
        (COMMERCIAL_INVOICE_TEXT, "UNRELATED_DOCUMENT"),
        (CERTIFICATE_TEXT, "UNRELATED_DOCUMENT"),
        (RESUME_TEXT, "UNRELATED_DOCUMENT"),
        (SHORT_UNRELATED_TEXT, "INSUFFICIENT_CONTENT"),
    ],
)
def test_relevance_validator_rejects_unrelated(text: str, expected_code: str) -> None:
    """Validate that non-recruitment documents are correctly identified and rejected."""
    is_valid, code, msg = RelevanceValidator.validate(text)
    assert not is_valid
    assert code == expected_code
    assert len(msg) > 0


@pytest.mark.parametrize(
    "text",
    [
        GENUINE_JOB_OFFER_TEXT,
        LEGITIMATE_INTERNSHIP_TEXT,
        SUSPICIOUS_JOB_OFFER_TEXT,
        SUSPICIOUS_INTERNSHIP_TEXT,
        INFORMAL_WHATSAPP_TEXT,
    ],
)
def test_relevance_validator_accepts_recruitment_content(text: str) -> None:
    """Validate that genuine, suspicious, and informal recruitment content is accepted."""
    is_valid, code, msg = RelevanceValidator.validate(text)
    assert is_valid
    assert code == ""
    assert msg == ""


# ---------------------------------------------------------------------------
# API Integration & Database Isolation Tests
# ---------------------------------------------------------------------------
def test_api_text_unrelated_document_rejected(client: TestClient, db_session: Session) -> None:
    """Ensure POST /api/analyze/text rejects unrelated documents with HTTP 422 and zero DB persistence."""
    initial_count = db_session.query(Analysis).count()

    response = client.post("/api/analyze/text", json={"text": BOOK_THIEF_TEXT})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    detail = data["detail"]
    if isinstance(detail, dict):
        assert detail.get("code") == "UNRELATED_DOCUMENT"
        assert "doesn't appear to be a job posting" in detail.get("message", "")

    # Confirm database isolation
    final_count = db_session.query(Analysis).count()
    assert final_count == initial_count


def test_api_text_resume_rejected(client: TestClient, db_session: Session) -> None:
    """Ensure candidate CVs/resumes are rejected with 422 and never stored in history."""
    initial_count = db_session.query(Analysis).count()

    response = client.post("/api/analyze/text", json={"text": RESUME_TEXT})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    detail = data["detail"]
    if isinstance(detail, dict):
        assert detail.get("code") == "UNRELATED_DOCUMENT"

    final_count = db_session.query(Analysis).count()
    assert final_count == initial_count


def test_api_text_insufficient_content_rejected(client: TestClient, db_session: Session) -> None:
    """Ensure short ambiguous text is rejected with INSUFFICIENT_CONTENT."""
    initial_count = db_session.query(Analysis).count()

    response = client.post("/api/analyze/text", json={"text": SHORT_UNRELATED_TEXT})
    assert response.status_code == 422
    data = response.json()
    detail = data["detail"]
    if isinstance(detail, dict):
        assert detail.get("code") == "INSUFFICIENT_CONTENT"

    final_count = db_session.query(Analysis).count()
    assert final_count == initial_count


def test_api_pdf_unrelated_rejected(client: TestClient, db_session: Session) -> None:
    """Ensure POST /api/analyze/file rejects unrelated PDF documents (The Book Thief) with HTTP 422."""
    initial_count = db_session.query(Analysis).count()
    pdf_bytes = _create_pdf_bytes(BOOK_THIEF_TEXT)

    files = {"file": ("the_book_thief.pdf", pdf_bytes, "application/pdf")}
    response = client.post("/api/analyze/file", files=files)
    assert response.status_code == 422
    detail = response.json()["detail"]
    if isinstance(detail, dict):
        assert detail.get("code") == "UNRELATED_DOCUMENT"

    final_count = db_session.query(Analysis).count()
    assert final_count == initial_count


def test_api_pdf_invoice_rejected(client: TestClient, db_session: Session) -> None:
    """Ensure commercial invoices uploaded as PDF are rejected with HTTP 422."""
    initial_count = db_session.query(Analysis).count()
    pdf_bytes = _create_pdf_bytes(COMMERCIAL_INVOICE_TEXT)

    files = {"file": ("tax_invoice.pdf", pdf_bytes, "application/pdf")}
    response = client.post("/api/analyze/file", files=files)
    assert response.status_code == 422
    detail = response.json()["detail"]
    if isinstance(detail, dict):
        assert detail.get("code") == "UNRELATED_DOCUMENT"

    final_count = db_session.query(Analysis).count()
    assert final_count == initial_count


def test_api_text_genuine_offer_accepted(client: TestClient, db_session: Session) -> None:
    """Ensure genuine job postings are accepted, analyzed, and persisted."""
    initial_count = db_session.query(Analysis).count()

    response = client.post("/api/analyze/text", json={"text": GENUINE_JOB_OFFER_TEXT})
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] == "LEGITIMATE"
    assert data["risk_level"] == "LOW"

    # Confirm database persistence
    final_count = db_session.query(Analysis).count()
    assert final_count == initial_count + 1


def test_api_text_suspicious_offer_accepted_for_scam_analysis(
    client: TestClient, db_session: Session
) -> None:
    """Ensure suspicious offers pass relevance check and are flagged as HIGH risk by scam engines."""
    initial_count = db_session.query(Analysis).count()

    response = client.post("/api/analyze/text", json={"text": SUSPICIOUS_JOB_OFFER_TEXT})
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] == "HIGH"
    assert len(data["detected_indicators"]) >= 1

    final_count = db_session.query(Analysis).count()
    assert final_count == initial_count + 1


def test_api_informal_whatsapp_accepted(client: TestClient, db_session: Session) -> None:
    """Ensure informal WhatsApp hiring messages pass relevance validation."""
    response = client.post("/api/analyze/text", json={"text": INFORMAL_WHATSAPP_TEXT})
    assert response.status_code == 200
    data = response.json()
    assert "risk_level" in data

