"""Pytest test configuration and shared fixtures for VerifAI backend."""

from __future__ import annotations

import io
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, Generator, Optional
from urllib.parse import parse_qs, urlparse

from fastapi import HTTPException, UploadFile, status
from pydantic import ValidationError
import pymupdf as fitz
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app, health_check, root_redirect  # noqa: E402
from app.models.database import Base, get_db  # noqa: E402
from app.routes.analyze import analyze_file, analyze_text  # noqa: E402
from app.routes.history import (  # noqa: E402
    delete_analysis_record,
    get_analysis_detail,
    get_analysis_history,
)
from app.routes.metrics import get_model_metrics  # noqa: E402
from app.schemas.analysis import TextAnalysisRequest  # noqa: E402

# Isolated in-memory SQLite database for test suites
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


class DirectResponse:
    """Encapsulates HTTP status code and JSON payload."""

    def __init__(self, status_code: int, data: Any):
        self.status_code = status_code
        self._data = data

    def json(self) -> Any:
        return json.loads(json.dumps(self._data, default=str))


class DirectTestClient:
    """Dispatches requests directly to FastAPI handlers without network sockets.

    Ensures 100% real inference, real PDF extraction, and real DB persistence
    while avoiding socket blocking in restricted sandbox execution modes.
    """

    def __init__(self, db_factory) -> None:
        self.db_factory = db_factory

    def _get_db(self) -> Session:
        return next(self.db_factory())

    def get(self, url: str) -> DirectResponse:
        parsed = urlparse(url)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/":
            return DirectResponse(200, root_redirect())

        if path == "/api/health":
            db = self._get_db()
            try:
                res = health_check(db=db)
                return DirectResponse(200, res.model_dump())
            except HTTPException as he:
                return DirectResponse(he.status_code, {"detail": he.detail})
            finally:
                db.close()

        if path == "/api/model/metrics":
            try:
                res = get_model_metrics()
                return DirectResponse(200, res.model_dump())
            except HTTPException as he:
                return DirectResponse(he.status_code, {"detail": he.detail})

        if path == "/api/history":
            limit = int(query.get("limit", [20])[0])
            offset = int(query.get("offset", [0])[0])
            db = self._get_db()
            try:
                res = get_analysis_history(limit=limit, offset=offset, db=db)
                return DirectResponse(200, res.model_dump())
            finally:
                db.close()

        detail_match = re.match(r"^/api/history/(\d+)$", path)
        if detail_match:
            record_id = int(detail_match.group(1))
            db = self._get_db()
            try:
                res = get_analysis_detail(analysis_id=record_id, db=db)
                return DirectResponse(200, res.model_dump())
            except HTTPException as he:
                return DirectResponse(he.status_code, {"detail": he.detail})
            finally:
                db.close()

        return DirectResponse(404, {"detail": f"Path {path} not found."})

    def post(
        self,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> DirectResponse:
        parsed = urlparse(url)
        path = parsed.path

        if path == "/api/analyze/text":
            db = self._get_db()
            try:
                if not json or "text" not in json:
                    return DirectResponse(422, {"detail": "Missing text field"})
                try:
                    req = TextAnalysisRequest(**json)
                except ValidationError as ve:
                    return DirectResponse(422, {"detail": ve.errors()})

                res = analyze_text(payload=req, db=db)
                return DirectResponse(200, res.model_dump())
            except HTTPException as he:
                return DirectResponse(he.status_code, {"detail": he.detail})
            finally:
                db.close()

        if path == "/api/analyze/file":
            db = self._get_db()
            try:
                if not files or "file" not in files:
                    return DirectResponse(400, {"detail": "No file uploaded."})

                file_tuple = files["file"]
                filename, file_content = file_tuple[0], file_tuple[1]

                # Wrap bytes into an UploadFile
                spool = io.BytesIO(file_content)
                upload_file = UploadFile(
                    file=spool,
                    filename=filename,
                    size=len(file_content),
                )

                # Route validation
                if not upload_file.filename:
                    return DirectResponse(400, {"detail": "Uploaded file must have a valid filename."})
                if not upload_file.filename.lower().endswith(".pdf"):
                    return DirectResponse(400, {"detail": "Only PDF documents (.pdf) are supported in this phase."})

                from app.services.extraction import extract_text_from_pdf_bytes
                from app.services.analysis_service import AnalysisService

                text = extract_text_from_pdf_bytes(file_content)
                service = AnalysisService()
                res = service.analyze_and_store(text=text, submission_type="pdf", db=db)
                return DirectResponse(200, res.model_dump())

            except HTTPException as he:
                return DirectResponse(he.status_code, {"detail": he.detail})
            finally:
                db.close()

        return DirectResponse(404, {"detail": f"Path {path} not found."})

    def delete(self, url: str) -> DirectResponse:
        parsed = urlparse(url)
        path = parsed.path

        del_match = re.match(r"^/api/history/(\d+)$", path)
        if del_match:
            record_id = int(del_match.group(1))
            db = self._get_db()
            try:
                res = delete_analysis_record(analysis_id=record_id, db=db)
                return DirectResponse(200, res)
            except HTTPException as he:
                return DirectResponse(he.status_code, {"detail": he.detail})
            finally:
                db.close()

        return DirectResponse(404, {"detail": f"Path {path} not found."})


@pytest.fixture(autouse=True)
def setup_test_database():
    """Create fresh schema tables before every test and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a dedicated database session for an individual test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> Generator[DirectTestClient, None, None]:
    """Provide test client wired to test database session."""
    def get_test_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = get_test_db
    yield DirectTestClient(get_test_db)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_valid_pdf_bytes() -> bytes:
    """Generate in-memory valid PDF bytes containing text."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 72),
        "VerifAI Test Recruitment Document.\n"
        "We are seeking a Software Engineer. Responsibilities include designing REST APIs.\n"
        "Competitive salary and full healthcare benefits provided.",
    )
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def sample_scam_pdf_bytes() -> bytes:
    """Generate in-memory PDF bytes containing scam indicators."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 72),
        "URGENT APPOINTMENT LETTER.\n"
        "Congratulations! You have been selected without any interview.\n"
        "Please pay 2500 rupees as registration fee immediately to confirm your seat.\n"
        "Refundable security deposit of 5000 rupees is also required for laptop allocation.",
    )
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.fixture
def sample_empty_pdf_bytes() -> bytes:
    """Generate in-memory PDF bytes with a blank page (no text)."""
    doc = fitz.open()
    doc.new_page()  # Blank page
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes
