"""Recruitment-content relevance validation service for VerifAI.

Distinguishes genuine, suspicious, and informal recruitment advertisements, job postings,
and offer letters from unrelated documents (novels, scientific papers, essays, invoices,
certificates, and candidate resumes) before execution of ML inference and risk scoring.
"""

from __future__ import annotations

import logging
import re
from typing import Tuple
from fastapi import HTTPException, status

HTTP_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)

logger = logging.getLogger("VerifAI.Services.RelevanceValidator")


class RelevanceValidator:
    """Deterministic, multi-signal validator for recruitment content."""

    # -------------------------------------------------------------
    # Anti-Patterns (Strong Non-Recruitment Signatures)
    # -------------------------------------------------------------
    INVOICE_PATTERNS = [
        r"\b(?:tax\s+)?invoice\b",
        r"\bbill\s+to\b",
        r"\bship\s+to\b",
        r"\binvoice\s*(?:no|number|#|date)\b",
        r"\bgstin\b",
        r"\bhsn(?:[/ ]sac)?\b",
        r"\btotal\s+(?:amount\s+)?payable\b",
        r"\bbalance\s+due\b",
        r"\bpayment\s+terms:\s*net\b",
        r"\bcgst\b|\bsgst\b|\bigst\b",
        r"\bunit\s+price\b",
        r"\bqty\b|\bquantity\b",
        r"\bsubtotal\b",
    ]

    CERTIFICATE_PATTERNS = [
        r"\bcertificate\s+of\s+(?:completion|achievement|appreciation|excellence|participation|training|merit)\b",
        r"\bthis\s+is\s+to\s+certify\s+that\b",
        r"\bis\s+hereby\s+awarded\s+to\b",
        r"\bhas\s+successfully\s+completed\b",
        r"\bin\s+recognition\s+of\b",
        r"\bdate\s+of\s+issuance\b",
        r"\bcertificate\s+id\b|\bcredential\s+id\b",
        r"\bcourse\s+director\b|\binstructor\s+signature\b",
    ]

    RESEARCH_PAPER_PATTERNS = [
        r"\babstract\b",
        r"\bmethodology\b",
        r"\bconclusions?\b",
        r"\breferences\s*\n\s*\[\d+\]|\bdoi:\s*10\.\d+",
        r"\barxiv:\s*\d+\.\d+",
        r"\bet\s+al\.",
        r"\bfigure\s+\d+\s*:",
        r"\btable\s+\d+\s*:",
        r"\bbranching\s+fraction\b|\bcross[\s-]section\b|\bstatistical\s+significance\b",
    ]

    RESUME_PATTERNS = [
        r"\b(?:curriculum\s+vitae|resume|c\.v\.|biodata)\b",
        r"\bcareer\s+objective\b",
        r"\bprofessional\s+summary\b",
        r"\bacademic\s+(?:qualifications|background|profile)\b",
        r"\beducational\s+(?:qualifications|background|details)\b",
        r"\btechnical\s+skills\b",
        r"\bprojects\s+(?:undertook|handled|completed)\b",
        r"\bdeclaration\s*:\s*i\s+hereby\s+declare\b",
        r"\bpersonal\s+details\b|\bdate\s+of\s+birth\b",
    ]

    # Explicit Employer/Hiring Actions (Distinguishes job offers from candidate resumes)
    EMPLOYER_ACTIONS = [
        r"\bwe\s+are\s+(?:hiring|recruiting|seeking|looking\s+for)\b",
        r"\bwe\'re\s+hiring\b|\bnow\s+hiring\b|\burgently?\s+hiring\b",
        r"\bwe\s+seek\b|\bwe\s+offer\b",
        r"\bapply\s+(?:now|here|via|online|directly|today)\b|\bhow\s+to\s+apply\b",
        r"\b(?:send|forward|share|submit)\s+(?:your\s+)?(?:resume|cv|application)\b",
        r"\bpleased\s+to\s+(?:offer|inform)\b|\bhappy\s+to\s+offer\b|\bdelighted\s+to\s+offer\b",
        r"\boffer\s+of\s+(?:employment|appointment)\b|\bemployment\s+offer\b|\bjob\s+offer\b",
        r"\bcongratulations\s+on\s+your\s+(?:selection|appointment|direct\s+joining)\b",
        r"\bguaranteed\s+selection\s+without\s+(?:an?\s+)?interview\b",
        r"\bdirect\s+(?:selection|appointment|joining)\s+without\s+(?:an?\s+)?interview\b",
        r"\binvite\s+applications\b|\bapplications\s+are\s+invited\b",
        r"\blooking\s+for\s+\d+\s+[a-zA-Z]+",
    ]

    # -------------------------------------------------------------
    # Positive Recruitment Signals
    # -------------------------------------------------------------
    # 1. Hiring Intent & Recruitment Context
    RECRUITMENT_CONTEXT_PATTERNS = [
        r"\b(?:we\s+are|we\'re|now|urgently?)\s+(?:hiring|recruiting)\b",
        r"\b(?:we\s+are\s+)?(?:seeking|looking\s+for)\s+(?:an?\s+)?(?:experienced|qualified|talented|dynamic|motivated|candidate|freshers?|interns?|engineers?|developers?|\d+)\b",
        r"\bwe\s+seek\b|\bwe\s+offer\b",
        r"\burgent\s+(?:requirement|opening|recruitment|hiring)\b",
        r"\bimmediate\s+(?:requirement|opening|joining|hiring|placement)\b",
        r"\b(?:job|career|internship)\s+(?:opening|openings|opportunity|opportunities|vacancy|vacancies|announcement|program)\b",
        r"\bcareers?\s+at\b",
        r"\bjoin\s+our\s+(?:team|squad|company|firm|organization|division)\b",
        r"\bjoin\s+us\b",
        r"\bwalk[\s-]in\s+(?:interview|drive)\b",
        r"\b(?:direct|guaranteed)\s+(?:selection|appointment|joining)\b",
        r"\boffer\s+of\s+(?:employment|appointment)\b|\bemployment\s+offer\b|\bjob\s+offer\b",
        r"\boffer\s+letter\b|\bappointment\s+letter\b|\bletter\s+of\s+appointment\b",
        r"\bpleased\s+to\s+(?:offer|inform)\b|\bhappy\s+to\s+offer\b|\bdelighted\s+to\s+offer\b",
        r"\bcongratulations\s+on\s+your\s+(?:selection|appointment|direct\s+joining)\b",
        r"\bselected\s+for\s+(?:the\s+)?(?:position|role|program)\b",
        r"\bshortlisted\s+for\s+(?:the\s+)?(?:position|role|program)\b",
        r"\binvite\s+applications\b|\bapplications\s+are\s+invited\b",
        r"\bapply\s+(?:now|here|via|online|directly|today)\b",
        r"\bhow\s+to\s+apply\b",
        r"\b(?:send|forward|share|submit)\s+(?:your\s+)?(?:resume|cv|application)\b",
        r"\binterested\s+candidates\b|\beligible\s+candidates\b",
        r"\bcontact\s+(?:hr|recruiter|coordinator)\b",
        r"\bhiring\s+(?:for|coordinator)\b",
        r"\b(?:summer|winter|graduate|developer|engineering)\s+internship\b",
        r"\b(?:interview|selection|hiring)\s+(?:process|involves|comprises|schedule|rounds?)\b",
        r"\b(?:technical|coding|hr|onsite|partner)\s+interview\b",
        r"\bcandidates?\s+(?:undergo|must|attending|traveling|selected|will|are\s+not\s+required)\b",
        r"\b(?:upon|before|prior\s+to)\s+joining\b",
        r"\bdate\s+of\s+joining\b|\bjoining\s+date\b",
        r"\bnew\s+team\s+member\b",
        r"\bapprenticeship\b|\bfellowship\b",
        r"\bour\s+company\s+never\s+charges\b|\bno\s+registration\s+fee\b",
    ]

    # 2. Roles & Titles
    ROLE_PATTERNS = [
        r"\b(?:software|backend|frontend|full[\s-]?stack|web|mobile|devops|cloud|systems?|qa|test|infrastructure|site\s+reliability|reliability)\s+(?:engineer|developer|architect|specialist|administrator)\b",
        r"\b(?:data|business|financial|security|operations|research|clinical\s+research|virtual\s+operations|field)\s+analyst\b",
        r"\b(?:product|project|program|engineering|account|sales|marketing)\s+manager\b",
        r"\b(?:data\s+entry|typing)\s+(?:operator|specialist|executive)\b",
        r"\b(?:customer\s+service|customer\s+support|customer\s+success|sales|field|marketing)\s+(?:executive|representative|associate|specialist|strategist)\b",
        r"\b(?:content\s+writer|copywriter|ui[\s\-/]?ux\s+(?:visual\s+)?designer|graphic\s+designer)\b",
        r"\b(?:consultant|specialist|associate|coordinator|administrator|executive|officer|assistant|clerk|strategist|architect)\b",
        r"\b(?:intern|internship|trainee|fellow|fellowship|apprentice|apprenticeship)\b",
        r"\b(?:senior|junior|lead|principal|staff|enterprise)\s+(?:[a-zA-Z]+\s+)*(?:engineer|developer|consultant|analyst|specialist|architect|strategist|designer)\b",
        r"\b(?:role|position|designation|job\s+title)\s*:\s*[a-zA-Z]",
    ]

    # 3. Structure & Job Description Sections
    STRUCTURE_PATTERNS = [
        r"\b(?:job\s+description|role\s+overview|about\s+the\s+role)\b",
        r"\bresponsibilities\s*:",
        r"\bresponsible\s+for\b",
        r"\bkey\s+responsibilities\b",
        r"\brequirements\s*:",
        r"\brequires\s+[a-zA-Z]",
        r"\bqualifications\s*:",
        r"\b(?:minimum|preferred)\s+qualifications\b",
        r"\beligibility(?:\s+criteria)?\s*:",
        r"\bskills\s+required\s*:",
        r"\bwho\s+can\s+apply\s*:",
        r"\bwhat\s+you(?:\'ll|\s+will)\s+do\b",
        r"\bjob\s+summary\b",
    ]

    # 4. Compensation & Work Arrangement
    COMPENSATION_PATTERNS = [
        r"\b(?:salary|stipend|ctc|remuneration|compensation|allowance|reimbursement)\b",
        r"\b(?:per\s+month|per\s+annum|per\s+week|\/month|\/mo|\/yr|lpa)\b",
        r"\b(?:earn\s+(?:₹|\$|\d+)|daily\s+earning|weekly\s+payout)\b",
        r"\b(?:₹|\$|inr)\s*[\d,]+",
        r"\b(?:full[\s-]time|part[\s-]time|work\s+from\s+home|wfh|remote|hybrid|onsite)\b",
        r"\b(?:health\s+insurance|joining\s+bonus|provident\s+fund|performance\s+incentives?|annual\s+package)\b",
        r"\bergonomics?\s+allowance\b|\bworkstation\b|\bcompany[\s-]provided\b",
    ]

    # 5. Scam Recruitment Markers (Must ACCEPT for scam analysis)
    SCAM_RECRUITMENT_PATTERNS = [
        r"\bguaranteed\s+selection\s+without\s+(?:an?\s+)?interview\b",
        r"\bdirect\s+(?:selection|appointment|joining)\s+without\s+(?:an?\s+)?interview\b",
        r"\bregistration\s+fee\b|\bonboarding\s+(?:fee|charge)\b|\btraining\s+(?:fee|charge)\b",
        r"\brefundable\s+security\s+deposit\b|\bequipment\s+deposit\b",
        r"\bportal\s+administration\s+fee\b|\bprocessing\s+fee\b|\bscreening\s+fee\b|\bverification\s+fee\b",
        r"\bearn\s+(?:₹|\$)?\d+\s+daily\s+for\s+typing\b",
        r"\bpart[\s-]time\s+typing\s+specialist\b",
        r"\bwork\s+\d+\s+hours?\s+daily\s+from\s+home\b",
        r"\bsend\s+(?:your\s+)?(?:identity\s+documents|bank\s+details|documents(?:\s+and\s+bank\s+details)?)\b.*?\b(?:telegram|whatsapp)\b",
        r"\bimmediate\s+payment\s+requirement\b",
    ]

    @classmethod
    def validate(cls, text: str) -> Tuple[bool, str, str]:
        """Validate whether the text constitutes a recruitment-related document.

        Args:
            text: Raw input text from pasted submission or extracted PDF.

        Returns:
            Tuple of (is_valid, error_code, error_message).
            - If valid: (True, "", "")
            - If invalid: (False, "UNRELATED_DOCUMENT" | "INSUFFICIENT_CONTENT", descriptive message)
        """
        if not text or not text.strip():
            return (
                False,
                "INSUFFICIENT_CONTENT",
                "Input text is empty. Please submit a valid recruitment notice or job offer.",
            )

        cleaned = text.strip()
        words = cleaned.split()
        lower_text = cleaned.lower()

        # -------------------------------------------------------------
        # 1. Negative Domain Filter (Anti-patterns)
        # -------------------------------------------------------------
        # A. Invoice Check
        invoice_matches = sum(1 for p in cls.INVOICE_PATTERNS if re.search(p, lower_text))
        if invoice_matches >= 3 and not any(re.search(p, lower_text) for p in cls.EMPLOYER_ACTIONS):
            return (
                False,
                "UNRELATED_DOCUMENT",
                "This document appears to be a commercial invoice or billing receipt rather than a recruitment opportunity. "
                "Please submit a job posting, recruitment notice, or employment offer.",
            )

        # B. Certificate Check
        cert_matches = sum(1 for p in cls.CERTIFICATE_PATTERNS if re.search(p, lower_text))
        if cert_matches >= 2 or re.search(r"\bthis\s+is\s+to\s+certify\s+that\b", lower_text):
            return (
                False,
                "UNRELATED_DOCUMENT",
                "This document appears to be a course completion or achievement certificate rather than a recruitment opportunity. "
                "Please submit a job posting, recruitment notice, or employment offer.",
            )

        # C. Research Paper Check
        paper_matches = sum(1 for p in cls.RESEARCH_PAPER_PATTERNS if re.search(p, lower_text))
        if paper_matches >= 3 and not any(re.search(p, lower_text) for p in cls.EMPLOYER_ACTIONS):
            return (
                False,
                "UNRELATED_DOCUMENT",
                "This document appears to be an academic research paper or scientific publication rather than a recruitment opportunity. "
                "Please submit a job posting, recruitment notice, or employment offer.",
            )

        # D. Resume / CV Check
        # Resumes describe the job seeker, not an employer hiring or offering a job.
        resume_matches = sum(1 for p in cls.RESUME_PATTERNS if re.search(p, lower_text))
        has_employer_action = any(re.search(p, lower_text) for p in cls.EMPLOYER_ACTIONS)
        if (resume_matches >= 2 or re.search(r"\b(?:curriculum\s+vitae|resume)\b", lower_text)) and not has_employer_action:
            return (
                False,
                "UNRELATED_DOCUMENT",
                "This document appears to be a candidate resume or curriculum vitae (CV) rather than a recruitment opportunity or job offer. "
                "Please submit a job posting, recruitment notice, or offer letter.",
            )

        # -------------------------------------------------------------
        # 2. Positive Recruitment Signal Evaluation
        # -------------------------------------------------------------
        context_score = sum(1 for p in cls.RECRUITMENT_CONTEXT_PATTERNS if re.search(p, lower_text))
        role_score = sum(1 for p in cls.ROLE_PATTERNS if re.search(p, lower_text))
        structure_score = sum(1 for p in cls.STRUCTURE_PATTERNS if re.search(p, lower_text))
        comp_score = sum(1 for p in cls.COMPENSATION_PATTERNS if re.search(p, lower_text))
        scam_score = sum(1 for p in cls.SCAM_RECRUITMENT_PATTERNS if re.search(p, lower_text))

        # Check Rule 1: Explicit Scam Recruitment (immediate accept for scam analysis)
        if scam_score >= 1 and (context_score >= 1 or role_score >= 1 or comp_score >= 1):
            return True, "", ""

        # Check Rule 2: Recruitment context + Role
        if context_score >= 1 and role_score >= 1:
            return True, "", ""

        # Check Rule 3: Recruitment context + Compensation or Structure
        if context_score >= 1 and (comp_score >= 1 or structure_score >= 1):
            return True, "", ""

        # Check Rule 4: Structure (Responsibilities/Requirements) + Role
        if structure_score >= 1 and role_score >= 1:
            return True, "", ""

        # Check Rule 5: Role + Compensation + Work arrangement (informal short ads)
        if role_score >= 1 and comp_score >= 2:
            return True, "", ""

        # Check Rule 6: Strong recruitment context alone (≥2 distinct context markers)
        if context_score >= 2:
            return True, "", ""

        # Check Rule 7: Role + at least 1 compensation marker (e.g. Staff SRE + compensation/bonus)
        if role_score >= 1 and comp_score >= 1:
            return True, "", ""

        # -------------------------------------------------------------
        # 3. Short / Ambiguous Content Check
        # -------------------------------------------------------------
        total_signals = context_score + role_score + structure_score + comp_score + scam_score
        if len(cleaned) < 120 or len(words) < 20:
            return (
                False,
                "INSUFFICIENT_CONTENT",
                "The provided text is too short or ambiguous to establish recruitment context. "
                "Please submit a complete job posting, internship advertisement, or employment offer.",
            )

        # Long document without any recruitment signals (e.g. literary novels, general essays)
        return (
            False,
            "UNRELATED_DOCUMENT",
            "This doesn't appear to be a job posting, recruitment notice, or employment offer. "
            "Please submit a recruitment-related document.",
        )


def validate_recruitment_relevance(text: str) -> None:
    """Validate recruitment relevance and raise HTTP 422 if unrelated or insufficient.

    Args:
        text: Input text to validate.

    Raises:
        HTTPException: HTTP 422 with structured error code and explanatory message if content is not recruitment-related.
    """
    is_valid, error_code, error_message = RelevanceValidator.validate(text)
    if not is_valid:
        logger.warning(
            "Recruitment relevance check failed [Code=%s]: %s (text preview: %.80s...)",
            error_code,
            error_message,
            text.replace("\n", " "),
        )
        raise HTTPException(
            status_code=HTTP_422,
            detail={
                "code": error_code,
                "message": error_message,
            },
        )
