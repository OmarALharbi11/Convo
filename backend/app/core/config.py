"""
Application configuration loaded from environment variables via Pydantic Settings.

All sensitive values (secrets, API keys) must be supplied via environment
variables or a .env file.  Defaults are only provided for non-sensitive,
environment-specific settings.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "insecure-dev-secret-change-in-production-immediately"
    BACKEND_BASE_URL: str = "http://localhost:8000"
    FRONTEND_BASE_URL: str = "http://localhost:5173"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"

    # ------------------------------------------------------------------
    # Azure AD / Microsoft Graph
    # ------------------------------------------------------------------
    AZURE_TENANT_ID: str = ""
    AZURE_CLIENT_ID: str = ""
    AZURE_CLIENT_SECRET: str = ""

    # Role assignment (comma-separated email lists)
    MANAGER_EMAILS: str = ""
    ADMIN_EMAILS: str = ""

    # ------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------
    OPENAI_API_KEY: str = ""

    # ------------------------------------------------------------------
    # Feature flags
    # ------------------------------------------------------------------
    USE_MOCK_GRAPH: bool = True
    USE_MOCK_STT: bool = True
    USE_MOCK_TTS: bool = True
    USE_LLM_INTENT: bool = False

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str = "sqlite+aiosqlite:///./ipa.db"

    # ------------------------------------------------------------------
    # JWT
    # ------------------------------------------------------------------
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    LOG_LEVEL: str = "INFO"

    # ------------------------------------------------------------------
    # Computed properties
    # ------------------------------------------------------------------

    @property
    def GRAPH_SCOPES(self) -> list[str]:
        """Minimal Microsoft Graph OAuth 2.0 scopes — least privilege."""
        return [
            "User.Read",
            "Mail.Read",
            "Mail.Send",
            "Calendars.ReadWrite",
            "offline_access",
        ]

    @property
    def is_mock_mode(self) -> bool:
        """True when no real Azure credentials are configured."""
        return not bool(self.AZURE_CLIENT_ID)

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("APP_SECRET_KEY")
    @classmethod
    def secret_key_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "APP_SECRET_KEY must be at least 32 characters long. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance.  Use this everywhere instead of
    instantiating Settings() directly so the .env file is only parsed once."""
    return Settings()
