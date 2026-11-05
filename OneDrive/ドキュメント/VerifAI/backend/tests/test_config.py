"""Unit tests for VerifAI application configuration and CORS origin handling."""

from __future__ import annotations

import os
from typing import List
import pytest

from app.config import Settings


def test_default_cors_origins_includes_preview_ports():
    """Verify default CORS origins contain both 5173 (dev) and 4173 (preview) ports."""
    settings = Settings()
    origins = settings.cors_origins

    assert isinstance(origins, list)
    # Check new preview ports
    assert "http://localhost:4173" in origins
    assert "http://127.0.0.1:4173" in origins

    # Check preserved existing ports
    assert "http://localhost:3000" in origins
    assert "http://localhost:5173" in origins
    assert "http://127.0.0.1:3000" in origins
    assert "http://127.0.0.1:5173" in origins
    assert len(origins) == 6


def test_cors_origins_env_override_comma_separated(monkeypatch):
    """Verify CORS_ORIGINS environment variable can override defaults via comma-separated string."""
    monkeypatch.setenv("CORS_ORIGINS", "http://custom-preview.local:4173, http://verifai.org")
    settings = Settings()
    origins = settings.cors_origins

    assert origins == ["http://custom-preview.local:4173", "http://verifai.org"]


def test_cors_origins_env_override_json_format(monkeypatch):
    """Verify CORS_ORIGINS environment variable can override defaults via JSON array format."""
    monkeypatch.setenv("CORS_ORIGINS", '["http://staging.verifai.app", "http://localhost:4173"]')
    settings = Settings()
    origins = settings.cors_origins

    assert origins == ["http://staging.verifai.app", "http://localhost:4173"]


def test_cors_origins_handles_trailing_commas_and_whitespace(monkeypatch):
    """Verify whitespace and trailing commas in CORS_ORIGINS are stripped cleanly."""
    monkeypatch.setenv("CORS_ORIGINS", " http://site1.com , http://site2.com, , ")
    settings = Settings()
    origins = settings.cors_origins

    assert origins == ["http://site1.com", "http://site2.com"]

