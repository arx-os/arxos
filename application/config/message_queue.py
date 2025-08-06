"""
Message Queue Configuration

This module provides message queue configuration settings with environment variable support.
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class MessageQueueConfig(BaseSettings):
    """Message queue configuration settings."""

    host: str = Field(default="localhost", env="MQ_HOST")
    port: int = Field(default=5672, env="MQ_PORT")
    username: Optional[str] = Field(default=None, env="MQ_USERNAME")
    password: Optional[str] = Field(default=None, env="MQ_PASSWORD")
    virtual_host: str = Field(default="/", env="MQ_VIRTUAL_HOST")

    @property
    def connection_string(self) -> str:
        """Get message queue connection string."""
        if self.username and self.password:
            return f"amqp://{self.username}:{self.password}@{self.host}:{self.port}/{self.virtual_host}"
        return f"amqp://{self.host}:{self.port}/{self.virtual_host}"

    class Config:
        env_file = ".env"
        case_sensitive = False
