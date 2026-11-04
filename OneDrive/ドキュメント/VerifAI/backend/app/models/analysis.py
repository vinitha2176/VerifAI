"""SQLAlchemy model for recruitment risk analysis records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List
from sqlalchemy import DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class Analysis(Base):
    """Stores the evaluation history for analyzed job postings and offer letters."""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    submission_type: Mapped[str] = mapped_column(String(20), nullable=False, default="text")
    
    # Privacy-conscious representation of submitted text (preview + hash)
    submitted_text_preview: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_text_hash: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    text_length: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ML & Rule Assessment
    prediction: Mapped[str] = mapped_column(String(50), nullable=False)
    model_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rule_risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="LOW")

    # Structured details
    detected_indicators: Mapped[List[Any]] = mapped_column(JSON, nullable=False, default=list)
    recommendations: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<Analysis id={self.id} type={self.submission_type} "
            f"risk={self.risk_level} score={self.model_score:.2f}>"
        )

