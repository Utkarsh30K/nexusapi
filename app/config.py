"""
Configuration management for NexusAPI.

Uses pydantic-settings for environment variable management.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://nexususer:nexuspass@localhost:5432/nexusapi"
    DEBUG: bool = True

    # App
    APP_NAME: str = "NexusAPI"
    APP_VERSION: str = "1.0.0"

    # Security
    JWT_SECRET_KEY: str = "change-me-in-production-use-strong-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    # OAuth (fill in when ready)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"


# Global settings instance
settings = Settings()
