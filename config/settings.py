"""Centralized configuration using pydantic-settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    google_api_key: str = ""
    model_name: str = "gemini-2.5-flash"
    temperature: float = 0.1
    max_tokens: int = 4096
    memory_window_size: int = 3
    log_file_path: str = str(BASE_DIR / "data" / "logs.txt")
    max_agent_iterations: int = 6
    agent_retry_attempts: int = 2


settings = Settings()
