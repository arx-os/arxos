"""
Arx AI Services Configuration Settings

Environment-based configuration management for AI/ML services.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import structlog

logger = structlog.get_logger()


class AIServiceSettings(BaseSettings):
    """AI Service configuration settings"""

    # Service Configuration
    service_name: str = Field(default="arx-ai-services", description="Service name")
    service_version: str = Field(default="1.0.0", description="Service version")
    debug: bool = Field(default=False, description="Debug mode")

    # API Configuration
    host: str = Field(default="0.0.0.0", description="Host to bind to")
    port: int = Field(default=8001, description="Port to bind to")
    reload: bool = Field(default=True, description="Auto-reload on changes")

    # AI Provider Configuration
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Anthropic API key"
    )

    # Model Configuration
    default_model: str = Field(default="gpt-4", description="Default AI model")
    max_tokens: int = Field(default=1000, description="Maximum tokens for responses")
    temperature: float = Field(default=0.7, description="AI model temperature")

    # Database Configuration
    database_url: Optional[str] = Field(
        default=None, description="Database connection URL"
    )
    redis_url: Optional[str] = Field(
        default="redis://localhost:6379", description="Redis connection URL"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format")

    # Voice Processing Configuration
    voice_sample_rate: int = Field(default=16000, description="Voice sample rate")
    voice_channels: int = Field(default=1, description="Voice channels")
    voice_max_duration: int = Field(
        default=30, description="Maximum voice duration in seconds"
    )

    # Geometry Validation Configuration
    geometry_precision: float = Field(
        default=1e-6, description="Geometry precision tolerance"
    )
    geometry_max_vertices: int = Field(
        default=10000, description="Maximum vertices per geometry"
    )

    # NLP Configuration
    nlp_model: str = Field(default="en_core_web_sm", description="spaCy model to use")
    nlp_cache_size: int = Field(default=1000, description="NLP cache size")

    # Security Configuration
    cors_origins: list = Field(default=["*"], description="CORS allowed origins")
    api_key_header: str = Field(default="X-API-Key", description="API key header name")

    # Monitoring Configuration
    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")
    health_check_interval: int = Field(
        default=30, description="Health check interval in seconds"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings: Optional[AIServiceSettings] = None


def get_settings() -> AIServiceSettings:
    """Get or create settings instance"""
    global _settings

    if _settings is None:
        _settings = AIServiceSettings()
        logger.info(
            "AI Service settings loaded",
            service_name=_settings.service_name,
            version=_settings.service_version,
            host=_settings.host,
            port=_settings.port,
        )

    return _settings


def update_settings(**kwargs) -> AIServiceSettings:
    """Update settings with new values"""
    global _settings

    if _settings is None:
        _settings = get_settings()

    for key, value in kwargs.items():
        if hasattr(_settings, key):
            setattr(_settings, key, value)
            logger.info(f"Updated setting: {key} = {value}")

    return _settings


def validate_settings() -> bool:
    """Validate required settings"""
    settings = get_settings()

    # Check required API keys
    if not settings.openai_api_key and not settings.anthropic_api_key:
        logger.warning("No AI provider API keys configured")
        return False

    # Check database configuration
    if not settings.database_url:
        logger.warning("No database URL configured")

    # Check Redis configuration
    if not settings.redis_url:
        logger.warning("No Redis URL configured")

    return True


# Environment variable mappings
ENV_MAPPINGS = {
    "OPENAI_API_KEY": "openai_api_key",
    "ANTHROPIC_API_KEY": "anthropic_api_key",
    "DATABASE_URL": "database_url",
    "REDIS_URL": "redis_url",
    "LOG_LEVEL": "log_level",
    "DEBUG": "debug",
    "HOST": "host",
    "PORT": "port",
}


def load_from_env():
    """Load settings from environment variables"""
    settings = get_settings()

    for env_var, setting_name in ENV_MAPPINGS.items():
        env_value = os.getenv(env_var)
        if env_value is not None:
            if hasattr(settings, setting_name):
                setattr(settings, setting_name, env_value)
                logger.info(
                    f"Loaded {setting_name} from environment variable {env_var}"
                )

    return settings
