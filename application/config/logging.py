"""
Logging Configuration

This module provides logging configuration settings with environment variable support.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class LoggingConfig(BaseSettings):
    """Logging configuration settings."""

    level: str = Field(default="INFO", env="LOG_LEVEL")
    file: Optional[str] = Field(default=None, env="LOG_FILE")
    format: str = Field(default="development", env="LOG_FORMAT")
    max_bytes: int = Field(default=10 * 1024 * 1024, env="LOG_MAX_BYTES")  # 10MB
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")

    class Config:
        env_file = ".env"
        case_sensitive = False
