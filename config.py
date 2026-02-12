"""
Configuration settings for the Business Backend application.

Uses Pydantic for settings management with environment variable support.
"""

import logging
from pydantic import Field
from pydantic.networks import PostgresDsn
from pydantic_settings import BaseSettings
from logging_config import get_logger

logger = get_logger(__name__)


class BusinessSettings(BaseSettings):
    """
    Business Backend settings.

    Loads configuration from environment variables or defaults.
    """

    # Database settings
    pg_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:admin123@localhost:5432/inventario_db",
        env="DATABASE_URL",
        description="PostgreSQL database URL for async connections"
    )

    # Application settings
    app_name: str = Field(default="Business Backend API", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")

    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=5000, env="PORT")

    class Config:
        env_file = ".env"
        case_sensitive = False


def get_business_settings() -> BusinessSettings:
    """
    Get business settings instance.

    Returns:
        BusinessSettings: Configured settings object
    """
    logger.debug("Loading business settings from environment")
    settings = BusinessSettings()
    logger.info(f"Business settings loaded - Host: {settings.host}, Port: {settings.port}, Debug: {settings.debug}")
    return settings