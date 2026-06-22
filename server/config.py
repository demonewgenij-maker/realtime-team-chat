"""Environment-driven configuration.

Read fresh from env each call so tests can override DATABASE_PATH after import.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_path: str
    token_ttl_min: int
    cors_origins: list[str]


def get_settings() -> Settings:
    """Build settings from the current environment (not cached -> test-friendly)."""
    origins = os.getenv("CORS_ORIGINS", "*")
    return Settings(
        secret_key=os.getenv("SECRET_KEY", "dev-secret-change-me"),
        database_path=os.getenv("DATABASE_PATH", "chat.db"),
        token_ttl_min=int(os.getenv("TOKEN_TTL_MIN", "1440")),
        cors_origins=[o.strip() for o in origins.split(",") if o.strip()],
    )
