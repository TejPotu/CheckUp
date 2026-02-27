"""Application configuration via environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from .env / environment."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Google Gemini ---
    google_api_key: str = ""

    # --- Meta WhatsApp Cloud API ---
    meta_whatsapp_token: str = ""
    meta_phone_number_id: str = ""
    meta_verify_token: str = "checkup-verify"
    meta_app_secret: str = ""

    # --- PostgreSQL ---
    database_url: str = "postgresql+asyncpg://checkup:checkup@localhost:5432/checkup"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Qdrant ---
    # Set qdrant_path for local file storage (no Docker needed).
    # Leave empty to connect to a Qdrant server via qdrant_url.
    qdrant_url: str = "http://localhost:6333"
    qdrant_path: str = "./qdrant_data"
    qdrant_collection: str = "elderly_health"

    # --- App ---
    app_env: str = "development"
    log_level: str = "INFO"
    default_language: str = "te"
    checkin_time: str = "09:00"
    timezone: str = "Asia/Kolkata"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
