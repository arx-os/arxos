"""
Configuration management using Pydantic Settings
Following 12-factor app principles with environment variables
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    APP_NAME: str = "Arxos AI Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")
    
    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql://arxos:arxos@localhost/arxos",
        env="DATABASE_URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=20, env="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=40, env="DATABASE_MAX_OVERFLOW")
    
    # Redis settings
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    REDIS_TTL: int = Field(default=3600, env="REDIS_TTL")  # 1 hour
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8080",
            "http://localhost:8000"
        ],
        env="ALLOWED_ORIGINS"
    )
    
    # AI Processing settings
    PDF_MAX_SIZE_MB: int = Field(default=100, env="PDF_MAX_SIZE_MB")
    PDF_PROCESSING_TIMEOUT: int = Field(default=60, env="PDF_PROCESSING_TIMEOUT")
    
    # Confidence thresholds
    CONFIDENCE_HIGH_THRESHOLD: float = Field(default=0.85, env="CONFIDENCE_HIGH_THRESHOLD")
    CONFIDENCE_MEDIUM_THRESHOLD: float = Field(default=0.60, env="CONFIDENCE_MEDIUM_THRESHOLD")
    CONFIDENCE_LOW_THRESHOLD: float = Field(default=0.60, env="CONFIDENCE_LOW_THRESHOLD")
    
    # Validation settings
    VALIDATION_CASCADE_DECAY: float = Field(default=0.9, env="VALIDATION_CASCADE_DECAY")
    VALIDATION_PATTERN_THRESHOLD: int = Field(default=5, env="VALIDATION_PATTERN_THRESHOLD")
    VALIDATION_SPATIAL_DISTANCE: float = Field(default=5.0, env="VALIDATION_SPATIAL_DISTANCE")
    
    # Pattern learning settings
    PATTERN_MIN_OCCURRENCES: int = Field(default=3, env="PATTERN_MIN_OCCURRENCES")
    PATTERN_CONFIDENCE_BOOST: float = Field(default=0.1, env="PATTERN_CONFIDENCE_BOOST")
    
    # Monitoring settings
    ENABLE_METRICS: bool = Field(default=True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(default=9090, env="METRICS_PORT")
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    
    # External services
    GO_BACKEND_URL: str = Field(
        default="http://localhost:8080",
        env="GO_BACKEND_URL"
    )
    
    # File storage
    TEMP_UPLOAD_DIR: str = Field(default="/tmp/arxos_uploads", env="TEMP_UPLOAD_DIR")
    
    # Model configuration for pydantic
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    def get_database_url(self) -> str:
        """Get database URL with async driver"""
        if self.DATABASE_URL.startswith("postgresql://"):
            # Convert to async driver
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        return self.DATABASE_URL
    
    def get_redis_url(self) -> Optional[str]:
        """Get Redis URL or None if not configured"""
        return self.REDIS_URL
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.DEBUG
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS allowed origins"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return self.ALLOWED_ORIGINS


# Create singleton instance
settings = Settings()


# Confidence level helpers
def get_confidence_level(score: float) -> str:
    """Get confidence level string from score"""
    if score >= settings.CONFIDENCE_HIGH_THRESHOLD:
        return "high"
    elif score >= settings.CONFIDENCE_MEDIUM_THRESHOLD:
        return "medium"
    else:
        return "low"


def get_confidence_color(score: float) -> str:
    """Get color for confidence visualization"""
    if score >= settings.CONFIDENCE_HIGH_THRESHOLD:
        return "#10b981"  # Green
    elif score >= settings.CONFIDENCE_MEDIUM_THRESHOLD:
        return "#f59e0b"  # Yellow
    else:
        return "#ef4444"  # Red