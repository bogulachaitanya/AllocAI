"""Application configuration via Pydantic BaseSettings.

All values are read from environment variables or a .env file.
No secrets are hard-coded here.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LLMProvider(StrEnum):
    GROQ = "groq"
    OPENAI = "openai"


class HindsightAdapter(StrEnum):
    LOCAL = "local"
    REMOTE = "remote"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_env: AppEnv = Field(default=AppEnv.DEVELOPMENT, description="Runtime environment")
    app_secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for session signing",
    )

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite:///./projectmind.db",
        description="SQLAlchemy connection string",
    )

    # ── LLM Provider ─────────────────────────────────────────────────────────
    llm_provider: LLMProvider = Field(default=LLMProvider.GROQ)
    llm_model: str = Field(default="openai/gpt-oss-120b")
    llm_fallback_model: str = Field(default="openai/gpt-oss-20b")
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=4096, ge=256, le=32768)

    # Groq
    groq_api_key: str = Field(default="", description="Groq API key")
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1")

    # ── Hindsight ────────────────────────────────────────────────────────────
    hindsight_adapter: HindsightAdapter = Field(default=HindsightAdapter.LOCAL)
    hindsight_api_key: str = Field(default="")
    hindsight_base_url: str = Field(default="")

    # ── RAG ──────────────────────────────────────────────────────────────────
    chroma_db_path: str = Field(default="./chroma_data")
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    rag_top_k: int = Field(default=5, ge=1, le=20)

    # ── Seed ─────────────────────────────────────────────────────────────────
    seed_employee_count: int = Field(default=150, ge=10, le=500)

    # ── Security ─────────────────────────────────────────────────────────────
    admin_users: str = Field(default="admin")

    @field_validator("app_secret_key")
    @classmethod
    def warn_default_secret(cls, v: str) -> str:
        if v == "change-me-in-production":
            import warnings

            warnings.warn(
                "APP_SECRET_KEY is using the default value. Set a strong secret in production.",
                stacklevel=2,
            )
        return v

    @property
    def admin_users_list(self) -> list[str]:
        return [u.strip() for u in self.admin_users.split(",") if u.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnv.PRODUCTION

    @property
    def is_testing(self) -> bool:
        return self.app_env == AppEnv.TESTING


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return _settings


# Module-level singleton; re-read on import.
_settings = Settings()
