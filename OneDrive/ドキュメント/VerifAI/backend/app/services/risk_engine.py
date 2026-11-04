"""Rule-based risk detection engine for VerifAI.

Operates independently of the ML classifier to identify specific recruitment
red flags and scam indicators with contextual awareness, robust negation handling,
and exact sentence-level evidence extraction.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Tuple
from app.schemas.analysis import DetectedIndicator

# Comprehensive negative declaration patterns for fee and deposit contexts
COMMON_FEE_NEGATION_PATTERNS = [
    re.compile(r"\bno\s+.*(?:is|are)\s+(?:required|needed|charged|demanded|asked|taken)\b", re.IGNORECASE),
    re.compile(
        r"\bno\s+(?:registration|application|processing|screening|onboarding|security|training|equipment|internship)?\s*"
        r"(?:fee|fees|charges?|cost|deposit|caution|payment)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:there\s+is\s+no|there\s+are\s+no)\s+.*(?:fee|deposit|charge|cost|payment)\b", re.IGNORECASE),
    re.compile(r"\b(?:candidates?|applicants?|students?)\s+(?:are|is)\s+not\s+required\s+to\s+pay\b", re.IGNORECASE),
    re.compile(r"\b(?:will\s+never\s+be|are\s+never|is\s+never|never\s+be)\s+(?:asked|required|requested)\s+(?:for|to\s+pay)?\b", re.IGNORECASE),
    re.compile(r"\b(?:we\s+do\s+not|do\s+not|never|company\s+never|does\s+not)\s+(?:ask|charge|require|demand|collect).*(?:fee|deposit|charge|payment|money)\b", re.IGNORECASE),
    re.compile(r"\b(?:do\s+not|never)\s+pay\s+(?:any\s+)?(?:money|fee|deposit|charge)\b", re.IGNORECASE),
    re.compile(r"\bno\s+payment\s+(?:is\s+)?(?:required|needed)\s+at\s+any\s+stage\b", re.IGNORECASE),
    re.compile(r"\b(?:free\s+of\s+cost|at\s+no\s+(?:cost|charge)|at\s+zero\s+cost|zero\s+fees?)\b", re.IGNORECASE),
    re.compile(r"\bwithout\s+(?:any\s+)?(?:fee|fees|deposit|charges?|cost|payment)\b", re.IGNORECASE),
]


def split_into_clean_clauses(text: str) -> List[str]:
    """Segment raw text into clean, individual sentence and clause units.

    Normalizes soft wraps (e.g. from PDF column formatting) while respecting
    sentence delimiters, paragraph boundaries, and bullet point prefixes.
    """
    # Step 1: Un-wrap soft line breaks inside paragraphs (common in PDF extracted text)
    # A newline not preceded by [.!?:] and not followed by a bullet symbol, number, or newline
    normalized = re.sub(r"(?<![.!?:\n])\n(?!\n|[\s]*[•\-\*\–—\d\.\)])", " ", text)

    raw_lines = re.split(r"[\r\n]+", normalized)
    clauses: List[str] = []
    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        # Strip leading bullet symbols or numbering markers (e.g. '• ', '- ', '1. ')
        line = re.sub(r"^[\s\-\*•–—\d\.\)]+", "", line).strip()
        if not line:
            continue
        # Split on sentence terminators followed by whitespace
        parts = re.split(r"(?<=[.!?])\s+", line)
        for p in parts:
            p = p.strip()
            if len(p) >= 3:
                clauses.append(p)
    return clauses


class RiskRule:
    """Represents a modular suspicious indicator rule with contextual negation handling."""

    def __init__(
        self,
        rule_id: str,
        name: str,
        severity: str,
        weight: float,
        explanation: str,
        positive_patterns: List[str],
        negation_patterns: Optional[List[str]] = None,
        is_fee_rule: bool = False,
    ) -> None:
        self.rule_id = rule_id
        self.name = name
        self.severity = severity
        self.weight = weight
        self.explanation = explanation
        self.positive_regexes = [re.compile(p, re.IGNORECASE) for p in positive_patterns]
        self.negation_regexes = (
            [re.compile(p, re.IGNORECASE) for p in negation_patterns]
            if negation_patterns
            else []
        )
        self.is_fee_rule = is_fee_rule

    def evaluate_sentence(self, sentence: str) -> Optional[str]:
        """Backward-compatible alias for evaluate_clause."""
        return self.evaluate_clause(sentence)

    def evaluate_clause(self, clause: str) -> Optional[str]:
        """Check if a clause triggers the rule while respecting negation contexts.

        Args:
            clause: Individual sentence or clause string.

        Returns:
            The exact matched evidence string if triggered, or None if safe/negated.
        """
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

        # Step 3: Check hierarchical fee negation patterns if applicable
        if self.is_fee_rule:
            for fee_neg in COMMON_FEE_NEGATION_PATTERNS:
                if fee_neg.search(clause):
                    return None

        # Step 4: Clean evidence extraction
        evidence = re.sub(r"^[\s\-\*•–—\d\.\)]+", "", clause).strip()
        return evidence


def build_default_rules() -> List[RiskRule]:
    """Instantiate the comprehensive rule catalog covering recruitment fraud patterns."""
    return [
        RiskRule(
            rule_id="REGISTRATION_FEE",
            name="Registration / Onboarding Fee Demand",
            severity="CRITICAL",
            weight=0.35,
            explanation=(
                "Legitimate employers do not charge candidates a fee to register, apply, "
                "or confirm an internship/job offer. Upfront fees are a hallmark indicator of recruitment fraud."
            ),
            positive_patterns=[
                r"(?:pay|deposit|transfer|remit|charge|fee\s+of|charges?\s+of)\s*(?:₹|rs\.?|\$|usd|inr)?\s*\d+.*(?:registration|onboarding|enrolment|enrollment|confirmation|booking)",
                r"(?:registration|onboarding|enrolment|enrollment|confirmation|booking)\s+(?:fee|fees|charges?|cost|amount)",
                r"(?:pay|deposit|remit)\s+.*(?:registration\s+fee|onboarding\s+fee|enrolment\s+fee)",
                r"(?:non-refundable|refundable)\s+(?:onboarding|registration|enrolment)\s+(?:fee|charges?|cost)",
                r"(?:fee|charge)\s+to\s+(?:confirm|book|register\s+for)\s+(?:your\s+)?(?:internship|seat|position|job)",
                r"(?:mandatory|required)\s+(?:registration|onboarding)\s+(?:fee|charge)",
            ],
            negation_patterns=[
                r"\b(?:no|without\s+any|zero)\s+(?:registration|onboarding|enrolment|enrollment)\s+(?:fee|charges?|cost)\b",
                r"\b(?:there\s+is\s+no|there\s+are\s+no)\s+(?:registration|onboarding|enrolment).*(?:fee|charges?)\b",
                r"\bno\s+.*(?:registration|onboarding|enrolment).*(?:is\s+)?(?:required|charged|needed|demanded)\b",
                r"\b(?:candidates?|applicants?)\s+(?:are|is)\s+not\s+required\s+to\s+pay.*(?:registration|onboarding)\b",
                r"\bnever\s+(?:ask|charge|demand).*(?:registration|onboarding|fee)\b",
                r"\b(?:we\s+do\s+not|do\s+not\s+pay|never\s+pay).*(?:registration|onboarding|fee)\b",
                r"\bno\s+fee\s+is\s+charged\b",
                r"\bno\s+payment\s+(?:is\s+)?(?:required|needed)\s+at\s+any\s+stage\b",
                r"\bfree\s+of\s+cost\b",
            ],
            is_fee_rule=True,
        ),
        RiskRule(
            rule_id="PROCESSING_FEE",
            name="Application / Processing Fee Requirement",
            severity="CRITICAL",
            weight=0.35,
            explanation=(
                "Demanding processing, interview, test, or administrative fees from job candidates "
                "is standard scam behavior. Reputable hiring processes do not charge applicants."
            ),
            positive_patterns=[
                r"(?:application|processing|screening|interview|exam|test|portal|administration|verification)\s+(?:fee|fees|charges?|cost|deposit)",
                r"(?:pay|deposit|transfer|remit)\s+(?:the\s+)?(?:application|processing|screening|verification)\s+(?:fee|charges?)",
                r"(?:pay|deposit|transfer|remit)\s+(?:₹|rs\.?|\$|usd|inr)?\s*\d+.*(?:processing|interview|screening|application)",
                r"(?:application|processing)\s+charge\s+of",
            ],
            negation_patterns=[
                r"\b(?:no|without\s+any|zero)\s+(?:application|processing|screening|interview|exam)\s+(?:fee|charges?|cost)\b",
                r"\b(?:there\s+is\s+no|there\s+are\s+no)\s+(?:application|processing|screening).*(?:fee|charges?)\b",
                r"\bno\s+.*(?:application|processing|screening).*(?:is\s+)?(?:required|charged|needed|demanded)\b",
                r"\bnever\s+(?:ask|charge|demand).*(?:processing|application\s+fee)\b",
                r"\b(?:we\s+do\s+not|do\s+not\s+pay|never\s+pay).*(?:processing|application\s+fee)\b",
                r"\bno\s+fee\s+is\s+charged\b",
                r"\bno\s+payment\s+(?:is\s+)?(?:required|needed)\s+at\s+any\s+stage\b",
            ],
            is_fee_rule=True,
        ),
        RiskRule(
            rule_id="TRAINING_FEE",
            name="Mandatory Paid Training / Training Charge",
            severity="CRITICAL",
            weight=0.35,
            explanation=(
                "Legitimate internships and employment opportunities provide training without charging candidates. "
                "Demanding training fees or fees for skill development is an illicit fee-shifting tactic."
            ),
            positive_patterns=[
                r"(?:training|skill\s+development|curriculum|course|bootcamp)\s+(?:fee|fees|charges?|cost|amount)",
                r"(?:pay|deposit|remit)\s+(?:₹|rs\.?|\$|usd|inr)?\s*\d+.*(?:training|skill\s+development|curriculum|course)",
                r"(?:additional|mandatory)\s+(?:₹|rs\.?|\$|usd|inr)?\s*\d+\s+training\s+charge",
                r"(?:pay|charge)\s+for\s+(?:the\s+)?(?:training|skill\s+development)",
                r"paid\s+training\s+(?:program|course|session|curriculum)",
                r"training\s+charge\s+is\s+mandatory",
            ],
            negation_patterns=[
                r"\b(?:no|without\s+any|zero)\s+training\s+(?:fee|charges?|cost)\b",
                r"\bfree\s+(?:training|skill\s+development)\b",
                r"\btraining\s+(?:is\s+)?(?:provided\s+)?(?:free\s+of\s+cost|at\s+no\s+cost)\b",
                r"\bcompany\s+provides\s+(?:free\s+)?training\b",
                r"\bno\s+.*training\s+(?:fee|charges?).*(?:is\s+)?(?:required|charged|needed)\b",
            ],
            is_fee_rule=True,
        ),
        RiskRule(
            rule_id="SECURITY_DEPOSIT",
            name="Security / Equipment Deposit Demand",
            severity="CRITICAL",
            weight=0.35,
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
            negation_patterns=[
                r"\bcompany\s+(?:provides|furnishes|covers)\s+(?:all\s+)?equipment\b",
                r"\bno\s+deposit\s+is\s+required\b",
            ],
            is_fee_rule=True,
        ),
        RiskRule(
            rule_id="PAYMENT_BEFORE_JOINING",
            name="Compulsory Payment or Purchase Before Joining",
            severity="HIGH",
            weight=0.25,
            explanation=(
                "Requiring candidates to purchase software licenses, work kits, or uniforms before joining "
                "is an illicit fee shifting tactic frequently used in employment scams."
            ),
            positive_patterns=[
                r"(?:purchase|buy|pay\s+for)\s+(?:your\s+own\s+)?(?:software\s+license|id\s+card|uniform|badge|kit)\s+before\s+(?:joining|start|commencing)",
                r"pay\s+before\s+(?:joining|commencing|starting|onboarding)",
                r"candidate\s+must\s+(?:pay|purchase|invest)\s+before\s+joining",
            ],
            negation_patterns=[
                r"company\s+provides",
                r"free\s+of\s+cost",
                r"at\s+no\s+(?:cost|charge)",
                r"(?:do\s+not|never)\s+pay\s+before\s+joining",
            ],
            is_fee_rule=True,
        ),
        RiskRule(
            rule_id="GUARANTEED_SELECTION",
            name="Guaranteed Selection Without Interview",
            severity="HIGH",
            weight=0.25,
            explanation=(
                "Claims of direct appointment, guaranteed selection without an interview or formal technical assessment "
                "are typical of fake recruitment schemes seeking fast money transfer."
            ),
            positive_patterns=[
                r"(?:guaranteed|direct|assured)\s+(?:selection|appointment|joining|hiring|placement)\s+without\s+(?:an?\s+)?(?:interview|test|screening|assessment)",
                r"(?:selected|hired|appointed|offer\s+issued|job\s+confirmed|seat\s+confirmed)\s+without\s+(?:any\s+)?(?:interview|test|screening|assessment)",
                r"selection\s+without\s+(?:an?\s+)?interview",
                r"appointment\s+without\s+(?:an?\s+)?interview",
                r"no\s+interview\s+(?:required|needed|conducted)\s*[,.-]?\s*(?:direct\s+selection|direct\s+joining|direct\s+appointment|guaranteed)",
                r"direct\s+(?:joining|selection|appointment)\s+without\s+(?:an?\s+)?interview",
                r"guaranteed\s+selection\s+(?:for|in)\s+(?:the|this)",
            ],
            negation_patterns=[
                r"\binterview\s+is\s+mandatory\b",
                r"\bmust\s+clear\s+(?:the\s+)?interview\b",
                r"\bconditional\s+(?:on|upon)\s+(?:an?\s+)?interview\b",
                r"\b(?:not|cannot\s+be)\s+selected\s+without\s+interview\b",
                r"\btechnical\s+interview\s+and\s+(?:practical\s+)?assessment\b",
                r"\bsubject\s+to\s+interview\b",
            ],
        ),
        RiskRule(
            rule_id="URGENT_PAYMENT_DEMAND",
            name="Urgent Payment Deadline Pressure",
            severity="HIGH",
            weight=0.25,
            explanation=(
                "Artificial urgency ('transfer immediately', 'within 2 hours to reserve seat') "
                "is a psychological pressure tactic intended to prevent candidates from verifying authenticity."
            ),
            positive_patterns=[
                r"(?:pay|transfer|remit|deposit)\s+(?:immediately|urgently|within\s+\d+\s+hours|today\s+itself)",
                r"(?:fee|charge|deposit|amount|payment)\s+must\s+be\s+(?:paid|deposited|transferred|remitted)\s+immediately",
                r"immediate\s+payment\s+(?:requirement|demanded|needed|mandatory)",
                r"within\s+(?:a\s+)?\d+[\s\-]hours?\s+(?:deadline|window|time)",
                r"(?:deadline|valid\s+for|expire\s+in)\s*[:\-]?\s*(?:within\s+)?\d+[\s\-]hours?",
                r"(?:pay|transfer|deposit|register)\s+within\s+\d+\s+hours?\s+to\s+(?:secure|hold|confirm|reserve)\s+(?:your\s+)?(?:slot|seat|position)",
                r"urgent\s+(?:payment|transfer|fee\s+submission)\s+required",
            ],
            negation_patterns=[
                r"(?:do\s+not|never)\s+(?:pay|transfer)",
                r"take\s+your\s+time",
            ],
        ),
        RiskRule(
            rule_id="SENSITIVE_DOCUMENTS_REQUEST",
            name="Premature Sensitive Financial Document Request",
            severity="CRITICAL",
            weight=0.35,
            explanation=(
                "Demanding credit card details, bank credentials, ATM PINs, or original identity/academic documents "
                "via informal messaging channels poses an acute identity theft or financial fraud risk."
            ),
            positive_patterns=[
                r"(?:send|submit|share|upload|provide)\s+.*(?:identity\s+documents|id\s+proof|aadhar|pan\s+card|passport\s+copy|bank\s+details|bank\s+account)\s+.*(?:via|on|through)\s+(?:telegram|whatsapp)",
                r"(?:send|submit|share|upload|provide)\s+(?:your\s+)?(?:credit\s+card|debit\s+card|bank\s+pin|atm\s+pin|net\s+banking\s+password|cvv)",
                r"(?:submit|deposit|surrender)\s+original\s+(?:degree|certificates?|marksheet|passport)\s+before\s+joining",
                r"(?:identity\s+documents|bank\s+details|aadhar\s+card)\s+.*(?:via|on)\s+(?:telegram|whatsapp)",
            ],
            negation_patterns=[
                r"(?:do\s+not|never)\s+share\s+(?:passwords?|pin|card|bank\s+details)",
                r"we\s+will\s+never\s+ask\s+for\s+(?:pin|credit\s+card|password|bank\s+details)",
            ],
        ),
        RiskRule(
            rule_id="SUSPICIOUS_COMMUNICATION_CHANNEL",
            name="Unofficial Communication Channel for Official Hiring",
            severity="MEDIUM",
            weight=0.15,
            explanation=(
                "Official hiring conducted exclusively through informal channels like Telegram groups "
                "or personal WhatsApp numbers without verifiable corporate email domains indicates potential scam operations."
            ),
            positive_patterns=[
                r"(?:official\s+interview|official\s+hiring|hiring\s+process)\s+(?:conducted\s+)?(?:only\s+)?(?:on|via)\s+(?:telegram|whatsapp)",
                r"(?:submit|send|contact)\s+.*(?:via|on)\s+(?:telegram|whatsapp)\s+to\s+(?:our\s+)?(?:hr|recruitment|coordinator)",
                r"contact\s+hr\s+(?:only\s+)?on\s+telegram\s+@[\w\d_]+",
                r"official\s+communication\s+(?:conducted\s+)?via\s+(?:telegram|whatsapp)",
            ],
            negation_patterns=[
                r"we\s+do\s+not\s+(?:use|conduct\s+interviews\s+via)\s+telegram",
                r"beware\s+of\s+telegram",
                r"never\s+communicate\s+via\s+telegram",
            ],
        ),
        RiskRule(
            rule_id="UNREALISTIC_SALARY",
            name="Unrealistic Earnings for Unskilled Work",
            severity="MEDIUM",
            weight=0.15,
            explanation=(
                "Promising disproportionately high daily or hourly compensation for basic, part-time, "
                "or data entry tasks is a prevalent recruitment trap."
            ),
            positive_patterns=[
                r"(?:earn|salary\s+of|pay\s+of)\s*(?:₹|rs\.?|\$|usd|inr)?\s*(?:[4-9]\d{4,}|[1-9]\d{5,})\s*per\s+(?:day|daily|hour|hr|week)",
                r"earn\s+\$\s*[1-9]\d{2,}\s*per\s+day\s+working\s+\d+\s*hours?",
                r"typing\s+(?:jobs?|work)\s+earn\s*(?:₹|\$)\s*[1-9]\d{3,}\s*daily",
            ],
            negation_patterns=[
                r"(?:per\s+annum|per\s+year|p\.a\.|annual)",
            ],
        ),
        RiskRule(
            rule_id="GUARANTEED_PLACEMENT",
            name="100% Placement / Job Guarantee",
            severity="MEDIUM",
            weight=0.15,
            explanation=(
                "Unconditional '100% placement guarantee' claims are often used by predatory "
                "training institutes or fraudulent agencies to mislead vulnerable applicants."
            ),
            positive_patterns=[
                r"(?:100%|guaranteed|assured)\s+(?:job\s+placement|job\s+offer|employment|placement\s+guarantee)",
                r"guaranteed\s+(?:placement|job|offer\s+letter)",
            ],
            negation_patterns=[
                r"not\s+guaranteed",
                r"cannot\s+guarantee",
                r"no\s+guarantee",
                r"subject\s+to\s+(?:performance|interview|criteria)",
            ],
        ),
    ]


class RiskEngine:
    """Independent rule-based risk evaluation service."""

    def __init__(self, rules: Optional[List[RiskRule]] = None) -> None:
        self.rules = rules or build_default_rules()

    def split_sentences(self, text: str) -> List[str]:
        """Split raw text into clean, individual sentence and clause segments."""
        return split_into_clean_clauses(text)

    def evaluate(self, text: str) -> Tuple[float, List[DetectedIndicator], List[str]]:
        """Analyze text against all configured rules with negation sensitivity.

        Args:
            text: Recruitment or offer document text.

        Returns:
            Tuple of:
            - rule_risk_score: Float between 0.0 and 1.0
            - detected_indicators: List of DetectedIndicator models
            - evidence_list: Distinct matching sentences
        """
        clauses = self.split_sentences(text)
        detected_indicators: List[DetectedIndicator] = []
        evidence_set: set[str] = set()
        accumulated_score: float = 0.0

        for rule in self.rules:
            matched_sentences: List[str] = []
            for clause in clauses:
                evidence = rule.evaluate_clause(clause)
                if evidence:
                    matched_sentences.append(evidence)
                    evidence_set.add(evidence)

            if matched_sentences:
                # Use the clearest matched sentence as primary evidence
                primary_evidence = matched_sentences[0]
                detected_indicators.append(
                    DetectedIndicator(
                        indicator_name=rule.name,
                        severity=rule.severity,
                        explanation=rule.explanation,
                        matched_evidence=primary_evidence,
                    )
                )
                accumulated_score += rule.weight

        # Normalize score between 0.0 and 1.0
        normalized_score = min(round(accumulated_score, 4), 1.0)
        evidence_list = list(evidence_set)

        return normalized_score, detected_indicators, evidence_list
