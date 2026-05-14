"""Application settings loaded from environment and optional `.env` file."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent


class Settings(BaseSettings):
    """Central config — avoids scattered `os.getenv` and documents env vars."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str | None = Field(default=None, description="OpenAI secret key")
    openai_model: str = Field(default="gpt-4o-mini")
    llm_temperature: float = Field(default=0.2, ge=0.0, le=2.0)
