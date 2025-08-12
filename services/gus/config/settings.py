"""
Gus Service Configuration Settings

This module manages configuration for the Gus AI service using
environment variables and pydantic settings.
"""

import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field, validator
from enum import Enum


class Environment(str, Enum):
    """Application environment"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    LOCAL = "local"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Uses pydantic BaseSettings for automatic env var loading and validation.
    """
    
    # Application
    app_name: str = Field(default="Gus AI Service", env="APP_NAME")
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API Settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    cors_origins: str = Field(default="*", env="CORS_ORIGINS")
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    jwt_secret: str = Field(default="your-jwt-secret", env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiry_hours: int = Field(default=24, env="JWT_EXPIRY_HOURS")
    
    # Database
    database_url: str = Field(
        default="postgresql://arxos:arxos@localhost:5432/arxos_db",
        env="DATABASE_URL"
    )
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=40, env="DATABASE_MAX_OVERFLOW")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_ttl: int = Field(default=3600, env="REDIS_TTL")
    
    # LLM Configuration
    llm_provider: LLMProvider = Field(default=LLMProvider.OPENAI, env="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4-turbo-preview", env="LLM_MODEL")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    azure_openai_endpoint: Optional[str] = Field(default=None, env="AZURE_OPENAI_ENDPOINT")
    azure_openai_key: Optional[str] = Field(default=None, env="AZURE_OPENAI_KEY")
    
    # LLM Parameters
    llm_temperature: float = Field(default=0.7, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2000, env="LLM_MAX_TOKENS")
    llm_top_p: float = Field(default=1.0, env="LLM_TOP_P")
    llm_frequency_penalty: float = Field(default=0.0, env="LLM_FREQUENCY_PENALTY")
    llm_presence_penalty: float = Field(default=0.0, env="LLM_PRESENCE_PENALTY")
    llm_timeout: int = Field(default=30, env="LLM_TIMEOUT")
    llm_retry_count: int = Field(default=3, env="LLM_RETRY_COUNT")
    
    # Vector Database
    vector_db_provider: str = Field(default="chroma", env="VECTOR_DB_PROVIDER")
    chroma_persist_dir: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIR")
    chroma_collection_name: str = Field(default="arxos_knowledge", env="CHROMA_COLLECTION_NAME")
    pinecone_api_key: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(default=None, env="PINECONE_ENVIRONMENT")
    pinecone_index: Optional[str] = Field(default=None, env="PINECONE_INDEX")
    
    # Knowledge Base
    knowledge_base_path: str = Field(default="./knowledge", env="KNOWLEDGE_BASE_PATH")
    knowledge_chunk_size: int = Field(default=1000, env="KNOWLEDGE_CHUNK_SIZE")
    knowledge_chunk_overlap: int = Field(default=200, env="KNOWLEDGE_CHUNK_OVERLAP")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="RATE_LIMIT_WINDOW")
    rate_limit_burst: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    # Conversation Management
    conversation_max_messages: int = Field(default=50, env="CONVERSATION_MAX_MESSAGES")
    conversation_ttl_hours: int = Field(default=24, env="CONVERSATION_TTL_HOURS")
    conversation_max_tokens: int = Field(default=4000, env="CONVERSATION_MAX_TOKENS")
    
    # ArxObject Integration
    arxobject_api_url: str = Field(default="http://localhost:8080", env="ARXOBJECT_API_URL")
    arxobject_api_key: Optional[str] = Field(default=None, env="ARXOBJECT_API_KEY")
    
    # Monitoring
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    tracing_enabled: bool = Field(default=False, env="TRACING_ENABLED")
    tracing_endpoint: Optional[str] = Field(default=None, env="TRACING_ENDPOINT")
    
    # Feature Flags
    enable_streaming: bool = Field(default=True, env="ENABLE_STREAMING")
    enable_function_calling: bool = Field(default=True, env="ENABLE_FUNCTION_CALLING")
    enable_knowledge_base: bool = Field(default=True, env="ENABLE_KNOWLEDGE_BASE")
    enable_query_translation: bool = Field(default=True, env="ENABLE_QUERY_TRANSLATION")
    enable_analytics: bool = Field(default=True, env="ENABLE_ANALYTICS")
    
    class Config:
        """Pydantic config"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("cors_origins")
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string"""
        if v == "*":
            return ["*"]
        return [origin.strip() for origin in v.split(",")]
    
    @validator("llm_temperature")
    def validate_temperature(cls, v):
        """Validate temperature is in valid range"""
        if not 0 <= v <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        return v
    
    @validator("llm_provider")
    def validate_llm_credentials(cls, v, values):
        """Validate that required API keys are present for provider"""
        if v == LLMProvider.OPENAI and not values.get("openai_api_key"):
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OpenAI API key required for OpenAI provider")
        elif v == LLMProvider.ANTHROPIC and not values.get("anthropic_api_key"):
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise ValueError("Anthropic API key required for Anthropic provider")
        elif v == LLMProvider.AZURE_OPENAI:
            if not values.get("azure_openai_endpoint") or not values.get("azure_openai_key"):
                raise ValueError("Azure OpenAI endpoint and key required")
        return v
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration as dictionary"""
        return {
            "provider": self.llm_provider,
            "model": self.llm_model,
            "api_key": self._get_llm_api_key(),
            "api_base": self._get_llm_api_base(),
            "temperature": self.llm_temperature,
            "max_tokens": self.llm_max_tokens,
            "top_p": self.llm_top_p,
            "frequency_penalty": self.llm_frequency_penalty,
            "presence_penalty": self.llm_presence_penalty,
            "timeout": self.llm_timeout,
            "retry_count": self.llm_retry_count
        }
    
    def _get_llm_api_key(self) -> Optional[str]:
        """Get appropriate API key for LLM provider"""
        if self.llm_provider == LLMProvider.OPENAI:
            return self.openai_api_key
        elif self.llm_provider == LLMProvider.ANTHROPIC:
            return self.anthropic_api_key
        elif self.llm_provider == LLMProvider.AZURE_OPENAI:
            return self.azure_openai_key
        return None
    
    def _get_llm_api_base(self) -> Optional[str]:
        """Get API base URL for LLM provider"""
        if self.llm_provider == LLMProvider.AZURE_OPENAI:
            return self.azure_openai_endpoint
        return None
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            "url": self.database_url,
            "pool_size": self.database_pool_size,
            "max_overflow": self.database_max_overflow
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration"""
        return {
            "url": self.redis_url,
            "ttl": self.redis_ttl
        }
    
    def get_rate_limit_config(self) -> Dict[str, Any]:
        """Get rate limiting configuration"""
        return {
            "enabled": self.rate_limit_enabled,
            "requests": self.rate_limit_requests,
            "window": self.rate_limit_window,
            "burst": self.rate_limit_burst
        }
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == Environment.DEVELOPMENT


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings singleton instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings():
    """Reload settings (useful for testing)"""
    global _settings
    _settings = Settings()