"""Unified analysis coordination service for VerifAI.

Combines ML inference, contextual rule engine evaluation, composite risk scoring,
tailored recommendations generation, and persistent database storage.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Tuple
from sqlalchemy.orm import Session

from app.models.analysis import Analysis
from app.schemas.analysis import (
    AnalysisResponse,
    DetectedIndicator,
    VERIFAI_DISCLAIMER,
)
from app.services.prediction import PredictionService
from app.services.relevance_service import validate_recruitment_relevance
from app.services.risk_engine import RiskEngine

logger = logging.getLogger("VerifAI.Services.AnalysisService")


class AnalysisService:
    """Coordinates risk assessment pipeline across ML, rules, and database."""

    def __init__(
        self,
        prediction_service: PredictionService | None = None,
        risk_engine: RiskEngine | None = None,
    ) -> None:
        self.prediction_service = prediction_service or PredictionService.get_instance()
        self.risk_engine = risk_engine or RiskEngine()

    @staticmethod
    def compute_risk_level(
        model_score: float,
        rule_score: float,
        detected_indicators: Sequence[DetectedIndicator] | None = None,
    ) -> str:
        """Determine tripartite risk classification (LOW, MODERATE, HIGH).

        Incorporates indicator severity count, rule score, and calibrated ML score.
        Critical indicators (such as registration fees, training fees, or sensitive document demands)
        immediately warrant a HIGH risk classification to protect applicants from acute extortion.

        Args:
            model_score: Calibrated ML score (0.0 to 1.0).
            rule_score: Deterministic rule-based score (0.0 to 1.0).
            detected_indicators: Optional sequence of DetectedIndicator instances.

        Returns:
            "LOW", "MODERATE", or "HIGH".
        """
        indicators = detected_indicators or []
        critical_count = sum(1 for ind in indicators if ind.severity.upper() == "CRITICAL")
        high_count = sum(1 for ind in indicators if ind.severity.upper() == "HIGH")
        medium_count = sum(1 for ind in indicators if ind.severity.upper() == "MEDIUM")

        # 1. Critical risk: Any CRITICAL extortion indicator (registration fee, mandatory training charge,
        # sensitive document demands) or multiple HIGH indicators or strong rule/ML score
        if (
            critical_count >= 1
            or high_count >= 2
            or rule_score >= 0.40
            or model_score >= 0.65
            or (model_score >= 0.40 and high_count >= 1)
        ):
            return "HIGH"

        # 2. Moderate risk: Single HIGH indicator, medium severity indicators, or moderate risk scores
        if (
            high_count == 1
            or medium_count >= 1
            or rule_score >= 0.20
            or model_score >= 0.35
        ):
            return "MODERATE"

        # 3. Safe baseline: No indicators and low ML model score
        return "LOW"

    @staticmethod
    def generate_recommendations(
        risk_level: str,
        detected_indicators: List[DetectedIndicator],
    ) -> List[str]:
        """Generate targeted, actionable guidance based on detected risk signals.

        Args:
            risk_level: Overall composite risk classification.
            detected_indicators: Indicators flagged by the rule engine.

        Returns:
            List of concrete verification actions for the applicant.
        """
        recommendations: List[str] = []
        indicator_names = {ind.indicator_name for ind in detected_indicators}

        # Specific recommendations for identified indicators
        if any("Fee" in name or "Payment" in name for name in indicator_names):
            recommendations.append(
                "Never send money or pay upfront fees for job registration, interviews, or application processing. "
                "Legitimate employers do not transfer recruitment overhead costs to candidates."
            )

        if any("Training" in name for name in indicator_names):
            recommendations.append(
                "Be cautious of mandatory paid training, onboarding packages, or certification fees required as a prerequisite. "
                "Authentic employers invest in employee training at company expense."
            )

        if any("Deposit" in name for name in indicator_names):
            recommendations.append(
                "Do not deposit funds for company assets or laptops. Authentic organisations provide necessary "
                "equipment directly without requiring candidate collateral."
            )

        if any("Guaranteed" in name or "Without Interview" in name for name in indicator_names):
            recommendations.append(
                "Treat guaranteed job offers without technical interviews or background validation with skepticism. "
                "Legitimate hiring processes involve thorough multi-stage assessments."
            )

        if any("Urgent" in name or "Deadline" in name for name in indicator_names):
            recommendations.append(
                "Do not yield to artificial urgency or short deadlines (such as 2-hour or same-day payment windows). "
                "Scammers create false panic to prevent candidates from verifying claims."
            )

        if any("Sensitive" in name or "Financial" in name for name in indicator_names):
            recommendations.append(
                "Never disclose banking passwords, credit card details, OTPs, or send copies of identity documents (Aadhaar, PAN, passport) "
                "over informal messaging apps like Telegram or WhatsApp. Submit verification documents only via secure corporate portals."
            )

        if any("Communication Channel" in name for name in indicator_names):
            recommendations.append(
                "Insist on official corporate email communication (e.g. name@company.com). Be wary of recruiters "
                "operating exclusively through personal Telegram handles or WhatsApp numbers."
            )

        # Baseline diligence checks
        if risk_level in ("HIGH", "MODERATE"):
            recommendations.append(
                "Cross-check the recruitment notice on the organization's official career portal or official LinkedIn page."
            )
            recommendations.append(
                "Contact the company's official reception or HR department via independently verified telephone numbers."
            )
        else:
            recommendations.append(
                "Standard diligence recommended: Review employment terms, role expectations, and formal offer letters."
            )

        return recommendations

    def analyze_and_store(
        self,
        text: str,
        submission_type: str,
        db: Session,
    ) -> AnalysisResponse:
        """Run the end-to-end analysis pipeline and persist the result.

        Args:
            text: Extracted or submitted recruitment text.
            submission_type: 'text' or 'pdf'.
            db: Active SQLAlchemy database session.

        Returns:
            AnalysisResponse schema with comprehensive results and disclaimer.
        """
        # Step 0: Validate recruitment relevance before ML inference or risk scoring
        validate_recruitment_relevance(text)

        # Step 1: Execute genuine ML inference
        prediction_label, model_score = self.prediction_service.predict(text)

        # Step 2: Execute independent rule-based detection
        rule_score, indicators, evidence_list = self.risk_engine.evaluate(text)

        # Step 3: Compute composite risk tier
        risk_level = self.compute_risk_level(
            model_score=model_score,
            rule_score=rule_score,
            detected_indicators=indicators,
        )

        # Step 4: Formulate actionable recommendations
        recommendations = self.generate_recommendations(
            risk_level=risk_level,
            detected_indicators=indicators,
        )

        # Step 5: Prepare privacy-conscious text preview & hash
        text_preview = text[:400] + ("..." if len(text) > 400 else "")
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        # Step 6: Persist in SQLite
        serialized_indicators = [ind.model_dump() for ind in indicators]

        db_record = Analysis(
            submission_type=submission_type,
            submitted_text_preview=text_preview,
            submitted_text_hash=text_hash,
            text_length=len(text),
            prediction=prediction_label,
            model_score=model_score,
            rule_risk_score=rule_score,
            risk_level=risk_level,
            detected_indicators=serialized_indicators,
            recommendations=recommendations,
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)

        logger.info(
            "Analysis complete [ID=%d, Type=%s, Risk=%s, ML_Score=%.2f, Rule_Score=%.2f]",
            db_record.id,
            submission_type,
            risk_level,
            model_score,
            rule_score,
        )

        return AnalysisResponse(
            id=db_record.id,
            submission_type=db_record.submission_type,
            prediction=db_record.prediction,
            model_score=db_record.model_score,
            rule_risk_score=db_record.rule_risk_score,
            risk_level=db_record.risk_level,
            detected_indicators=indicators,
            evidence=evidence_list,
            recommendations=recommendations,
            disclaimer=VERIFAI_DISCLAIMER,
            created_at=db_record.created_at,
        )
