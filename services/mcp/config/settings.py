"""
MCP Service Settings Configuration

Configuration settings for the MCP service including API settings,
logging configuration, and service parameters.
"""

import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """MCP Service Settings"""
    
    # Service settings
    service_name: str = "MCP Service"
    version: str = "1.0.0"
    
    # API settings
    host: str = "0.0.0.0"
    port: int = 8001
    debug: bool = False
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"
    
    # MCP settings
    mcp_data_path: str = "mcp"
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hour
    
    # Performance settings
    max_concurrent_validations: int = 10
    validation_timeout: int = 300  # 5 minutes
    
    # Database settings (if needed)
    database_url: Optional[str] = None
    
    # External service settings
    redis_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_prefix = "MCP_"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings 