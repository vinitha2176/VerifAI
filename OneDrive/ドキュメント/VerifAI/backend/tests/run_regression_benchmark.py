"""Benchmark script for VerifAI Analysis Engine across 35 test scenarios.

Evaluates:
- 10 Suspicious recruitment offers
- 10 Legitimate recruitment offers
- 5 Explicit fee/deposit negation examples
- 5 Multi-flag offers
- 5 Ambiguous/safe edge cases
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, NamedTuple

# Ensure backend root on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.prediction import PredictionService
from app.services.risk_engine import RiskEngine
from app.services.analysis_service import AnalysisService
from app.models.database import Base, SessionLocal, engine
from app.schemas.analysis import DetectedIndicator


class TestCase(NamedTuple):
    id: str
    category: str
    ground_truth: str  # "SUSPICIOUS" or "LEGITIMATE"
    expected_risk: str  # "HIGH", "MODERATE", or "LOW"
    text: str
    expected_indicators: List[str]


TEST_CASES: List[TestCase] = [
    # ---------------------------------------------------------
    # 10 SUSPICIOUS CASES
    # ---------------------------------------------------------
    TestCase(
        id="SUSP_01_TEST_A",
        category="Suspicious",
        ground_truth="SUSPICIOUS",
        expected_risk="HIGH",
        text=(
            "Apex Technologies - Junior Software Developer. "
            "We are pleased to inform you of your guaranteed selection without an interview for the Junior Software Developer position. "
            "To confirm your acceptance, a refundable registration fee of ₹2,500 must be paid immediately. "
            "Immediate payment requirement applies to secure your placement in this cohort."
        ),
        expected_indicators=[
            "Registration / Onboarding Fee Demand",
            "Guaranteed Selection Without Interview",
            "Urgent Payment Deadline Pressure",
        ],
    ),
    TestCase(
        id="SUSP_02_TEST_B",
        category="Suspicious",
        ground_truth="SUSPICIOUS",
        expected_risk="HIGH",
        text=(
            "Global Infotech Internship Program. "
            "Congratulations! You have received guaranteed selection without an interview for our 2026 Developer Internship. "
            "A non-refundable onboarding charge of ₹1,999 is required to initiate your profile. "
            "Additionally, a mandatory ₹4,000 training charge must be paid for the induction module. "
            "Please submit your identity documents and bank details via Telegram to our HR coordinator (@InfotechHR). "
            "This offer expires within a 2-hour deadline, so payment must be transferred immediately."
        ),
        expected_indicators=[
            "Registration / Onboarding Fee Demand",
            "Mandatory Paid Training / Training Charge",
            "Guaranteed Selection Without Interview",
            "Urgent Payment Deadline Pressure",
            "Premature Sensitive Financial Document Request",
        ],
    ),
    TestCase(
        id="SUSP_03_EQUIPMENT_DEPOSIT",
        category="Suspicious",
        ground_truth="SUSPICIOUS",
        expected_risk="HIGH",
        text=(
            "Remote Customer Service Representative. Welcome to Global Logistics Ltd. "
            "Before dispatching your company Apple MacBook Pro and workstation, candidate must remit a refundable equipment deposit of ₹15,000. "
            "Refundable security deposit will be credited back on the first monthly payroll."
        ),
        expected_indicators=["Security / Equipment Deposit Demand"],
    ),
    TestCase(
        id="SUSP_04_DIRECT_APPOINTMENT_UPI",
        category="Suspicious",
        ground_truth="SUSPICIOUS",
        expected_risk="HIGH",
        text=(
            "Offer of Appointment - Business Analyst. "
            "You have been selected without any interview based on your resume profile. Direct appointment without interview is confirmed. "
            "Please transfer the processing fee of ₹1,500 via UPI to our HR desk immediately."
        ),
        expected_indicators=[
            "Guaranteed Selection Without Interview",
            "Application / Processing Fee Requirement",
            "Urgent Payment Deadline Pressure",
        ],
    ),
    TestCase(
        id="SUSP_05_PORTAL_ACCESS_FEE",
        category="Suspicious",
        ground_truth="SUSPICIOUS",
        expected_risk="HIGH",
        text=(
            "Online Data Entry Executive. Start working from home and earn guaranteed ₹30,000 per month. "
            "An initial portal administration fee of ₹3,000 is required to activate your employee dashboard and allocate project data."
        ),
        expected_indicators=["Application / Processing Fee Requirement"],
    ),
    TestCase(
        id="SUSP_06_MANDATORY_TRAINING",
        category="Suspicious",
        ground_truth="SUSPICIOUS",
        expected_risk="HIGH",
        text=(
            "Full Stack Developer Trainee. Candidates must undergo our proprietary 4-week industry curriculum. "
            "A mandatory ₹6,500 training charge must be deposited prior to joining date. Training fee is non-refundable."
        ),
        expected_indicators=["Mandatory Paid Training / Training Charge"],
    ),
    TestCase(
        id="SUSP_07_URGENT_DEADLINE",
        category="Suspicious",
        ground_truth="SUSPICIOUS",
        expected_risk="HIGH",
        text=(
            "Urgent Hiring Notice: Backend Engineer. We have 1 remaining slot for our development center. "
            "You must pay registration fee of ₹2,000 within a 2-hour deadline today itself to secure your seat. "
            "Immediate payment requirement is strictly enforced."
        ),
        expected_indicators=[
            "Registration / Onboarding Fee Demand",
            "Urgent Payment Deadline Pressure",
        ],
    ),
    TestCase(
        id="SUSP_08_DOCS_TELEGRAM",
        category="Suspicious",
        ground_truth="SUSPICIOUS",
        expected_risk="HIGH",
        text=(
            "Digital Marketing Specialist. Congratulations on your direct joining without an interview! "
            "To finalize your documentation, please send your identity documents and bank details via WhatsApp to our hiring coordinator."
        ),
        expected_indicators=[
            "Guaranteed Selection Without Interview",
            "Premature Sensitive Financial Document Request",
        ],
    ),
    TestCase(
        id="SUSP_09_SCREENING_FEE",
        category="Suspicious",
        ground_truth="SUSPICIOUS",
        expected_risk="HIGH",
        text=(
            "Executive Assistant Position. Before releasing your final contract, an external screening fee of ₹2,200 must be transferred to our partner account. "
            "Candidates must pay the verification fee before joining."
        ),
        expected_indicators=["Application / Processing Fee Requirement"],
    ),
    TestCase(
        id="SUSP_10_HIGH_EARNINGS",
        category="Suspicious",
        ground_truth="SUSPICIOUS",
        expected_risk="HIGH",
        text=(
            "Part-Time Typing Specialist. Earn ₹2,500 daily for typing 5 pages per day. Zero qualifications required. "
            "Immediate enrollment fee of ₹1,200 is mandatory to receive your first assignment kit."
        ),
        expected_indicators=["Registration / Onboarding Fee Demand"],
    ),

    # ---------------------------------------------------------
    # 10 LEGITIMATE CASES
    # ---------------------------------------------------------
    TestCase(
        id="LEGIT_01_FRONTEND",
        category="Legitimate",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Senior Frontend Engineer at CloudScale Technologies. We are looking for an experienced engineer skilled in React, TypeScript, and modern CSS. "
            "You will lead UI architecture across our core SaaS products. Responsibilities include mentoring junior engineers and optimizing page performance. "
            "Minimum 5 years of production experience required. Competitive annual package with health insurance and provident fund. "
            "Selection involves an initial recruiter phone screen, a 60-minute technical coding interview, a system architecture discussion, and a culture fit conversation."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="LEGIT_02_PRODUCT_MGR",
        category="Legitimate",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Product Manager - FinTech Platform. Metro Financial Services is hiring a Product Manager to guide our next-generation payments product. "
            "The ideal candidate has 3+ years in product discovery, user journey mapping, and cross-functional leadership. "
            "Interview process comprises a recruiter screen, product case study presentation, and interview rounds with engineering and design leads. "
            "We provide comprehensive medical insurance, annual learning stipends, and flexible hybrid working arrangements."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="LEGIT_03_DEVOPS",
        category="Legitimate",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "DevOps / Infrastructure Engineer at DataMesh Networks. We seek a DevOps Engineer proficient with Kubernetes, Terraform, Docker, and AWS cloud architecture. "
            "Candidate will maintain CI/CD deployment pipelines, manage observability via Prometheus and Grafana, and ensure system uptime. "
            "Candidates undergo an architectural review and technical deep dive interview. The company provides competitive compensation and standard benefits."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="LEGIT_04_DATA_ANALYST",
        category="Legitimate",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Business Intelligence & Data Analyst. Retail Insights Corp is expanding its analytics division. "
            "Requirements: Strong proficiency in SQL, Python data libraries (pandas, numpy), and visualization tools (Tableau, PowerBI). "
            "The candidate will collaborate with supply chain managers to optimize inventory logistics. "
            "Candidates must complete a take-home SQL practical assessment followed by a technical panel interview."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="LEGIT_05_SUPPORT",
        category="Legitimate",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Customer Success Specialist at BrightDesk Software. You will support enterprise customers across email and live chat, "
            "troubleshooting product configuration issues and documenting recurring user feedback. "
            "Shift timings include rotational morning and evening schedules. "
            "Comprehensive 3-week onboarding training is provided free of cost by the company. "
            "Annual salary ₹4,50,000 with quarterly performance incentives."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="LEGIT_06_QA_AUTOMATION",
        category="Legitimate",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Quality Assurance Automation Engineer at SecureApp Ltd. Join our test engineering squad to build automated test frameworks using Playwright and pytest. "
            "Requirements include 2+ years experience in automated regression testing and API testing. "
            "Selection process consists of a coding challenge, technical interview, and managerial discussion. "
            "Company furnishes all computer hardware and development workstations."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="LEGIT_07_MARKETING",
        category="Legitimate",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Content Marketing Strategist at Apex Media. Responsible for producing technical whitepapers, case studies, and corporate blog content. "
            "Requires portfolio submission demonstrating published B2B articles. "
            "Interview process consists of an editorial evaluation and an interview with the VP of Marketing."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="LEGIT_08_SYSADMIN",
        category="Legitimate",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Linux Systems Administrator at Horizon Cloud. Manage enterprise Linux servers, perform routine patching, "
            "monitor network security protocols, and support database backups. Qualifications include RHCE certification or equivalent practical expertise. "
            "Candidate must complete two rounds of technical interviews."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="LEGIT_09_DESIGNER",
        category="Legitimate",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "UI/UX Visual Designer at StudioNine. We are seeking a creative designer with proficiency in Figma, design systems, and typography. "
            "Candidates must submit a design portfolio showcasing wireframes, interactive prototypes, and web design projects. "
            "Multi-stage assessment includes portfolio walkthrough and collaboration interview."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="LEGIT_10_ARCHITECT",
        category="Legitimate",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Enterprise Solutions Architect at PrimeCloud Inc. Partner with enterprise clients to design fault-tolerant, scalable cloud infrastructure. "
            "Minimum 8 years in IT with active AWS or Azure Solutions Architect professional certification. "
            "Selection involves a panel presentation and stakeholder discussions. Top-tier compensation and relocation support."
        ),
        expected_indicators=[],
    ),

    # ---------------------------------------------------------
    # 5 EXPLICIT NEGATION CASES (CRITICAL FOR FALSE POSITIVE MITIGATION)
    # ---------------------------------------------------------
    TestCase(
        id="NEG_01_TEST_C",
        category="Fee Negation",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Acme Systems - Summer Engineering Internship. We invite applications for our competitive three-month internship program in Software Engineering. "
            "Selected interns receive a ₹10,000 monthly stipend and work directly with senior architects. "
            "Candidates must complete a technical interview and practical assessment. "
            "No registration fee, security deposit, or application fee is required at any point in our hiring process. "
            "Apply via our official corporate careers portal."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="NEG_02_SECURITY_DEPOSIT",
        category="Fee Negation",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Remote Full Stack Developer at OpenSource Technologies. Join our distributed team building web applications. "
            "Candidates are not required to pay any security deposit or equipment fees. "
            "The company provides all laptops and work accessories free of cost directly to your residence upon joining."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="NEG_03_NO_APPLICATION_FEES",
        category="Fee Negation",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Graduate Engineer Trainee - Nexus Industries. We are hiring fresh engineering graduates for our core plant operations. "
            "There are no registration fees, interview charges, or processing costs at any stage of our recruitment process. "
            "All interviews are conducted at our regional offices."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="NEG_04_BEWARE_SCAMS",
        category="Fee Negation",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Careers at Sterling Health Systems - Clinical Research Associate. "
            "Please note that our company never charges any application fee, registration cost, or security deposit. "
            "We do not ask candidates to pay money for interviews or training. Report any unauthorized person asking for payment in our name."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="NEG_05_ZERO_COST",
        category="Fee Negation",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Associate Software Engineer at Global Logic Solutions. "
            "Applicants will never be asked for application fees, training charges, or caution deposits. "
            "Our entire selection process is completely free of cost and strictly merit-based. Technical interviews and HR evaluations are mandatory."
        ),
        expected_indicators=[],
    ),

    # ---------------------------------------------------------
    # 5 MULTI-FLAG OFFERS
    # ---------------------------------------------------------
    TestCase(
        id="MULTI_01_EXTORTION_COMBO",
        category="Multi-Flag",
        ground_truth="SUSPICIOUS",
        expected_risk="HIGH",
        text=(
            "Software Developer Trainee. Congratulations, guaranteed selection without an interview is confirmed. "
            "Candidates must pay a registration fee of ₹2,000 immediately within a 2-hour deadline to reserve seat. "
            "Transfer funds to our recruitment desk via WhatsApp coordinator."
        ),
        expected_indicators=[
            "Registration / Onboarding Fee Demand",
            "Guaranteed Selection Without Interview",
            "Urgent Payment Deadline Pressure",
        ],
    ),
    TestCase(
        id="MULTI_02_DEPOSIT_AND_DOCS",
        category="Multi-Flag",
        ground_truth="SUSPICIOUS",
        expected_risk="HIGH",
        text=(
            "Remote Data Specialist. Offer of appointment issued without interview. "
            "Please deposit a refundable security deposit of ₹8,000 for work equipment. "
            "Additionally, remit an application processing fee of ₹1,000. "
            "Send your identity documents and bank details via Telegram to proceed."
        ),
        expected_indicators=[
            "Security / Equipment Deposit Demand",
            "Application / Processing Fee Requirement",
            "Guaranteed Selection Without Interview",
            "Premature Sensitive Financial Document Request",
        ],
    ),
    TestCase(
        id="MULTI_03_TRAINING_AND_PRESSURE",
        category="Multi-Flag",
        ground_truth="SUSPICIOUS",
        expected_risk="HIGH",
        text=(
            "Python Developer Internship. Immediate direct appointment without any assessment. "
            "A mandatory ₹5,000 training charge is required for the project orientation kit. "
            "Immediate payment requirement applies and must be transferred today."
        ),
        expected_indicators=[
            "Mandatory Paid Training / Training Charge",
            "Guaranteed Selection Without Interview",
            "Urgent Payment Deadline Pressure",
        ],
    ),
    TestCase(
        id="MULTI_04_ONBOARDING_PURCHASE",
        category="Multi-Flag",
        ground_truth="SUSPICIOUS",
        expected_risk="HIGH",
        text=(
            "Virtual Operations Analyst. You are selected without an interview. "
            "A non-refundable onboarding fee of ₹2,500 must be paid before joining. "
            "Candidate must purchase software license before joining through our designated vendor. "
            "Official communication conducted via Telegram."
        ),
        expected_indicators=[
            "Registration / Onboarding Fee Demand",
            "Compulsory Payment or Purchase Before Joining",
            "Guaranteed Selection Without Interview",
        ],
    ),
    TestCase(
        id="MULTI_05_SCREENING_SURRENDER",
        category="Multi-Flag",
        ground_truth="SUSPICIOUS",
        expected_risk="HIGH",
        text=(
            "Regional Field Executive. Urgent hiring: selected candidates must pay screening fee of ₹1,800 immediately. "
            "You must surrender original degree certificates before joining. "
            "Urgent payment required within 2 hours."
        ),
        expected_indicators=[
            "Application / Processing Fee Requirement",
            "Premature Sensitive Financial Document Request",
            "Urgent Payment Deadline Pressure",
        ],
    ),

    # ---------------------------------------------------------
    # 5 AMBIGUOUS / SAFE EDGE CASES
    # ---------------------------------------------------------
    TestCase(
        id="EDGE_01_REIMBURSEMENT",
        category="Edge Case",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Senior Consultant - Strategy & Operations at McKinsey & Partners. "
            "Candidates traveling from out of station for the final partner round will receive travel expense reimbursement up to ₹5,000. "
            "Submit original travel tickets to the reception desk for company reimbursement."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="EDGE_02_TRAINING_MENTION",
        category="Edge Case",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Cloud Engineering Apprenticeship. The 6-month curriculum includes intensive hands-on training in microservices, "
            "followed by deployment to enterprise client teams. "
            "Mentorship is provided by principal architects throughout the fellowship."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="EDGE_03_JOINING_BONUS",
        category="Edge Case",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Staff Site Reliability Engineer. We offer a competitive base compensation of ₹35,00,000 alongside a joining bonus of ₹3,00,000 "
            "payable upon completion of 90 days. Comprehensive health benefits included."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="EDGE_04_PHYSICAL_ID",
        category="Edge Case",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Systems Engineer - Onsite Client Facility. For security clearance at the client tech park, "
            "candidates attending the on-site interview must present government photo identity at the reception gate. "
            "Valid items include Passport or Driver License."
        ),
        expected_indicators=[],
    ),
    TestCase(
        id="EDGE_05_EQUIPMENT_PROVISION",
        category="Edge Case",
        ground_truth="LEGITIMATE",
        expected_risk="LOW",
        text=(
            "Senior Frontend Developer. We support remote work across India. "
            "Every new team member receives a company-provided M3 MacBook Pro, 4K monitor, and ergonomics allowance upon joining."
        ),
        expected_indicators=[],
    ),
]


def run_benchmark():
    risk_engine = RiskEngine()
    analysis_service = AnalysisService()

    print("=" * 80)
    print("VERIFAI ANALYSIS ENGINE — 35-SAMPLE REGRESSION BENCHMARK")
    print("=" * 80)

    tp = 0  # Ground truth SUSPICIOUS predicted HIGH
    tn = 0  # Ground truth LEGITIMATE predicted LOW or MODERATE (clean)
    fp = 0  # Ground truth LEGITIMATE predicted HIGH (or false fee indicator)
    fn = 0  # Ground truth SUSPICIOUS predicted LOW

    category_results: Dict[str, Dict[str, int]] = {}

    for tc in TEST_CASES:
        cat = tc.category
        if cat not in category_results:
            category_results[cat] = {"total": 0, "correct": 0, "fp": 0, "fn": 0}
        category_results[cat]["total"] += 1

        rule_score, indicators, evidence_list = risk_engine.evaluate(tc.text)
        pred_label, ml_score = analysis_service.prediction_service.predict(tc.text)
        risk_level = analysis_service.compute_risk_level(ml_score, rule_score, indicators)

        detected_names = {ind.indicator_name for ind in indicators}

        # Check classification correctness
        is_scam = tc.ground_truth == "SUSPICIOUS"
        predicted_high = (risk_level == "HIGH")

        if is_scam:
            if predicted_high:
                tp += 1
                category_results[cat]["correct"] += 1
                status = "PASS (TP)"
            else:
                fn += 1
                category_results[cat]["fn"] += 1
                status = "FAIL (FN)"
        else:
            if not predicted_high and len(indicators) == 0:
                tn += 1
                category_results[cat]["correct"] += 1
                status = "PASS (TN)"
            elif predicted_high or any("Fee" in n or "Deposit" in n for n in detected_names):
                fp += 1
                category_results[cat]["fp"] += 1
                status = "FAIL (FP)"
            else:
                tn += 1
                category_results[cat]["correct"] += 1
                status = "PASS (TN-clean)"

        print(
            f"[{status:12}] {tc.id:28} | GT={tc.ground_truth:10} | Risk={risk_level:8} | "
            f"ML={ml_score:.2f} | Rule={rule_score:.2f} | Indicators={len(indicators)}"
        )
        if status.startswith("FAIL"):
            print(f"   -> Detected: {detected_names}")
            print(f"   -> Expected: {tc.expected_indicators}")

    # Calculate metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(TEST_CASES)

    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY RESULTS")
    print("=" * 80)
    print(f"Total Test Cases Evaluated : {len(TEST_CASES)}")
    print(f"True Positives  (TP)       : {tp} / 15")
    print(f"True Negatives  (TN)       : {tn} / 20")
    print(f"False Positives (FP)       : {fp} / 20")
    print(f"False Negatives (FN)       : {fn} / 15")
    print("-" * 80)
    print(f"Accuracy                   : {accuracy * 100:.2f}%")
    print(f"Precision                  : {precision * 100:.2f}%")
    print(f"Recall                     : {recall * 100:.2f}%")
    print(f"F1 Score                   : {f1 * 100:.2f}%")
    print("=" * 80)

    print("\nCATEGORY BREAKDOWN:")
    for cat, d in category_results.items():
        pct = (d["correct"] / d["total"]) * 100
        print(f" - {cat:20}: {d['correct']}/{d['total']} passed ({pct:.1f}%) | FP={d['fp']}, FN={d['fn']}")


if __name__ == "__main__":
    run_benchmark()

