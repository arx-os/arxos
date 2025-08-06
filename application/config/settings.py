"""
Main Application Settings

This module provides the main application configuration using Pydantic settings
for type safety and environment variable support.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from .database import DatabaseConfig
from .cache import CacheConfig
from .logging import LoggingConfig
from .message_queue import MessageQueueConfig


class Settings(BaseSettings):
    """Main application settings with environment variable support."""

    # Application settings
    app_name: str = "Arxos Platform"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", env="ARXOS_ENV")
    debug: bool = Field(default=False, env="ARXOS_DEBUG")

    # API settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")

    # Security settings
    secret_key: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, env="ACCESS_TOKEN_EXIRE_MINUTES"
    )

    # Database configuration
    database: DatabaseConfig = DatabaseConfig()

    # Cache configuration
    cache: CacheConfig = CacheConfig()

    # Message queue configuration
    message_queue: MessageQueueConfig = MessageQueueConfig()

    # Logging configuration
    logging: LoggingConfig = LoggingConfig()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
