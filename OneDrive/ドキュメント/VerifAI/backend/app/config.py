"""VerifAI configuration management using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Any, List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base backend directory: .../backend
BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "VerifAI"
    app_env: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS configuration
    cors_origins: Union[List[str], str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:4173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:4173",
        ]
    )

    @field_validator("cors_origins", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        """Parse comma-separated or JSON list strings into a list of origins."""
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                import json
                return json.loads(v_str)
            return [origin.strip() for origin in v_str.split(",") if origin.strip()]
        return list(v)

    # Database
    database_url: str = f"sqlite:///{BACKEND_DIR / 'verifai.db'}"

    # ML Artifacts
    model_path: str = str(BACKEND_DIR / "ml" / "saved_model" / "model.joblib")
    metrics_path: str = str(BACKEND_DIR / "ml" / "saved_model" / "metrics.json")

    # Upload limitations
    max_upload_size_mb: int = 10

    @property
    def max_upload_size_bytes(self) -> int:
        """Maximum file size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def resolved_model_path(self) -> Path:
        """Absolute Path to the trained ML model."""
        p = Path(self.model_path)
        if not p.is_absolute():
            p = BACKEND_DIR / p
        return p

    @property
    def resolved_metrics_path(self) -> Path:
        """Absolute Path to the model metrics JSON."""
        p = Path(self.metrics_path)
        if not p.is_absolute():
            p = BACKEND_DIR / p
        return p


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
