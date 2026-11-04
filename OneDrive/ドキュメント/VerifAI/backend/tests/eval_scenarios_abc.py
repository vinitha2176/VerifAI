"""Audit script to run the exact Test A, Test B, and Test C scenarios."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pymupdf as fitz
from app.services.extraction import extract_text_from_pdf_bytes
from app.services.risk_engine import RiskEngine
from app.services.analysis_service import AnalysisService

risk_engine = RiskEngine()
analysis_service = AnalysisService()

# Test A (text submission)
text_a = (
    "Apex Technologies - Junior Software Developer. "
    "We are pleased to inform you of your guaranteed selection without an interview for the Junior Software Developer position. "
    "To confirm your acceptance, a refundable registration fee of ₹2,500 must be paid immediately. "
    "Immediate payment requirement applies to secure your placement in this cohort."
)

# Test B (PDF submission)
raw_text_b = (
    "Global Infotech Internship Program. "
    "Congratulations! You have received guaranteed selection without an interview for our 2026 Developer Internship. "
    "A non-refundable onboarding charge of ₹1,999 is required to initiate your profile. "
    "Additionally, a mandatory ₹4,000 training charge must be paid for the induction module. "
    "Please submit your identity documents and bank details via Telegram to our HR coordinator (@InfotechHR). "
    "This offer expires within a 2-hour deadline, so payment must be transferred immediately."
)

doc_b = fitz.open()
page_b = doc_b.new_page()
rect_b = fitz.Rect(50, 50, 550, 750)
page_b.insert_textbox(rect_b, raw_text_b)
pdf_bytes_b = doc_b.tobytes()
doc_b.close()
text_b = extract_text_from_pdf_bytes(pdf_bytes_b)

# Test C (PDF submission)
raw_text_c = (
    "Acme Systems - Summer Engineering Internship. "
    "We invite applications for our competitive three-month internship program in Software Engineering. "
    "Selected interns receive a ₹10,000 monthly stipend and work directly with senior architects. "
    "Candidates must complete a technical interview and practical assessment. "
    "No registration fee, security deposit, or application fee is required at any point in our hiring process. "
    "Apply via our official corporate careers portal."
)

doc_c = fitz.open()
page_c = doc_c.new_page()
rect_c = fitz.Rect(50, 50, 550, 750)
page_c.insert_textbox(rect_c, raw_text_c)
pdf_bytes_c = doc_c.tobytes()
doc_c.close()
text_c = extract_text_from_pdf_bytes(pdf_bytes_c)

scenarios = [
    ("Scenario A: Suspicious Job Offer (Text)", "text", text_a),
    ("Scenario B: Suspicious Internship Advertisement (PDF)", "pdf", text_b),
    ("Scenario C: Lower-Risk Internship Offer (PDF)", "pdf", text_c),
]

for label, sub_type, doc_text in scenarios:
    ml_pred, ml_score = analysis_service.prediction_service.predict(doc_text)
    rule_score, indicators, evidence_list = risk_engine.evaluate(doc_text)
    risk_level = analysis_service.compute_risk_level(ml_score, rule_score, indicators)
    recs = analysis_service.generate_recommendations(risk_level, indicators)

    print("=" * 80)
    print(label)
    print("=" * 80)
    print(f"Submission Type: {sub_type}")
    print(f"Extracted Text:\n{doc_text.strip()}\n")
    print(f"ML Prediction: {ml_pred}")
    print(f"ML Calibrated Score: {ml_score:.4f} ({ml_score * 100:.2f}%)")
    print(f"Rule Engine Risk Score: {rule_score:.4f} ({rule_score * 100:.2f}%)")
    print(f"Composite Risk Level: {risk_level}")
    print(f"Detected Indicators Count: {len(indicators)}")
    for i, ind in enumerate(indicators, 1):
        print(f"  {i}. [{ind.severity}] {ind.indicator_name}")
        print(f"     Matched Evidence: '{ind.matched_evidence}'")
        print(f"     Explanation: {ind.explanation}")
    print("Actionable Recommendations:")
    for i, r in enumerate(recs, 1):
        print(f"  {i}. {r}")
    print()

