"""Configuration management using pydantic-settings."""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class ConfigError(Exception):
    """Raised when required configuration is missing."""
    pass


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = "sqlite:///data/demandflow.db"
    HUEY_URL: str = "sqlite:///data/huey_queue.db"
    LLM_API_KEY: Optional[str] = None
    GIT_REPO_URL: Optional[str] = None
    IM_PLATFORM: Optional[str] = None
    IM_WEBHOOK_SECRET: Optional[str] = None
    MINIO_ENDPOINT: Optional[str] = None
    MINIO_ACCESS_KEY: Optional[str] = None
    MINIO_SECRET_KEY: Optional[str] = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def get_settings() -> Settings:
    """Load settings from environment variables.

    Returns:
        Settings instance with all fields populated.

    Raises:
        ConfigError: If required environment variables are missing.
    """
    try:
        return Settings()
    except Exception as e:
        raise ConfigError(f"Configuration error: {e}") from e
