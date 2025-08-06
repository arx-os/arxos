"""
Cache Configuration

This module provides cache configuration settings with environment variable support.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class CacheConfig(BaseSettings):
    """Cache configuration settings."""

    host: str = Field(default="localhost", env="REDIS_HOST")
    port: int = Field(default=6379, env="REDIS_PORT")
    db: int = Field(default=0, env="REDIS_DB")
    password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    max_connections: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")
    ttl_default: int = Field(default=3600, env="REDIS_TTL_DEFAULT")

    @property
    def connection_string(self) -> str:
        """Get cache connection string."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

    class Config:
        env_file = ".env"
        case_sensitive = False
