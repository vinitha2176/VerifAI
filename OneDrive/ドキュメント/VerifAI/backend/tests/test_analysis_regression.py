"""Comprehensive regression test suite for VerifAI Analysis Engine.

Validates the fix for:
- Test A: Suspicious job offer (text) -> High risk, multi-indicator detection
- Test B: Suspicious internship advertisement (PDF) -> High risk, multi-indicator detection
- Test C: Lower-risk internship offer (PDF) -> Low risk, zero false positive on negated fees/deposits
- 35-sample benchmark suite covering Suspicious, Legitimate, Fee Negation, Multi-Flag, and Edge Cases
"""

from __future__ import annotations

import io
from typing import Dict, List, NamedTuple
import pymupdf as fitz
import pytest

from app.schemas.analysis import AnalysisResponse


class BenchmarkCase(NamedTuple):
    id: str
    category: str
    ground_truth: str  # "SUSPICIOUS" or "LEGITIMATE"
    expected_risk: str  # "HIGH" or "LOW"
    text: str
    expected_indicators: List[str]


# ---------------------------------------------------------------------------
# Test Scenarios A, B, and C
# ---------------------------------------------------------------------------
TEXT_SCENARIO_A = (
    "Apex Technologies - Junior Software Developer. "
    "We are pleased to inform you of your guaranteed selection without an interview for the Junior Software Developer position. "
    "To confirm your acceptance, a refundable registration fee of ₹2,500 must be paid immediately. "
    "Immediate payment requirement applies to secure your placement in this cohort."
)

TEXT_SCENARIO_B = (
    "Global Infotech Internship Program. "
    "Congratulations! You have received guaranteed selection without an interview for our 2026 Developer Internship. "
    "A non-refundable onboarding charge of ₹1,999 is required to initiate your profile. "
    "Additionally, a mandatory ₹4,000 training charge must be paid for the induction module. "
    "Please submit your identity documents and bank details via Telegram to our HR coordinator (@InfotechHR). "
    "This offer expires within a 2-hour deadline, so payment must be transferred immediately."
)

TEXT_SCENARIO_C = (
    "Acme Systems - Summer Engineering Internship. "
    "We invite applications for our competitive three-month internship program in Software Engineering. "
    "Selected interns receive a ₹10,000 monthly stipend and work directly with senior architects. "
    "Candidates must complete a technical interview and practical assessment. "
    "No registration fee, security deposit, or application fee is required at any point in our hiring process. "
    "Apply via our official corporate careers portal."
)


def _text_to_pdf_bytes(text: str) -> bytes:
    """Helper to generate in-memory PDF bytes from raw text with proper textbox wrapping."""
    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(50, 50, 550, 750)
    page.insert_textbox(rect, text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ---------------------------------------------------------------------------
# 35 Benchmark Cases
# ---------------------------------------------------------------------------
BENCHMARK_CASES: List[BenchmarkCase] = [
    # 10 Suspicious
    BenchmarkCase(
        "SUSP_01_TEST_A", "Suspicious", "SUSPICIOUS", "HIGH",
        TEXT_SCENARIO_A,
        ["Registration / Onboarding Fee Demand", "Guaranteed Selection Without Interview", "Urgent Payment Deadline Pressure"]
    ),
    BenchmarkCase(
        "SUSP_02_TEST_B", "Suspicious", "SUSPICIOUS", "HIGH",
        TEXT_SCENARIO_B,
        ["Registration / Onboarding Fee Demand", "Mandatory Paid Training / Training Charge", "Guaranteed Selection Without Interview", "Urgent Payment Deadline Pressure", "Premature Sensitive Financial Document Request"]
    ),
    BenchmarkCase(
        "SUSP_03_EQUIPMENT_DEPOSIT", "Suspicious", "SUSPICIOUS", "HIGH",
        (
            "Remote Customer Service Representative. Welcome to Global Logistics Ltd. "
            "Before dispatching your company Apple MacBook Pro and workstation, candidate must remit a refundable equipment deposit of ₹15,000. "
            "Refundable security deposit will be credited back on the first monthly payroll."
        ),
        ["Security / Equipment Deposit Demand"]
    ),
    BenchmarkCase(
        "SUSP_04_DIRECT_APPOINTMENT_UPI", "Suspicious", "SUSPICIOUS", "HIGH",
        (
            "Offer of Appointment - Business Analyst. "
            "You have been selected without any interview based on your resume profile. Direct appointment without interview is confirmed. "
            "Please transfer the processing fee of ₹1,500 via UPI to our HR desk immediately."
        ),
        ["Guaranteed Selection Without Interview", "Application / Processing Fee Requirement", "Urgent Payment Deadline Pressure"]
    ),
    BenchmarkCase(
        "SUSP_05_PORTAL_ACCESS_FEE", "Suspicious", "SUSPICIOUS", "HIGH",
        (
            "Online Data Entry Executive. Start working from home and earn guaranteed ₹30,000 per month. "
            "An initial portal administration fee of ₹3,000 is required to activate your employee dashboard and allocate project data."
        ),
        ["Application / Processing Fee Requirement"]
    ),
    BenchmarkCase(
        "SUSP_06_MANDATORY_TRAINING", "Suspicious", "SUSPICIOUS", "HIGH",
        (
            "Full Stack Developer Trainee. Candidates must undergo our proprietary 4-week industry curriculum. "
            "A mandatory ₹6,500 training charge must be deposited prior to joining date. Training fee is non-refundable."
        ),
        ["Mandatory Paid Training / Training Charge"]
    ),
    BenchmarkCase(
        "SUSP_07_URGENT_DEADLINE", "Suspicious", "SUSPICIOUS", "HIGH",
        (
            "Urgent Hiring Notice: Backend Engineer. We have 1 remaining slot for our development center. "
            "You must pay registration fee of ₹2,000 within a 2-hour deadline today itself to secure your seat. "
            "Immediate payment requirement is strictly enforced."
        ),
        ["Registration / Onboarding Fee Demand", "Urgent Payment Deadline Pressure"]
    ),
    BenchmarkCase(
        "SUSP_08_DOCS_TELEGRAM", "Suspicious", "SUSPICIOUS", "HIGH",
        (
            "Digital Marketing Specialist. Congratulations on your direct joining without an interview! "
            "To finalize your documentation, please send your identity documents and bank details via WhatsApp to our hiring coordinator."
        ),
        ["Guaranteed Selection Without Interview", "Premature Sensitive Financial Document Request"]
    ),
    BenchmarkCase(
        "SUSP_09_SCREENING_FEE", "Suspicious", "SUSPICIOUS", "HIGH",
        (
            "Executive Assistant Position. Before releasing your final contract, an external screening fee of ₹2,200 must be transferred to our partner account. "
            "Candidates must pay the verification fee before joining."
        ),
        ["Application / Processing Fee Requirement"]
    ),
    BenchmarkCase(
        "SUSP_10_HIGH_EARNINGS", "Suspicious", "SUSPICIOUS", "HIGH",
        (
            "Part-Time Typing Specialist. Earn ₹2,500 daily for typing 5 pages per day. Zero qualifications required. "
            "Immediate enrollment fee of ₹1,200 is mandatory to receive your first assignment kit."
        ),
        ["Registration / Onboarding Fee Demand"]
    ),

    # 10 Legitimate
    BenchmarkCase(
        "LEGIT_01_FRONTEND", "Legitimate", "LEGITIMATE", "LOW",
        (
            "Senior Frontend Engineer at CloudScale Technologies. We are looking for an experienced engineer skilled in React, TypeScript, and modern CSS. "
            "You will lead UI architecture across our core SaaS products. Responsibilities include mentoring junior engineers and optimizing page performance. "
            "Minimum 5 years of production experience required. Competitive annual package with health insurance and provident fund. "
            "Selection involves an initial recruiter phone screen, a 60-minute technical coding interview, a system architecture discussion, and a culture fit conversation."
        ),
        []
    ),
    BenchmarkCase(
        "LEGIT_02_PRODUCT_MGR", "Legitimate", "LEGITIMATE", "LOW",
        (
            "Product Manager - FinTech Platform. Metro Financial Services is hiring a Product Manager to guide our next-generation payments product. "
            "The ideal candidate has 3+ years in product discovery, user journey mapping, and cross-functional leadership. "
            "Interview process comprises a recruiter screen, product case study presentation, and interview rounds with engineering and design leads. "
            "We provide comprehensive medical insurance, annual learning stipends, and flexible hybrid working arrangements."
        ),
        []
    ),
    BenchmarkCase(
        "LEGIT_03_DEVOPS", "Legitimate", "LEGITIMATE", "LOW",
        (
            "DevOps / Infrastructure Engineer at DataMesh Networks. We seek a DevOps Engineer proficient with Kubernetes, Terraform, Docker, and AWS cloud architecture. "
            "Candidate will maintain CI/CD deployment pipelines, manage observability via Prometheus and Grafana, and ensure system uptime. "
            "Candidates undergo an architectural review and technical deep dive interview. The company provides competitive compensation and standard benefits."
        ),
        []
    ),
    BenchmarkCase(
        "LEGIT_04_DATA_ANALYST", "Legitimate", "LEGITIMATE", "LOW",
        (
            "Business Intelligence & Data Analyst. Retail Insights Corp is expanding its analytics division. "
            "Requirements: Strong proficiency in SQL, Python data libraries (pandas, numpy), and visualization tools (Tableau, PowerBI). "
            "The candidate will collaborate with supply chain managers to optimize inventory logistics. "
            "Candidates must complete a take-home SQL practical assessment followed by a technical panel interview."
        ),
        []
    ),
    BenchmarkCase(
        "LEGIT_05_SUPPORT", "Legitimate", "LEGITIMATE", "LOW",
        (
            "Customer Success Specialist at BrightDesk Software. You will support enterprise customers across email and live chat, "
            "troubleshooting product configuration issues and documenting recurring user feedback. "
            "Shift timings include rotational morning and evening schedules. "
            "Comprehensive 3-week onboarding training is provided free of cost by the company. "
            "Annual salary ₹4,50,000 with quarterly performance incentives."
        ),
        []
    ),
    BenchmarkCase(
        "LEGIT_06_QA_AUTOMATION", "Legitimate", "LEGITIMATE", "LOW",
        (
            "Quality Assurance Automation Engineer at SecureApp Ltd. Join our test engineering squad to build automated test frameworks using Playwright and pytest. "
            "Requirements include 2+ years experience in automated regression testing and API testing. "
            "Selection process consists of a coding challenge, technical interview, and managerial discussion. "
            "Company furnishes all computer hardware and development workstations."
        ),
        []
    ),
    BenchmarkCase(
        "LEGIT_07_MARKETING", "Legitimate", "LEGITIMATE", "LOW",
        (
            "Content Marketing Strategist at Apex Media. Responsible for producing technical whitepapers, case studies, and corporate blog content. "
            "Requires portfolio submission demonstrating published B2B articles. "
            "Interview process consists of an editorial evaluation and an interview with the VP of Marketing."
        ),
        []
    ),
    BenchmarkCase(
        "LEGIT_08_SYSADMIN", "Legitimate", "LEGITIMATE", "LOW",
        (
            "Linux Systems Administrator at Horizon Cloud. Manage enterprise Linux servers, perform routine patching, "
            "monitor network security protocols, and support database backups. Qualifications include RHCE certification or equivalent practical expertise. "
            "Candidate must complete two rounds of technical interviews."
        ),
        []
    ),
    BenchmarkCase(
        "LEGIT_09_DESIGNER", "Legitimate", "LEGITIMATE", "LOW",
        (
            "UI/UX Visual Designer at StudioNine. We are seeking a creative designer with proficiency in Figma, design systems, and typography. "
            "Candidates must submit a design portfolio showcasing wireframes, interactive prototypes, and web design projects. "
            "Multi-stage assessment includes portfolio walkthrough and collaboration interview."
        ),
        []
    ),
    BenchmarkCase(
        "LEGIT_10_ARCHITECT", "Legitimate", "LEGITIMATE", "LOW",
        (
            "Enterprise Solutions Architect at PrimeCloud Inc. Partner with enterprise clients to design fault-tolerant, scalable cloud infrastructure. "
            "Minimum 8 years in IT with active AWS or Azure Solutions Architect professional certification. "
            "Selection involves a panel presentation and stakeholder discussions. Top-tier compensation and relocation support."
        ),
        []
    ),

    # 5 Fee Negation
    BenchmarkCase(
        "NEG_01_TEST_C", "Fee Negation", "LEGITIMATE", "LOW",
        TEXT_SCENARIO_C,
        []
    ),
    BenchmarkCase(
        "NEG_02_SECURITY_DEPOSIT", "Fee Negation", "LEGITIMATE", "LOW",
        (
            "Remote Full Stack Developer at OpenSource Technologies. Join our distributed team building web applications. "
            "Candidates are not required to pay any security deposit or equipment fees. "
            "The company provides all laptops and work accessories free of cost directly to your residence upon joining."
        ),
        []
    ),
    BenchmarkCase(
        "NEG_03_NO_APPLICATION_FEES", "Fee Negation", "LEGITIMATE", "LOW",
        (
            "Graduate Engineer Trainee - Nexus Industries. We are hiring fresh engineering graduates for our core plant operations. "
            "There are no registration fees, interview charges, or processing costs at any stage of our recruitment process. "
            "All interviews are conducted at our regional offices."
        ),
        []
    ),
    BenchmarkCase(
        "NEG_04_BEWARE_SCAMS", "Fee Negation", "LEGITIMATE", "LOW",
        (
            "Careers at Sterling Health Systems - Clinical Research Associate. "
            "Please note that our company never charges any application fee, registration cost, or security deposit. "
            "We do not ask candidates to pay money for interviews or training. Report any unauthorized person asking for payment in our name."
        ),
        []
    ),
    BenchmarkCase(
        "NEG_05_ZERO_COST", "Fee Negation", "LEGITIMATE", "LOW",
        (
            "Associate Software Engineer at Global Logic Solutions. "
            "Applicants will never be asked for application fees, training charges, or caution deposits. "
            "Our entire selection process is completely free of cost and strictly merit-based. Technical interviews and HR evaluations are mandatory."
        ),
        []
    ),

    # 5 Multi-Flag
    BenchmarkCase(
        "MULTI_01_EXTORTION_COMBO", "Multi-Flag", "SUSPICIOUS", "HIGH",
        (
            "Software Developer Trainee. Congratulations, guaranteed selection without an interview is confirmed. "
            "Candidates must pay a registration fee of ₹2,000 immediately within a 2-hour deadline to reserve seat. "
            "Transfer funds to our recruitment desk via WhatsApp coordinator."
        ),
        ["Registration / Onboarding Fee Demand", "Guaranteed Selection Without Interview", "Urgent Payment Deadline Pressure"]
    ),
    BenchmarkCase(
        "MULTI_02_DEPOSIT_AND_DOCS", "Multi-Flag", "SUSPICIOUS", "HIGH",
        (
            "Remote Data Specialist. Offer of appointment issued without interview. "
            "Please deposit a refundable security deposit of ₹8,000 for work equipment. "
            "Additionally, remit an application processing fee of ₹1,000. "
            "Send your identity documents and bank details via Telegram to proceed."
        ),
        ["Security / Equipment Deposit Demand", "Application / Processing Fee Requirement", "Guaranteed Selection Without Interview", "Premature Sensitive Financial Document Request"]
    ),
    BenchmarkCase(
        "MULTI_03_TRAINING_AND_PRESSURE", "Multi-Flag", "SUSPICIOUS", "HIGH",
        (
            "Python Developer Internship. Immediate direct appointment without any assessment. "
            "A mandatory ₹5,000 training charge is required for the project orientation kit. "
            "Immediate payment requirement applies and must be transferred today."
        ),
        ["Mandatory Paid Training / Training Charge", "Guaranteed Selection Without Interview", "Urgent Payment Deadline Pressure"]
    ),
    BenchmarkCase(
        "MULTI_04_ONBOARDING_PURCHASE", "Multi-Flag", "SUSPICIOUS", "HIGH",
        (
            "Virtual Operations Analyst. You are selected without an interview. "
            "A non-refundable onboarding fee of ₹2,500 must be paid before joining. "
            "Candidate must purchase software license before joining through our designated vendor. "
            "Official communication conducted via Telegram."
        ),
        ["Registration / Onboarding Fee Demand", "Compulsory Payment or Purchase Before Joining", "Guaranteed Selection Without Interview"]
    ),
    BenchmarkCase(
        "MULTI_05_SCREENING_SURRENDER", "Multi-Flag", "SUSPICIOUS", "HIGH",
        (
            "Regional Field Executive. Urgent hiring: selected candidates must pay screening fee of ₹1,800 immediately. "
            "You must surrender original degree certificates before joining. "
            "Urgent payment required within 2 hours."
        ),
        ["Application / Processing Fee Requirement", "Premature Sensitive Financial Document Request", "Urgent Payment Deadline Pressure"]
    ),

    # 5 Safe Edge Cases
    BenchmarkCase(
        "EDGE_01_REIMBURSEMENT", "Edge Case", "LEGITIMATE", "LOW",
        (
            "Senior Consultant - Strategy & Operations at McKinsey & Partners. "
            "Candidates traveling from out of station for the final partner round will receive travel expense reimbursement up to ₹5,000. "
            "Submit original travel tickets to the reception desk for company reimbursement."
        ),
        []
    ),
    BenchmarkCase(
        "EDGE_02_TRAINING_MENTION", "Edge Case", "LEGITIMATE", "LOW",
        (
            "Cloud Engineering Apprenticeship. The 6-month curriculum includes intensive hands-on training in microservices, "
            "followed by deployment to enterprise client teams. "
            "Mentorship is provided by principal architects throughout the fellowship."
        ),
        []
    ),
    BenchmarkCase(
        "EDGE_03_JOINING_BONUS", "Edge Case", "LEGITIMATE", "LOW",
        (
            "Staff Site Reliability Engineer. We offer a competitive base compensation of ₹35,00,000 alongside a joining bonus of ₹3,00,000 "
            "payable upon completion of 90 days. Comprehensive health benefits included."
        ),
        []
    ),
    BenchmarkCase(
        "EDGE_04_PHYSICAL_ID", "Edge Case", "LEGITIMATE", "LOW",
        (
            "Systems Engineer - Onsite Client Facility. For security clearance at the client tech park, "
            "candidates attending the on-site interview must present government photo identity at the reception gate. "
            "Valid items include Passport or Driver License."
        ),
        []
    ),
    BenchmarkCase(
        "EDGE_05_EQUIPMENT_PROVISION", "Edge Case", "LEGITIMATE", "LOW",
        (
            "Senior Frontend Developer. We support remote work across India. "
            "Every new team member receives a company-provided M3 MacBook Pro, 4K monitor, and ergonomics allowance upon joining."
        ),
        []
    ),
]


# ---------------------------------------------------------------------------
# Test Functions
# ---------------------------------------------------------------------------
def test_scenario_a_suspicious_job_text_integration(client):
    """Test A (Suspicious job offer): Verifies HIGH risk and multi-indicator detection."""
    response = client.post("/api/analyze/text", json={"text": TEXT_SCENARIO_A})
    assert response.status_code == 200
    data = response.json()

    assert data["risk_level"] == "HIGH"
    detected_names = [ind["indicator_name"] for ind in data["detected_indicators"]]

    # Verify all 3 independent red flags are detected
    assert "Registration / Onboarding Fee Demand" in detected_names
    assert "Guaranteed Selection Without Interview" in detected_names
    assert "Urgent Payment Deadline Pressure" in detected_names
    assert len(data["detected_indicators"]) == 3

    # Verify clean, exact evidence extraction (not whole document)
    for ind in data["detected_indicators"]:
        assert len(ind["matched_evidence"]) > 0
        assert len(ind["matched_evidence"]) < len(TEXT_SCENARIO_A)
        assert ind["matched_evidence"] in TEXT_SCENARIO_A

    # Verify actionable recommendations match detected signals
    rec_text = " ".join(data["recommendations"]).lower()
    assert "fee" in rec_text
    assert "guaranteed" in rec_text
    assert "urgency" in rec_text or "deadline" in rec_text


def test_scenario_b_suspicious_internship_pdf_integration(client):
    """Test B (Suspicious internship offer): Verifies PDF extraction, HIGH risk, and 5 red flags."""
    pdf_bytes = _text_to_pdf_bytes(TEXT_SCENARIO_B)
    response = client.post(
        "/api/analyze/file",
        files={"file": ("internship_offer.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["risk_level"] == "HIGH"
    assert data["submission_type"] == "pdf"

    detected_names = [ind["indicator_name"] for ind in data["detected_indicators"]]
    assert "Registration / Onboarding Fee Demand" in detected_names
    assert "Mandatory Paid Training / Training Charge" in detected_names
    assert "Guaranteed Selection Without Interview" in detected_names
    assert "Urgent Payment Deadline Pressure" in detected_names
    assert "Premature Sensitive Financial Document Request" in detected_names
    assert len(data["detected_indicators"]) >= 5

    # Verify clean evidence clauses
    evidence_list = data["evidence"]
    assert len(evidence_list) >= 5
    for ev in evidence_list:
        assert len(ev) < len(TEXT_SCENARIO_B)


def test_scenario_c_legitimate_internship_pdf_integration(client):
    """Test C (Lower-risk internship offer): Verifies zero false positive on fee/deposit negation."""
    pdf_bytes = _text_to_pdf_bytes(TEXT_SCENARIO_C)
    response = client.post(
        "/api/analyze/file",
        files={"file": ("legitimate_internship.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()

    # Must be classified as LOW risk with ZERO red flags triggered
    assert data["risk_level"] == "LOW"
    assert data["detected_indicators"] == []
    assert data["evidence"] == []

    # Verify no false positive for Security Deposit or Fee
    detected_names = [ind["indicator_name"] for ind in data["detected_indicators"]]
    assert "Security / Equipment Deposit Demand" not in detected_names
    assert "Registration / Onboarding Fee Demand" not in detected_names
    assert "Application / Processing Fee Requirement" not in detected_names

    # Diligence recommendations provided without scam alarmism
    assert len(data["recommendations"]) > 0
    assert "Standard diligence" in data["recommendations"][0]


def test_full_35_sample_regression_matrix(client):
    """Evaluates all 35 test cases through the API and validates 100% precision and recall."""
    tp = 0
    tn = 0
    fp = 0
    fn = 0

    for tc in BENCHMARK_CASES:
        res = client.post("/api/analyze/text", json={"text": tc.text})
        assert res.status_code == 200, f"Analysis failed for {tc.id}"
        data = res.json()

        risk_level = data["risk_level"]
        indicators = data["detected_indicators"]
        detected_names = {ind["indicator_name"] for ind in indicators}

        is_scam = tc.ground_truth == "SUSPICIOUS"
        predicted_high = (risk_level == "HIGH")

        if is_scam:
            if predicted_high:
                tp += 1
            else:
                fn += 1
                pytest.fail(f"False Negative for {tc.id}: expected HIGH, got {risk_level}")
        else:
            if predicted_high or any("Fee" in n or "Deposit" in n for n in detected_names):
                fp += 1
                pytest.fail(f"False Positive for {tc.id}: expected LOW, got {risk_level} with {detected_names}")
            else:
                tn += 1

    total = len(BENCHMARK_CASES)
    assert total == 35
    assert tp == 15, f"Expected 15 True Positives, got {tp}"
    assert tn == 20, f"Expected 20 True Negatives, got {tn}"
    assert fp == 0, f"Expected 0 False Positives, got {fp}"
    assert fn == 0, f"Expected 0 False Negatives, got {fn}"

    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f1 = 2 * precision * recall / (precision + recall)
    accuracy = (tp + tn) / total

    assert accuracy == 1.0
    assert precision == 1.0
    assert recall == 1.0
    assert f1 == 1.0
