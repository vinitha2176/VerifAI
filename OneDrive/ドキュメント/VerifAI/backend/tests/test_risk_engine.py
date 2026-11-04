"""Tests for rule-based risk detection and negation handling."""

from app.services.risk_engine import RiskEngine


def test_registration_fee_detection() -> None:
    """Verify that explicit registration fee demands are flagged as critical."""
    engine = RiskEngine()
    text = "Pay ₹2,500 as a registration fee to confirm your internship seat."
    score, indicators, evidence = engine.evaluate(text)

    assert score > 0.3
    names = [ind.indicator_name for ind in indicators]
    assert any("Registration" in n for n in names)
    assert any("2,500" in ev or "registration fee" in ev.lower() for ev in evidence)


def test_negation_handling_no_registration_fee() -> None:
    """Crucial requirement: 'There is no registration fee' must NOT trigger a warning."""
    engine = RiskEngine()
    text = (
        "Welcome to our summer internship program. "
        "There is no registration fee for this internship. "
        "Selected candidates will receive a monthly stipend of $2,000."
    )
    score, indicators, evidence = engine.evaluate(text)

    names = [ind.indicator_name for ind in indicators]
    assert not any("Registration" in n for n in names)
    assert score == 0.0


def test_negation_handling_disclaimer() -> None:
    """Verify company anti-scam disclaimers do not trigger false positive fee rules."""
    engine = RiskEngine()
    text = (
        "Careers at ACME Corp. "
        "Disclaimer: We never ask candidates for any registration fee or application fee. "
        "Do not pay any money to recruitment agents."
    )
    score, indicators, evidence = engine.evaluate(text)

    names = [ind.indicator_name for ind in indicators]
    assert not any("Registration" in n for n in names)
    assert not any("Processing" in n for n in names)


def test_processing_fee_detection() -> None:
    """Check application and screening processing fee detection."""
    engine = RiskEngine()
    text = "Candidates are required to pay a processing fee of $150 before the interview."
    score, indicators, evidence = engine.evaluate(text)

    assert score > 0.3
    names = [ind.indicator_name for ind in indicators]
    assert any("Processing" in n for n in names)


def test_security_deposit_detection() -> None:
    """Verify laptop/security deposit demands are flagged."""
    engine = RiskEngine()
    text = "Selected applicants must submit a refundable security deposit of 5000 for company laptop."
    score, indicators, evidence = engine.evaluate(text)

    names = [ind.indicator_name for ind in indicators]
    assert any("Security" in n for n in names)


def test_guaranteed_selection_detection() -> None:
    """Verify guaranteed selection without interview is flagged."""
    engine = RiskEngine()
    text = "Congratulations! You are selected without any interview for the position."
    score, indicators, evidence = engine.evaluate(text)

    names = [ind.indicator_name for ind in indicators]
    assert any("Without Interview" in n for n in names)


def test_legitimate_recruitment_text_clean() -> None:
    """Legitimate job posting without scam keywords should trigger zero indicators."""
    engine = RiskEngine()
    text = (
        "We are hiring a Frontend React Developer in Tokyo. "
        "Requirements include 3+ years experience with TypeScript and Tailwind CSS. "
        "We offer comprehensive medical insurance and flexible hybrid working arrangements."
    )
    score, indicators, evidence = engine.evaluate(text)

    assert score == 0.0
    assert len(indicators) == 0
    assert len(evidence) == 0


def test_multiple_indicators_combination() -> None:
    """Verify combination of multiple red flags yields a cumulative score."""
    engine = RiskEngine()
    text = (
        "Congratulations! You are selected without any interview! "
        "Pay 2000 rupees as registration fee immediately today to confirm your seat. "
        "Also send your credit card details and deposit 5000 for training kit."
    )
    score, indicators, evidence = engine.evaluate(text)

    assert len(indicators) >= 3
    assert score >= 0.70

