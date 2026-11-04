"""Text preprocessing utilities for the VerifAI ML pipeline.

This module provides consistent text cleaning and normalization across both
the training pipeline and the real-time inference service.
"""

from __future__ import annotations

import html
import re
from typing import Sequence
import pandas as pd

# Regex patterns for text cleaning
HTML_TAG_PATTERN = re.compile(r"<[^>]+?>")
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
MULTIPLE_SPACES_PATTERN = re.compile(r"\s+")
SPECIAL_CHARS_PATTERN = re.compile(r"[^\w\s\$\€\£\₹\%\.\,\!\?\-]")

# Standard text columns used in EMSCAD training
DEFAULT_TEXT_COLUMNS = [
    "title",
    "company_profile",
    "description",
    "requirements",
    "benefits",
]


def clean_text(text: str | None) -> str:
    """Clean and normalize raw text for ML model inference and training.

    Args:
        text: Raw input string or None.

    Returns:
        Cleaned, normalized lowercase string.
    """
    if text is None:
        return ""

    if not isinstance(text, str):
        text = str(text)

    # Decode HTML entities (e.g., &amp; -> &, &nbsp; -> ' ')
    text = html.unescape(text)

    # Strip HTML tags common in job posting datasets
    text = HTML_TAG_PATTERN.sub(" ", text)

    # Normalize URLs and emails to preserve context without noise
    text = URL_PATTERN.sub(" ", text)
    text = EMAIL_PATTERN.sub(" ", text)

    # Strip non-standard characters while preserving punctuation and currency
    text = SPECIAL_CHARS_PATTERN.sub(" ", text)

    # Normalize excessive whitespace
    text = MULTIPLE_SPACES_PATTERN.sub(" ", text)

    # Lowercase and strip boundaries
    return text.strip().lower()


def combine_text_fields(
    df: pd.DataFrame,
    columns: Sequence[str] | None = None,
) -> pd.Series:
    """Combine multiple tabular text columns into a single unified text series.

    Args:
        df: Input pandas DataFrame.
        columns: List of column names to combine. Defaults to DEFAULT_TEXT_COLUMNS.

    Returns:
        pd.Series containing the cleaned, concatenated text for each row.
    """
    if columns is None:
        columns = DEFAULT_TEXT_COLUMNS

    available_cols = [col for col in columns if col in df.columns]
    if not available_cols:
        raise ValueError(f"None of the requested columns {columns} exist in DataFrame.")

    combined = df[available_cols].fillna("").astype(str).agg(" ".join, axis=1)
    return combined.apply(clean_text)
