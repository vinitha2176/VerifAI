# VERIFAI — ANALYSIS ENGINE AUDIT & VERIFICATION REPORT

**Report Generated:** November 4, 2026  
**System Version:** VerifAI MVP 1.0  
**Audit Scope:** Verification-Only Audit of Analysis Engine, Risk Rules, Negation Handling, Evidence Extraction, Composite Risk Scoring, and Regression Test Suite.  
**Execution Constraint:** No code modifications permitted during this audit; all reported metrics represent genuine executed runtime tests.

---

## 1. Executive Summary

A critical bug investigation was conducted to resolve severe reliability issues observed in the VerifAI analysis engine during manual testing of three core recruitment scenarios:
1. **Scenario A (Suspicious Job Offer - Text):** Contained a refundable registration fee of ₹2,500, guaranteed selection without an interview, and an immediate payment requirement. Previously misclassified as `LEGITIMATE` (ML score ~13%, composite risk `MODERATE`) with only 1 indicator detected.
2. **Scenario B (Suspicious Internship - PDF):** Contained a non-refundable ₹1,999 onboarding charge, a mandatory ₹4,000 training fee, Telegram/WhatsApp sensitive document demands, guaranteed selection without an interview, and an artificial 2-hour deadline. Previously misclassified as `LEGITIMATE` (ML score ~9%, composite risk `MODERATE`) with only 1 indicator detected.
3. **Scenario C (Lower-Risk Internship - PDF):** Contained an explicit negative disclaimer: *"No registration fee, security deposit, or application fee is required at any point in our hiring process."* Previously produced a severe false positive by triggering `"Security / Equipment Deposit Demand"` and quoting the negative sentence as scam evidence.

### Current Audit Status
- **Total Backend Tests:** 36 passed, 0 failed, 0 skipped (Execution time: 1.45s).
- **Regression Suite:** 4 passed, 0 failed, 0 skipped (Execution time: 0.95s).
- **35-Sample Benchmark Matrix:** 35 / 35 passed (100% Accuracy, 100% Precision, 100% Recall, 0 False Positives, 0 False Negatives).
- **Frontend Production Build:** Vite v5.4.21 compiled successfully in 7.37s with zero errors or warnings.
- **Scenario A Current Status:** Classified as `HIGH` risk, 3 red flags detected, exact sentence-level evidence extracted, actionable warnings generated.
- **Scenario B Current Status:** Classified as `HIGH` risk, 6 red flags detected (covering all 5 distinct scam mechanisms), exact sentence-level evidence extracted, 8 tailored recommendations generated.
- **Scenario C Current Status:** Classified as `LOW` risk, 0 red flags detected (false positive completely eliminated), standard diligence guidance provided.

---

## 2. Root Cause Analysis

### Defect 1: Negation Handling Failure on Coordinated Lists (Scenario C)
* **Observed Defect:** In Scenario C, the text *"No registration fee, security deposit, or application fee is required at any point in our hiring process"* triggered `Security / Equipment Deposit Demand`.
* **Root Cause:** In `risk_engine.py`, the rule-specific negation pattern was `r"\bno\s+(?:security\s+)?deposit\b"`. In coordinated lists where intervening nouns appear (`"No registration fee, security deposit..."`), the word `"No"` was separated from `"security deposit"` by comma-delimited items. Because standard sentence segmentation did not recognize cross-coordinate scope, the positive regex `r"(?:security|refundable).*(?:deposit)"` matched, while the narrow negation regex failed to trigger.

### Defect 2: Inadequate Indicator Coverage & Nominalization Gaps (Scenarios A & B)
* **Observed Defect:** Highly suspicious documents containing multiple distinct predatory signals produced only a single indicator.
* **Root Causes:**
  1. **Guaranteed Selection:** The pattern only matched verb phrases (e.g. `selected without interview`, `hired without test`), completely missing nominalized phrases (e.g. `"guaranteed selection without an interview"`, `"direct appointment without interview"`).
  2. **Urgent Payment Demands:** Regexes only looked for imperative verbs (`pay immediately`), missing noun phrases like `"immediate payment requirement"` and short deadline expressions like `"within a 2-hour deadline"`.
  3. **Mandatory Paid Training:** The rule catalog completely lacked a rule for training charges. When recruiters demanded `"₹4,000 training charge"` or `"paid training program"`, no rule existed to flag it.
  4. **Sensitive Personal & Financial Documents:** Patterns only checked for banking PINs and credit card numbers, failing to flag requests for `"identity documents"`, `"bank details"`, Aadhaar, or PAN cards sent via informal channels (`Telegram` or `WhatsApp`).

### Defect 3: Monolithic Evidence Extraction & PDF Soft-Wrap Fragmentation
* **Observed Defect:** The "Matched Evidence" section displayed multi-line blocks encompassing entire paragraphs or pages.
* **Root Causes:**
  1. The sentence segmentation regex split only on `(?<=\n)\s+`. In text extracted from PDFs via PyMuPDF (`fitz`), lines often end with `\n` without trailing spaces. Monolithic page chunks were treated as a single sentence.
  2. Conversely, when line breaks wrapped mid-sentence (e.g., `"guaranteed selection without\nan interview"`), splitting on raw `\n` broke the sentence into two halves, preventing regexes from seeing the full syntactic clause.

### Defect 4: Composite Risk Scoring Flaw
* **Observed Defect:** Even when extortion indicators were flagged, the document was downgraded to `MODERATE` risk because the ML score was low (~7%–14%).
* **Root Cause:** `compute_risk_level(model_score, rule_score)` required `rule_score >= 0.50` or `model_score >= 0.70` to trigger `HIGH` risk. Individual extortion rules had weights between 0.25 and 0.35. Unless two heavy rules fired simultaneously, a document demanding a ₹2,500 registration fee was downgraded to `MODERATE` because the ML model (trained on US/UK corporate postings from 2012–2014) did not assign high scam probability to localized Indian fee terminology.

### Defect 5: Generic, Static Recommendations
* **Observed Defect:** Guidance was generic and failed to address specific risks like 2-hour deadlines, mandatory training fees, or Telegram document submissions.

---

## 3. Code Modifications & Architectural Changes

### Summary of Modified Files
1. `backend/app/services/risk_engine.py`: Enhanced negation handling, clause splitting, new `TRAINING_FEE` rule, severity elevation for `SECURITY_DEPOSIT`, and comprehensive indicator patterns.
2. `backend/app/services/analysis_service.py`: Multi-factor composite risk evaluation incorporating indicator severities, dynamic recommendation generation.
3. `backend/tests/test_analysis_regression.py`: Comprehensive 4-scenario integration test suite and 35-sample benchmark validation.
4. `backend/tests/run_regression_benchmark.py`: Standalone benchmark execution harness.
5. `backend/tests/eval_scenarios_abc.py`: Runtime verification harness for Scenarios A, B, and C.
6. `frontend/src/pages/ResultsPage.jsx`: Inspected — confirmed fully compatible; no frontend code changes were necessary.

---

### File Diff 1: `backend/app/services/risk_engine.py`

```diff
--- a/backend/app/services/risk_engine.py
+++ b/backend/app/services/risk_engine.py
@@ -14,6 +14,24 @@ from app.schemas.analysis import DetectedIndicator
+# Comprehensive negative declaration patterns for fee and deposit contexts
+COMMON_FEE_NEGATION_PATTERNS = [
+    re.compile(r"\bno\s+.*(?:is|are)\s+(?:required|needed|charged|demanded|asked|taken)\b", re.IGNORECASE),
+    re.compile(
+        r"\bno\s+(?:registration|application|processing|screening|onboarding|security|training|equipment|internship)?\s*"
+        r"(?:fee|fees|charges?|cost|deposit|caution|payment)\b",
+        re.IGNORECASE,
+    ),
+    re.compile(r"\b(?:there\s+is\s+no|there\s+are\s+no)\s+.*(?:fee|deposit|charge|cost|payment)\b", re.IGNORECASE),
+    re.compile(r"\b(?:candidates?|applicants?|students?)\s+(?:are|is)\s+not\s+required\s+to\s+pay\b", re.IGNORECASE),
+    re.compile(r"\b(?:will\s+never\s+be|are\s+never|is\s+never|never\s+be)\s+(?:asked|required|requested)\s+(?:for|to\s+pay)?\b", re.IGNORECASE),
+    re.compile(r"\b(?:we\s+do\s+not|do\s+not|never|company\s+never|does\s+not)\s+(?:ask|charge|require|demand|collect).*(?:fee|deposit|charge|payment|money)\b", re.IGNORECASE),
+    re.compile(r"\b(?:do\s+not|never)\s+pay\s+(?:any\s+)?(?:money|fee|deposit|charge)\b", re.IGNORECASE),
+    re.compile(r"\bno\s+payment\s+(?:is\s+)?(?:required|needed)\s+at\s+any\s+stage\b", re.IGNORECASE),
+    re.compile(r"\b(?:free\s+of\s+cost|at\s+no\s+(?:cost|charge)|at\s+zero\s+cost|zero\s+fees?)\b", re.IGNORECASE),
+    re.compile(r"\bwithout\s+(?:any\s+)?(?:fee|fees|deposit|charges?|cost|payment)\b", re.IGNORECASE),
+]
+
+def split_into_clean_clauses(text: str) -> List[str]:
+    """Segment raw text into clean, individual sentence and clause units.
+    Normalizes soft wraps while respecting sentence delimiters and bullet points.
+    """
+    normalized = re.sub(r"(?<![.!?:\n])\n(?!\n|[\s]*[•\-\*\–—\d\.\)])", " ", text)
+    raw_lines = re.split(r"[\r\n]+", normalized)
+    clauses: List[str] = []
+    for line in raw_lines:
+        line = line.strip()
+        if not line:
+            continue
+        line = re.sub(r"^[\s\-\*•–—\d\.\)]+", "", line).strip()
+        if not line:
+            continue
+        parts = re.split(r"(?<=[.!?])\s+", line)
+        for p in parts:
+            p = p.strip()
+            if len(p) >= 3:
+                clauses.append(p)
+    return clauses

@@ -88,14 +118,24 @@ class RiskRule:
     def evaluate_clause(self, clause: str) -> Optional[str]:
         # Step 1: Check positive matches
         matched = False
         for pos_re in self.positive_regexes:
             if pos_re.search(clause):
                 matched = True
                 break
         if not matched:
             return None
 
         # Step 2: Check rule-specific negation patterns
         for neg_re in self.negation_regexes:
             if neg_re.search(clause):
                 return None
+
+        # Step 3: Check hierarchical fee negation patterns if applicable
+        if self.is_fee_rule:
+            for fee_neg in COMMON_FEE_NEGATION_PATTERNS:
+                if fee_neg.search(clause):
+                    return None
+
+        # Step 4: Clean evidence extraction
+        evidence = re.sub(r"^[\s\-\*•–—\d\.\)]+", "", clause).strip()
+        return evidence

@@ -182,24 +230,50 @@ def build_default_rules() -> List[RiskRule]:
+        RiskRule(
+            rule_id="TRAINING_FEE",
+            name="Mandatory Paid Training / Training Charge",
+            severity="CRITICAL",
+            weight=0.35,
+            explanation=(
+                "Legitimate internships and employment opportunities provide training without charging candidates. "
+                "Demanding training fees or fees for skill development is an illicit fee-shifting tactic."
+            ),
+            positive_patterns=[
+                r"(?:training|skill\s+development|curriculum|course|bootcamp)\s+(?:fee|fees|charges?|cost|amount)",
+                r"(?:pay|deposit|remit)\s+(?:₹|rs\.?|\$|usd|inr)?\s*\d+.*(?:training|skill\s+development|curriculum|course)",
+                r"(?:additional|mandatory)\s+(?:₹|rs\.?|\$|usd|inr)?\s*\d+\s+training\s+charge",
+                r"(?:pay|charge)\s+for\s+(?:the\s+)?(?:training|skill\s+development)",
+                r"paid\s+training\s+(?:program|course|session|curriculum)",
+                r"training\s+charge\s+is\s+mandatory",
+            ],
+            negation_patterns=[
+                r"\b(?:no|without\s+any|zero)\s+training\s+(?:fee|charges?|cost)\b",
+                r"\bfree\s+(?:training|skill\s+development)\b",
+                r"\btraining\s+(?:is\s+)?(?:provided\s+)?(?:free\s+of\s+cost|at\s+no\s+cost)\b",
+                r"\bcompany\s+provides\s+(?:free\s+)?training\b",
+                r"\bno\s+.*training\s+(?:fee|charges?).*(?:is\s+)?(?:required|charged|needed)\b",
+            ],
+            is_fee_rule=True,
+        ),
         RiskRule(
             rule_id="SECURITY_DEPOSIT",
             name="Security / Equipment Deposit Demand",
-            severity="HIGH",
-            weight=0.25,
+            severity="CRITICAL",
+            weight=0.35,
             explanation=(
                 "Scammers frequently solicit 'refundable' security deposits for laptops, "
                 "training materials, or asset allocations. Genuine firms supply necessary equipment without deposit."
             ),
             positive_patterns=[
                 r"(?:security|refundable|laptop|asset|equipment)\s+(?:deposit|caution\s+money)",
                 r"(?:deposit|pay)\s+(?:of\s+)?(?:₹|rs\.?|\$|usd|inr)?\s*\d+\s*(?:as|for)?\s*(?:security|refundable|laptop|asset|equipment)",
                 r"refundable\s+amount\s+(?:of\s+)?(?:₹|rs\.?|\$|usd|inr)?\s*\d+",
                 r"(?:security\s+deposit|equipment\s+deposit)\s+(?:of\s+)?(?:₹|rs\.?|\$|usd|inr)?\s*\d+",
                 r"(?:security\s+deposit|equipment\s+deposit)\s+is\s+(?:mandatory|required)",
             ],
+            negation_patterns=[
+                r"\bcompany\s+(?:provides|furnishes|covers)\s+(?:all\s+)?equipment\b",
+                r"\bno\s+deposit\s+is\s+required\b",
+            ],
+            is_fee_rule=True,
         ),
```

---

### File Diff 2: `backend/app/services/analysis_service.py`

```diff
--- a/backend/app/services/analysis_service.py
+++ b/backend/app/services/analysis_service.py
@@ -37,24 +37,47 @@ class AnalysisService:
     @staticmethod
-    def compute_risk_level(model_score: float, rule_score: float) -> str:
+    def compute_risk_level(
+        model_score: float,
+        rule_score: float,
+        detected_indicators: Sequence[DetectedIndicator] | None = None,
+    ) -> str:
         """Determine tripartite risk classification (LOW, MODERATE, HIGH).
 
-        Prevents a single weak rule match from falsely escalating risk while
-        honoring acute payment demands and strong ML scam signals.
+        Incorporates indicator severity count, rule score, and calibrated ML score.
+        Critical indicators (such as registration fees, training fees, or sensitive document demands)
+        immediately warrant a HIGH risk classification to protect applicants from acute extortion.
         """
-        # Critical risk: high ML probability OR severe fee/extortion rules triggered
-        if rule_score >= 0.50 or model_score >= 0.70:
-            return "HIGH"
+        indicators = detected_indicators or []
+        critical_count = sum(1 for ind in indicators if ind.severity.upper() == "CRITICAL")
+        high_count = sum(1 for ind in indicators if ind.severity.upper() == "HIGH")
+        medium_count = sum(1 for ind in indicators if ind.severity.upper() == "MEDIUM")
+
+        # 1. Critical risk: Any CRITICAL extortion indicator (registration fee, mandatory training charge,
+        # sensitive document demands) or multiple HIGH indicators or strong rule/ML score
+        if (
+            critical_count >= 1
+            or high_count >= 2
+            or rule_score >= 0.40
+            or model_score >= 0.65
+            or (model_score >= 0.40 and high_count >= 1)
+        ):
+            return "HIGH"
 
-        # Moderate risk: medium ML probability OR presence of suspicious indicators
-        if rule_score >= 0.25 or model_score >= 0.40:
+        # 2. Moderate risk: Single HIGH indicator, medium severity indicators, or moderate risk scores
+        if (
+            high_count == 1
+            or medium_count >= 1
+            or rule_score >= 0.20
+            or model_score >= 0.35
+        ):
             return "MODERATE"
 
-        # Safe baseline
+        # 3. Safe baseline: No indicators and low ML model score
         return "LOW"

@@ -80,18 +103,42 @@ class AnalysisService:
         # Specific recommendations for identified indicators
-        if any("Fee" in name for name in indicator_names):
+        if any("Fee" in name or "Payment" in name for name in indicator_names):
             recommendations.append(
                 "Never send money or pay upfront fees for job registration, interviews, or application processing. "
                 "Legitimate employers do not transfer recruitment overhead costs to candidates."
             )
 
+        if any("Training" in name for name in indicator_names):
+            recommendations.append(
+                "Be cautious of mandatory paid training, onboarding packages, or certification fees required as a prerequisite. "
+                "Authentic employers invest in employee training at company expense."
+            )
+
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
 
+        if any("Urgent" in name or "Deadline" in name for name in indicator_names):
+            recommendations.append(
+                "Do not yield to artificial urgency or short deadlines (such as 2-hour or same-day payment windows). "
+                "Scammers create false panic to prevent candidates from verifying claims."
+            )
+
-        if any("Sensitive" in name for name in indicator_names):
+        if any("Sensitive" in name or "Financial" in name for name in indicator_names):
             recommendations.append(
-                "Never disclose banking passwords, credit card details, OTPs, or original academic credentials. "
-                "Only submit verified document photocopies after confirming the employer's authenticity."
+                "Never disclose banking passwords, credit card details, OTPs, or send copies of identity documents (Aadhaar, PAN, passport) "
+                "over informal messaging apps like Telegram or WhatsApp. Submit verification documents only via secure corporate portals."
             )
 
         if any("Communication Channel" in name for name in indicator_names):
             recommendations.append(
                 "Insist on official corporate email communication (e.g. name@company.com). Be wary of recruiters "
                 "operating exclusively through personal Telegram handles or WhatsApp numbers."
             )

@@ -148,3 +195,7 @@ class AnalysisService:
         # Step 3: Compute composite risk tier
-        risk_level = self.compute_risk_level(model_score=model_score, rule_score=rule_score)
+        risk_level = self.compute_risk_level(
+            model_score=model_score,
+            rule_score=rule_score,
+            detected_indicators=indicators,
+        )
```

---

## 4. Original Three Scenarios Verification (Test A, Test B, Test C)

The original three documents were evaluated via the runtime harness (`eval_scenarios_abc.py`) and direct API endpoints.

```
================================================================================
Scenario A: Suspicious Job Offer (Text)
================================================================================
Submission Type: text
Extracted Text:
Apex Technologies - Junior Software Developer. We are pleased to inform you of your guaranteed selection without an interview for the Junior Software Developer position. To confirm your acceptance, a refundable registration fee of ₹2,500 must be paid immediately. Immediate payment requirement applies to secure your placement in this cohort.

ML Prediction: LEGITIMATE
ML Calibrated Score: 0.1425 (14.25%)
Rule Engine Risk Score: 0.8500 (85.00%)
Composite Risk Level: HIGH
Detected Indicators Count: 3
  1. [CRITICAL] Registration / Onboarding Fee Demand
     Matched Evidence: 'To confirm your acceptance, a refundable registration fee of ₹2,500 must be paid immediately.'
     Explanation: Legitimate employers do not charge candidates a fee to register, apply, or confirm an internship/job offer. Upfront fees are a hallmark indicator of recruitment fraud.
  2. [HIGH] Guaranteed Selection Without Interview
     Matched Evidence: 'We are pleased to inform you of your guaranteed selection without an interview for the Junior Software Developer position.'
     Explanation: Claims of direct appointment, guaranteed selection without an interview or formal technical assessment are typical of fake recruitment schemes seeking fast money transfer.
  3. [HIGH] Urgent Payment Deadline Pressure
     Matched Evidence: 'Immediate payment requirement applies to secure your placement in this cohort.'
     Explanation: Artificial urgency ('transfer immediately', 'within 2 hours to reserve seat') is a psychological pressure tactic intended to prevent candidates from verifying authenticity.
Actionable Recommendations:
  1. Never send money or pay upfront fees for job registration, interviews, or application processing. Legitimate employers do not transfer recruitment overhead costs to candidates.
  2. Treat guaranteed job offers without technical interviews or background validation with skepticism. Legitimate hiring processes involve thorough multi-stage assessments.
  3. Do not yield to artificial urgency or short deadlines (such as 2-hour or same-day payment windows). Scammers create false panic to prevent candidates from verifying claims.
  4. Cross-check the recruitment notice on the organization's official career portal or official LinkedIn page.
  5. Contact the company's official reception or HR department via independently verified telephone numbers.

================================================================================
Scenario B: Suspicious Internship Advertisement (PDF)
================================================================================
Submission Type: pdf
Extracted Text:
Global Infotech Internship Program. Congratulations! You have received guaranteed selection without
an interview for our 2026 Developer Internship. A non-refundable onboarding charge of ?1,999 is
required to initiate your profile. Additionally, a mandatory ?4,000 training charge must be paid for the
induction module. Please submit your identity documents and bank details via Telegram to our HR
coordinator (@InfotechHR). This offer expires within a 2-hour deadline, so payment must be
transferred immediately.

ML Prediction: LEGITIMATE
ML Calibrated Score: 0.0710 (7.10%)
Rule Engine Risk Score: 1.0000 (100.00%)
Composite Risk Level: HIGH
Detected Indicators Count: 6
  1. [CRITICAL] Registration / Onboarding Fee Demand
     Matched Evidence: 'A non-refundable onboarding charge of ?1,999 is required to initiate your profile.'
     Explanation: Legitimate employers do not charge candidates a fee to register, apply, or confirm an internship/job offer. Upfront fees are a hallmark indicator of recruitment fraud.
  2. [CRITICAL] Mandatory Paid Training / Training Charge
     Matched Evidence: 'Additionally, a mandatory ?4,000 training charge must be paid for the induction module.'
     Explanation: Legitimate internships and employment opportunities provide training without charging candidates. Demanding training fees or fees for skill development is an illicit fee-shifting tactic.
  3. [HIGH] Guaranteed Selection Without Interview
     Matched Evidence: 'You have received guaranteed selection without an interview for our 2026 Developer Internship.'
     Explanation: Claims of direct appointment, guaranteed selection without an interview or formal technical assessment are typical of fake recruitment schemes seeking fast money transfer.
  4. [HIGH] Urgent Payment Deadline Pressure
     Matched Evidence: 'This offer expires within a 2-hour deadline, so payment must be transferred immediately.'
     Explanation: Artificial urgency ('transfer immediately', 'within 2 hours to reserve seat') is a psychological pressure tactic intended to prevent candidates from verifying authenticity.
  5. [CRITICAL] Premature Sensitive Financial Document Request
     Matched Evidence: 'Please submit your identity documents and bank details via Telegram to our HR coordinator (@InfotechHR).'
     Explanation: Demanding credit card details, bank credentials, ATM PINs, or original identity/academic documents via informal messaging channels poses an acute identity theft or financial fraud risk.
  6. [MEDIUM] Unofficial Communication Channel for Official Hiring
     Matched Evidence: 'Please submit your identity documents and bank details via Telegram to our HR coordinator (@InfotechHR).'
     Explanation: Official hiring conducted exclusively through informal channels like Telegram groups or personal WhatsApp numbers without verifiable corporate email domains indicates potential scam operations.
Actionable Recommendations:
  1. Never send money or pay upfront fees for job registration, interviews, or application processing. Legitimate employers do not transfer recruitment overhead costs to candidates.
  2. Be cautious of mandatory paid training, onboarding packages, or certification fees required as a prerequisite. Authentic employers invest in employee training at company expense.
  3. Treat guaranteed job offers without technical interviews or background validation with skepticism. Legitimate hiring processes involve thorough multi-stage assessments.
  4. Do not yield to artificial urgency or short deadlines (such as 2-hour or same-day payment windows). Scammers create false panic to prevent candidates from verifying claims.
  5. Never disclose banking passwords, credit card details, OTPs, or send copies of identity documents (Aadhaar, PAN, passport) over informal messaging apps like Telegram or WhatsApp. Submit verification documents only via secure corporate portals.
  6. Insist on official corporate email communication (e.g. name@company.com). Be wary of recruiters operating exclusively through personal Telegram handles or WhatsApp numbers.
  7. Cross-check the recruitment notice on the organization's official career portal or official LinkedIn page.
  8. Contact the company's official reception or HR department via independently verified telephone numbers.

================================================================================
Scenario C: Lower-Risk Internship Offer (PDF)
================================================================================
Submission Type: pdf
Extracted Text:
Acme Systems - Summer Engineering Internship. We invite applications for our competitive
three-month internship program in Software Engineering. Selected interns receive a ?10,000 monthly
stipend and work directly with senior architects. Candidates must complete a technical interview and
practical assessment. No registration fee, security deposit, or application fee is required at any point in
our hiring process. Apply via our official corporate careers portal.

ML Prediction: LEGITIMATE
ML Calibrated Score: 0.1060 (10.60%)
Rule Engine Risk Score: 0.0000 (0.00%)
Composite Risk Level: LOW
Detected Indicators Count: 0
Actionable Recommendations:
  1. Standard diligence recommended: Review employment terms, role expectations, and formal offer letters.
```

### Before vs. After Comparison Matrix

| Metric / Attribute | Scenario A (Job Offer) Before | Scenario A (Job Offer) After | Scenario B (Internship) Before | Scenario B (Internship) After | Scenario C (Legit Offer) Before | Scenario C (Legit Offer) After |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ML Prediction** | LEGITIMATE (0.13) | LEGITIMATE (0.14) | LEGITIMATE (0.09) | LEGITIMATE (0.07) | LEGITIMATE (0.11) | LEGITIMATE (0.11) |
| **Rule Engine Score** | 0.35 | **0.85** | 0.35 | **1.00** | 0.25 (FP) | **0.00** (Clean) |
| **Composite Risk** | MODERATE (Defect) | **HIGH** | MODERATE (Defect) | **HIGH** | MODERATE (Defect) | **LOW** |
| **Detected Red Flags** | 1 indicator | **3 indicators** | 1 indicator | **6 indicators** | 1 indicator (FP) | **0 indicators** |
| **Evidence Extraction** | Entire document | **Clean sentence** | Entire document | **Clean sentences** | Negation quote | **None (Clean)** |
| **Recommendations** | Generic static text | **Tailored & Urgent**| Generic static text | **8 Dynamic Warnings**| Scam warnings | **Standard Diligence**|

---

## 5. 35-Sample Regression Benchmark & Performance Metrics

### Test Distribution
- **Suspicious Recruitment Offers:** 10 samples (extortion fees, deposits, urgent deadlines, informal document surrender).
- **Legitimate Recruitment Offers:** 10 samples (engineering, design, product, support, enterprise roles).
- **Explicit Fee / Deposit Negations:** 5 samples (negative corporate disclaimers and warnings).
- **Multi-Flag Offers:** 5 samples (complex scams combining 3 to 4 distinct red flags).
- **Ambiguous / Safe Edge Cases:** 5 samples (travel reimbursements, training descriptions, joining bonuses, gate security ID checks).

### Execution Output (`backend/tests/run_regression_benchmark.py`)

```
================================================================================
VERIFAI ANALYSIS ENGINE — 35-SAMPLE REGRESSION BENCHMARK
================================================================================
[PASS (TP)   ] SUSP_01_TEST_A               | GT=SUSPICIOUS | Risk=HIGH     | ML=0.14 | Rule=0.85 | Indicators=3
[PASS (TP)   ] SUSP_02_TEST_B               | GT=SUSPICIOUS | Risk=HIGH     | ML=0.07 | Rule=1.00 | Indicators=6
[PASS (TP)   ] SUSP_03_EQUIPMENT_DEPOSIT    | GT=SUSPICIOUS | Risk=HIGH     | ML=0.11 | Rule=0.35 | Indicators=1
[PASS (TP)   ] SUSP_04_DIRECT_APPOINTMENT_UPI | GT=SUSPICIOUS | Risk=HIGH     | ML=0.02 | Rule=0.60 | Indicators=2
[PASS (TP)   ] SUSP_05_PORTAL_ACCESS_FEE    | GT=SUSPICIOUS | Risk=HIGH     | ML=0.97 | Rule=0.35 | Indicators=1
[PASS (TP)   ] SUSP_06_MANDATORY_TRAINING   | GT=SUSPICIOUS | Risk=HIGH     | ML=0.04 | Rule=0.35 | Indicators=1
[PASS (TP)   ] SUSP_07_URGENT_DEADLINE      | GT=SUSPICIOUS | Risk=HIGH     | ML=0.15 | Rule=0.60 | Indicators=2
[PASS (TP)   ] SUSP_08_DOCS_TELEGRAM        | GT=SUSPICIOUS | Risk=HIGH     | ML=0.06 | Rule=0.60 | Indicators=2
[PASS (TP)   ] SUSP_09_SCREENING_FEE        | GT=SUSPICIOUS | Risk=HIGH     | ML=0.19 | Rule=0.35 | Indicators=1
[PASS (TP)   ] SUSP_10_HIGH_EARNINGS        | GT=SUSPICIOUS | Risk=HIGH     | ML=0.78 | Rule=0.35 | Indicators=1
[PASS (TN)   ] LEGIT_01_FRONTEND            | GT=LEGITIMATE | Risk=LOW      | ML=0.03 | Rule=0.00 | Indicators=0
[PASS (TN)   ] LEGIT_02_PRODUCT_MGR         | GT=LEGITIMATE | Risk=LOW      | ML=0.02 | Rule=0.00 | Indicators=0
[PASS (TN)   ] LEGIT_03_DEVOPS              | GT=LEGITIMATE | Risk=LOW      | ML=0.06 | Rule=0.00 | Indicators=0
[PASS (TN)   ] LEGIT_04_DATA_ANALYST        | GT=LEGITIMATE | Risk=LOW      | ML=0.01 | Rule=0.00 | Indicators=0
[PASS (TN)   ] LEGIT_05_SUPPORT             | GT=LEGITIMATE | Risk=LOW      | ML=0.02 | Rule=0.00 | Indicators=0
[PASS (TN)   ] LEGIT_06_QA_AUTOMATION       | GT=LEGITIMATE | Risk=LOW      | ML=0.02 | Rule=0.00 | Indicators=0
[PASS (TN)   ] LEGIT_07_MARKETING           | GT=LEGITIMATE | Risk=LOW      | ML=0.01 | Rule=0.00 | Indicators=0
[PASS (TN)   ] LEGIT_08_SYSADMIN            | GT=LEGITIMATE | Risk=LOW      | ML=0.01 | Rule=0.00 | Indicators=0
[PASS (TN)   ] LEGIT_09_DESIGNER            | GT=LEGITIMATE | Risk=LOW      | ML=0.04 | Rule=0.00 | Indicators=0
[PASS (TN)   ] LEGIT_10_ARCHITECT           | GT=LEGITIMATE | Risk=LOW      | ML=0.01 | Rule=0.00 | Indicators=0
[PASS (TN)   ] NEG_01_TEST_C                | GT=LEGITIMATE | Risk=LOW      | ML=0.11 | Rule=0.00 | Indicators=0
[PASS (TN)   ] NEG_02_SECURITY_DEPOSIT      | GT=LEGITIMATE | Risk=LOW      | ML=0.05 | Rule=0.00 | Indicators=0
[PASS (TN)   ] NEG_03_NO_APPLICATION_FEES   | GT=LEGITIMATE | Risk=LOW      | ML=0.01 | Rule=0.00 | Indicators=0
[PASS (TN)   ] NEG_04_BEWARE_SCAMS          | GT=LEGITIMATE | Risk=LOW      | ML=0.04 | Rule=0.00 | Indicators=0
[PASS (TN)   ] NEG_05_ZERO_COST             | GT=LEGITIMATE | Risk=LOW      | ML=0.02 | Rule=0.00 | Indicators=0
[PASS (TP)   ] MULTI_01_EXTORTION_COMBO     | GT=SUSPICIOUS | Risk=HIGH     | ML=0.03 | Rule=0.85 | Indicators=3
[PASS (TP)   ] MULTI_02_DEPOSIT_AND_DOCS    | GT=SUSPICIOUS | Risk=HIGH     | ML=0.10 | Rule=1.00 | Indicators=3
[PASS (TP)   ] MULTI_03_TRAINING_AND_PRESSURE | GT=SUSPICIOUS | Risk=HIGH     | ML=0.27 | Rule=0.60 | Indicators=2
[PASS (TP)   ] MULTI_04_ONBOARDING_PURCHASE | GT=SUSPICIOUS | Risk=HIGH     | ML=0.02 | Rule=0.75 | Indicators=3
[PASS (TP)   ] MULTI_05_SCREENING_SURRENDER | GT=SUSPICIOUS | Risk=HIGH     | ML=0.10 | Rule=0.60 | Indicators=2
[PASS (TN)   ] EDGE_01_REIMBURSEMENT        | GT=LEGITIMATE | Risk=LOW      | ML=0.09 | Rule=0.00 | Indicators=0
[PASS (TN)   ] EDGE_02_TRAINING_MENTION     | GT=LEGITIMATE | Risk=LOW      | ML=0.02 | Rule=0.00 | Indicators=0
[PASS (TN)   ] EDGE_03_JOINING_BONUS        | GT=LEGITIMATE | Risk=LOW      | ML=0.05 | Rule=0.00 | Indicators=0
[PASS (TN)   ] EDGE_04_PHYSICAL_ID          | GT=LEGITIMATE | Risk=LOW      | ML=0.01 | Rule=0.00 | Indicators=0
[PASS (TN)   ] EDGE_05_EQUIPMENT_PROVISION  | GT=LEGITIMATE | Risk=LOW      | ML=0.02 | Rule=0.00 | Indicators=0

================================================================================
BENCHMARK SUMMARY RESULTS
================================================================================
Total Test Cases Evaluated : 35
True Positives  (TP)       : 15 / 15
True Negatives  (TN)       : 20 / 20
False Positives (FP)       : 0 / 20
False Negatives (FN)       : 0 / 15
--------------------------------------------------------------------------------
Accuracy                   : 100.00%
Precision                  : 100.00%
Recall                     : 100.00%
F1 Score                   : 100.00%
================================================================================

CATEGORY BREAKDOWN:
 - Suspicious          : 10/10 passed (100.0%) | FP=0, FN=0
 - Legitimate          : 10/10 passed (100.0%) | FP=0, FN=0
 - Fee Negation        : 5/5 passed (100.0%) | FP=0, FN=0
 - Multi-Flag          : 5/5 passed (100.0%) | FP=0, FN=0
 - Edge Case           : 5/5 passed (100.0%) | FP=0, FN=0
```

### Metric Calculation Definitions & Confusion Matrix

$$\text{Confusion Matrix} = \begin{pmatrix} \text{TP}=15 & \text{FP}=0 \\ \text{FN}=0 & \text{TN}=20 \end{pmatrix}$$

1. **Accuracy:** Fraction of all predictions that were correct:
   $$\text{Accuracy} = \frac{\text{TP} + \text{TN}}{\text{Total}} = \frac{15 + 20}{35} = 1.000\ (100.0\%)$$
2. **Precision:** Proportion of positive risk escalations that were genuine threats:
   $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}} = \frac{15}{15 + 0} = 1.000\ (100.0\%)$$
3. **Recall (Sensitivity):** Proportion of actual fraudulent offers successfully identified:
   $$\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}} = \frac{15}{15 + 0} = 1.000\ (100.0\%)$$
4. **F1-Score:** Harmonic mean of precision and recall:
   $$\text{F1} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} = 2 \times \frac{1.0 \times 1.0}{2.0} = 1.000\ (100.0\%)$$
5. **False Positive Rate (FPR):** Proportion of legitimate offers incorrectly flagged:
   $$\text{FPR} = \frac{\text{FP}}{\text{FP} + \text{TN}} = \frac{0}{0 + 20} = 0.000\ (0.0\%)$$

> [!NOTE]
> **Data Independence Guarantee:** None of these 35 benchmark test cases were used to fit the TF-IDF vectorizer or train the Linear SVM model (which were trained strictly on the independent 17,880-row EMSCAD dataset). The benchmark evaluates the end-to-end composite pipeline against modern recruitment text patterns.

---

## 6. Complete Test Execution Log

### 1. Backend Test Suite Output
Command: `pytest -p no:anyio backend/tests -v`
```
============================= test session starts =============================
platform win32 -- Python 3.11.3, pytest-8.4.2, pluggy-1.7.0 -- backend\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: c:\Users\User25\OneDrive\ドキュメント\VerifAI
collected 36 items

backend/tests/test_analysis.py::test_analyze_text_legitimate PASSED      [  2%]
backend/tests/test_analysis.py::test_analyze_text_scam_high_risk PASSED  [  5%]
backend/tests/test_analysis.py::test_analyze_text_negation_awareness_api PASSED [  8%]
backend/tests/test_analysis.py::test_analyze_text_too_short PASSED       [ 11%]
backend/tests/test_analysis.py::test_analyze_text_empty PASSED           [ 13%]
backend/tests/test_analysis.py::test_analyze_text_exceeding_max_length PASSED [ 16%]
backend/tests/test_analysis.py::test_analyze_pdf_valid PASSED            [ 19%]
backend/tests/test_analysis.py::test_analyze_pdf_scam PASSED             [ 22%]
backend/tests/test_analysis.py::test_analyze_pdf_empty_pages PASSED      [ 25%]
backend/tests/test_analysis.py::test_analyze_pdf_corrupted_file PASSED   [ 27%]
backend/tests/test_analysis.py::test_analyze_pdf_unsupported_file_type PASSED [ 30%]
backend/tests/test_analysis.py::test_analyze_pdf_oversized_file PASSED   [ 33%]
backend/tests/test_analysis_regression.py::test_scenario_a_suspicious_job_text_integration PASSED [ 36%]
backend/tests/test_analysis_regression.py::test_scenario_b_suspicious_internship_pdf_integration PASSED [ 38%]
backend/tests/test_analysis_regression.py::test_scenario_c_legitimate_internship_pdf_integration PASSED [ 41%]
backend/tests/test_analysis_regression.py::test_full_35_sample_regression_matrix PASSED [ 44%]
backend/tests/test_health.py::test_root_endpoint PASSED                  [ 47%]
backend/tests/test_health.py::test_health_check_endpoint PASSED          [ 50%]
backend/tests/test_history.py::test_history_flow_crud PASSED             [ 52%]
backend/tests/test_history.py::test_get_nonexistent_history_404 PASSED   [ 55%]
backend/tests/test_history.py::test_delete_nonexistent_history_404 PASSED [ 58%]
backend/tests/test_history.py::test_history_pagination_offset PASSED     [ 61%]
backend/tests/test_metrics.py::test_get_model_metrics_available PASSED   [ 63%]
backend/tests/test_metrics.py::test_get_model_metrics_unavailable PASSED [ 66%]
backend/tests/test_prediction.py::test_clean_text_normalization PASSED   [ 69%]
backend/tests/test_prediction.py::test_prediction_service_valid_prediction PASSED [ 72%]
backend/tests/test_prediction.py::test_prediction_service_empty_input_rejected PASSED [ 75%]
backend/tests/test_prediction.py::test_missing_model_handling PASSED     [ 77%]
backend/tests/test_risk_engine.py::test_registration_fee_detection PASSED [ 80%]
backend/tests/test_risk_engine.py::test_negation_handling_no_registration_fee PASSED [ 83%]
backend/tests/test_risk_engine.py::test_negation_handling_disclaimer PASSED [ 86%]
backend/tests/test_risk_engine.py::test_processing_fee_detection PASSED  [ 88%]
backend/tests/test_risk_engine.py::test_security_deposit_detection PASSED [ 91%]
backend/tests/test_risk_engine.py::test_guaranteed_selection_detection PASSED [ 94%]
backend/tests/test_risk_engine.py::test_legitimate_recruitment_text_clean PASSED [ 97%]
backend/tests/test_risk_engine.py::test_multiple_indicators_combination PASSED [100%]

======================== 36 passed, 1 warning in 1.45s ========================
```

### 2. Frontend Production Build Output
Command: `npm --prefix frontend run build`
```
> verifai-frontend@1.0.0 build
> vite build

vite v5.4.21 building for production...
transforming...
✓ 1646 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   1.13 kB │ gzip:  0.63 kB
dist/assets/index-H1vpNpue.css   28.72 kB │ gzip:  5.41 kB
dist/assets/index-D7y9oj4O.js   303.45 kB │ gzip: 92.83 kB
✓ built in 7.37s
```

---

## 7. Frontend Verification & Source vs. Browser Audit

### Distinction Between Code Inspection and Browser Automation
* **Playwright / Puppeteer Status:** No automated browser test framework (`playwright`, `@playwright/test`, or `puppeteer`) is installed in the local Node.js or Python environment. As mandated, we explicitly report that dynamic automated browser-click testing was **not executed** because the driver binaries are not present.
* **Component-Level Source Code Verification:** A rigorous static audit of `frontend/src/pages/ResultsPage.jsx` was conducted to verify that all backend fields are consumed and rendered without distortion:
  1. **Composite Risk Presentation:** Reads `risk_level` from `analysis` and applies appropriate alert badges (`HIGH`, `MODERATE`, `LOW`).
  2. **Dual-Engine Metrics:** The Machine Learning Classifier card displays `(model_score * 100).toFixed(1)%` and `prediction` badge. The Contextual Rule Engine card displays `(rule_risk_score * 100).toFixed(1)%` and `detected_indicators.length`.
  3. **Matched Evidence Isolation:** Lines 337–346 explicitly map over `detected_indicators` and render `ind.matched_evidence` inside a designated `<Quote>` container with distinct monospace italic styling:
     ```jsx
     {ind.matched_evidence && (
       <div className="rounded-lg p-3 bg-white border border-ivory-300 text-xs text-charcoal-800 flex items-start gap-2.5">
         <Quote className="w-4 h-4 text-forest-700 shrink-0 mt-0.5" />
         <div>
           <span className="font-semibold text-charcoal-900 block mb-0.5">Matched Evidence in Text:</span>
           <span className="italic font-mono text-charcoal-700">&quot;{ind.matched_evidence}&quot;</span>
         </div>
       </div>
     )}
     ```
  4. **Dynamic Recommendations:** Lines 352–375 render the array of tailored advice strings generated by `generate_recommendations`.
  5. **State Freshness:** Navigation from `AnalysePage` passes `{ state: { result: data } }` directly to `ResultsPage`, preventing stale cache reuse. Direct URL access (`/results/:id`) triggers an authenticated fetch from `/api/history/:id`.

---

## 8. ML Model Limitations & Transparency Analysis

### Why the Dual-Engine Architecture is Essential
The VerifAI machine learning model was trained on the public EMSCAD dataset (17,880 real-world job advertisements collected between 2012 and 2014, predominantly from the US, UK, and international markets). The model achieves 98.24% test accuracy and 71.13% test recall on that held-out benchmark split.

However, modern recruitment fraud targeting Indian applicants features domain-specific linguistic shifts:
1. **Currency and Payment Rails:** Mentions of `₹2,500`, `₹1,999`, `₹4,000`, `UPI`, `Google Pay`, or `PhonePe` have near-zero feature weights in EMSCAD's historical TF-IDF vocabulary.
2. **Channel Shifts:** Contemporary fraud operates heavily via informal messaging channels (`Telegram @coordinator`, `WhatsApp interview`).
3. **Short-Form Offer Letters:** Many candidate submissions are concise appointment letters (50–150 words) rather than full 1,000-word corporate job descriptions.

Because the ML model alone produces an empirical probability of ~7% to 14% on such text, relying on ML alone would result in catastrophic false negatives. The **Contextual Rule Engine** provides deterministic extortion detection, while the **ML Classifier** screens for broader linguistic deception patterns. The updated composite risk function (`compute_risk_level`) ensures that when unequivocal extortion signals (upfront registration fees, training charges, or sensitive document surrender) are detected, the system immediately protects the user by escalating to `HIGH RISK`.

---

## 9. Remaining Limitations & Recommendations

1. **Scanned / Image-Based PDFs:** The current extraction pipeline uses PyMuPDF (`fitz`), which extracts text streams from vector and digital PDFs. If a user uploads a flattened image scan without embedded text layers, text extraction returns an empty string. Integrating Tesseract OCR in a future release will ensure coverage for scanned documents.
2. **Multi-Lingual Scams:** Current rule patterns are optimized for English-language recruitment notices. Scam offers written in Hindi or regional Indian languages require dedicated multi-lingual regex definitions and tokenizers.
3. **Continuous Domain Re-training:** When an expanded, labeled dataset of modern localized job scam notices becomes available, fine-tuning a transformer or updating the TF-IDF feature space will further elevate the raw ML model score on contemporary scams.

---

## 10. Audit Sign-Off

All defects identified in the original investigation have been resolved:
- **Test A:** Verified `HIGH` risk with 3 detected indicators.
- **Test B:** Verified `HIGH` risk with 6 detected indicators (covering all 5 distinct scam mechanisms).
- **Test C:** Verified `LOW` risk with 0 false positive indicators.
- **All 36 backend tests pass.**
- **Frontend compiles cleanly for production.**
- **No further code changes were made during this audit.**
