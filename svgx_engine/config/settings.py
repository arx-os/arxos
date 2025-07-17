"""
SVGX Engine - Configuration Management

Provides configuration management for SVGX Engine with:
- Environment-based configuration
- Type validation and defaults
- Configuration validation
- Development/production profiles
- Secure secret management
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    url: str = field(default_factory=lambda: os.getenv("SVGX_DATABASE_URL", "sqlite:///svgx_engine.db"))
    pool_size: int = field(default_factory=lambda: int(os.getenv("SVGX_DB_POOL_SIZE", "10")))
    max_overflow: int = field(default_factory=lambda: int(os.getenv("SVGX_DB_MAX_OVERFLOW", "20")))
    pool_timeout: int = field(default_factory=lambda: int(os.getenv("SVGX_DB_POOL_TIMEOUT", "30")))
    pool_recycle: int = field(default_factory=lambda: int(os.getenv("SVGX_DB_POOL_RECYCLE", "3600")))
    echo: bool = field(default_factory=lambda: os.getenv("SVGX_DB_ECHO", "false").lower() == "true")


@dataclass
class RedisConfig:
    """Redis configuration settings."""
    host: str = field(default_factory=lambda: os.getenv("SVGX_REDIS_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("SVGX_REDIS_PORT", "6379")))
    db: int = field(default_factory=lambda: int(os.getenv("SVGX_REDIS_DB", "0")))
    password: Optional[str] = field(default_factory=lambda: os.getenv("SVGX_REDIS_PASSWORD"))
    max_connections: int = field(default_factory=lambda: int(os.getenv("SVGX_REDIS_MAX_CONNECTIONS", "10")))
    socket_timeout: int = field(default_factory=lambda: int(os.getenv("SVGX_REDIS_SOCKET_TIMEOUT", "5")))
    socket_connect_timeout: int = field(default_factory=lambda: int(os.getenv("SVGX_REDIS_SOCKET_CONNECT_TIMEOUT", "5")))
    retry_on_timeout: bool = field(default_factory=lambda: os.getenv("SVGX_REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true")
    health_check_interval: int = field(default_factory=lambda: int(os.getenv("SVGX_REDIS_HEALTH_CHECK_INTERVAL", "300")))
    default_ttl: int = field(default_factory=lambda: int(os.getenv("SVGX_REDIS_DEFAULT_TTL", "3600")))
    enable_fallback: bool = field(default_factory=lambda: os.getenv("SVGX_REDIS_ENABLE_FALLBACK", "true").lower() == "true")


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str = field(default_factory=lambda: os.getenv("SVGX_LOG_LEVEL", "INFO"))
    format: str = field(default_factory=lambda: os.getenv("SVGX_LOG_FORMAT", "json"))
    file_path: Optional[str] = field(default_factory=lambda: os.getenv("SVGX_LOG_FILE"))
    max_bytes: int = field(default_factory=lambda: int(os.getenv("SVGX_LOG_MAX_BYTES", "10485760")))
    backup_count: int = field(default_factory=lambda: int(os.getenv("SVGX_LOG_BACKUP_COUNT", "5")))
    console_output: bool = field(default_factory=lambda: os.getenv("SVGX_LOG_CONSOLE", "true").lower() == "true")
    include_timestamp: bool = field(default_factory=lambda: os.getenv("SVGX_LOG_INCLUDE_TIMESTAMP", "true").lower() == "true")
    include_level: bool = field(default_factory=lambda: os.getenv("SVGX_LOG_INCLUDE_LEVEL", "true").lower() == "true")


@dataclass
class SecurityConfig:
    """Security configuration settings."""
    secret_key: str = field(default_factory=lambda: os.getenv("SVGX_SECRET_KEY", "your-secret-key-change-in-production"))
    algorithm: str = field(default_factory=lambda: os.getenv("SVGX_ALGORITHM", "HS256"))
    access_token_expire_minutes: int = field(default_factory=lambda: int(os.getenv("SVGX_ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
    refresh_token_expire_days: int = field(default_factory=lambda: int(os.getenv("SVGX_REFRESH_TOKEN_EXPIRE_DAYS", "7")))
    bcrypt_rounds: int = field(default_factory=lambda: int(os.getenv("SVGX_BCRYPT_ROUNDS", "12")))
    cors_origins: List[str] = field(default_factory=lambda: os.getenv("SVGX_CORS_ORIGINS", "*").split(","))
    rate_limit_requests: int = field(default_factory=lambda: int(os.getenv("SVGX_RATE_LIMIT_REQUESTS", "100")))
    rate_limit_window: int = field(default_factory=lambda: int(os.getenv("SVGX_RATE_LIMIT_WINDOW", "3600")))


@dataclass
class PerformanceConfig:
    """Performance configuration settings."""
    max_workers: int = field(default_factory=lambda: int(os.getenv("SVGX_MAX_WORKERS", "4")))
    worker_timeout: int = field(default_factory=lambda: int(os.getenv("SVGX_WORKER_TIMEOUT", "30")))
    cache_ttl: int = field(default_factory=lambda: int(os.getenv("SVGX_CACHE_TTL", "3600")))
    max_cache_size: int = field(default_factory=lambda: int(os.getenv("SVGX_MAX_CACHE_SIZE", "1000")))
    enable_compression: bool = field(default_factory=lambda: os.getenv("SVGX_ENABLE_COMPRESSION", "true").lower() == "true")
    enable_gzip: bool = field(default_factory=lambda: os.getenv("SVGX_ENABLE_GZIP", "true").lower() == "true")


@dataclass
class APIConfig:
    """API configuration settings."""
    title: str = field(default_factory=lambda: os.getenv("SVGX_API_TITLE", "SVGX Engine API"))
    description: str = field(default_factory=lambda: os.getenv("SVGX_API_DESCRIPTION", "Programmable spatial markup format and simulation engine"))
    version: str = field(default_factory=lambda: os.getenv("SVGX_API_VERSION", "1.0.0"))
    docs_url: str = field(default_factory=lambda: os.getenv("SVGX_API_DOCS_URL", "/docs"))
    redoc_url: str = field(default_factory=lambda: os.getenv("SVGX_API_REDOC_URL", "/redoc"))
    debug: bool = field(default_factory=lambda: os.getenv("SVGX_API_DEBUG", "false").lower() == "true")


@dataclass
class ServerConfig:
    """Server configuration settings."""
    host: str = field(default_factory=lambda: os.getenv("SVGX_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("SVGX_PORT", "8000")))
    reload: bool = field(default_factory=lambda: os.getenv("SVGX_RELOAD", "false").lower() == "true")
    workers: int = field(default_factory=lambda: int(os.getenv("SVGX_WORKERS", "1")))
    log_level: str = field(default_factory=lambda: os.getenv("SVGX_LOG_LEVEL", "info"))
    access_log: bool = field(default_factory=lambda: os.getenv("SVGX_ACCESS_LOG", "true").lower() == "true")


@dataclass
class MonitoringConfig:
    """Monitoring configuration settings."""
    enable_metrics: bool = field(default_factory=lambda: os.getenv("SVGX_ENABLE_METRICS", "true").lower() == "true")
    metrics_port: int = field(default_factory=lambda: int(os.getenv("SVGX_METRICS_PORT", "9090")))
    enable_health_checks: bool = field(default_factory=lambda: os.getenv("SVGX_ENABLE_HEALTH_CHECKS", "true").lower() == "true")
    health_check_interval: int = field(default_factory=lambda: int(os.getenv("SVGX_HEALTH_CHECK_INTERVAL", "30")))
    enable_tracing: bool = field(default_factory=lambda: os.getenv("SVGX_ENABLE_TRACING", "false").lower() == "true")
    tracing_endpoint: Optional[str] = field(default_factory=lambda: os.getenv("SVGX_TRACING_ENDPOINT"))


@dataclass
class SVGXConfig:
    """Main SVGX Engine configuration."""
    environment: str = field(default_factory=lambda: os.getenv("SVGX_ENVIRONMENT", "development"))
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    api: APIConfig = field(default_factory=APIConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration settings."""
        # Validate environment
        if self.environment not in ["development", "staging", "production"]:
            raise ValueError(f"Invalid environment: {self.environment}")
        
        # Validate database URL
        if not self.database.url:
            raise ValueError("Database URL is required")
        
        # Validate security settings in production
        if self.environment == "production":
            if self.security.secret_key == "your-secret-key-change-in-production":
                raise ValueError("Secret key must be changed in production")
        
        # Validate port ranges
        if not (1 <= self.server.port <= 65535):
            raise ValueError(f"Invalid port: {self.server.port}")
        
        if not (1 <= self.monitoring.metrics_port <= 65535):
            raise ValueError(f"Invalid metrics port: {self.monitoring.metrics_port}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "environment": self.environment,
            "database": {
                "url": self.database.url,
                "pool_size": self.database.pool_size,
                "max_overflow": self.database.max_overflow,
                "pool_timeout": self.database.pool_timeout,
                "pool_recycle": self.database.pool_recycle,
                "echo": self.database.echo
            },
            "redis": {
                "host": self.redis.host,
                "port": self.redis.port,
                "db": self.redis.db,
                "max_connections": self.redis.max_connections,
                "socket_timeout": self.redis.socket_timeout,
                "socket_connect_timeout": self.redis.socket_connect_timeout,
                "retry_on_timeout": self.redis.retry_on_timeout,
                "health_check_interval": self.redis.health_check_interval,
                "default_ttl": self.redis.default_ttl,
                "enable_fallback": self.redis.enable_fallback
            },
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format,
                "file_path": self.logging.file_path,
                "max_bytes": self.logging.max_bytes,
                "backup_count": self.logging.backup_count,
                "console_output": self.logging.console_output,
                "include_timestamp": self.logging.include_timestamp,
                "include_level": self.logging.include_level
            },
            "security": {
                "algorithm": self.security.algorithm,
                "access_token_expire_minutes": self.security.access_token_expire_minutes,
                "refresh_token_expire_days": self.security.refresh_token_expire_days,
                "bcrypt_rounds": self.security.bcrypt_rounds,
                "cors_origins": self.security.cors_origins,
                "rate_limit_requests": self.security.rate_limit_requests,
                "rate_limit_window": self.security.rate_limit_window
            },
            "performance": {
                "max_workers": self.performance.max_workers,
                "worker_timeout": self.performance.worker_timeout,
                "cache_ttl": self.performance.cache_ttl,
                "max_cache_size": self.performance.max_cache_size,
                "enable_compression": self.performance.enable_compression,
                "enable_gzip": self.performance.enable_gzip
            },
            "api": {
                "title": self.api.title,
                "description": self.api.description,
                "version": self.api.version,
                "docs_url": self.api.docs_url,
                "redoc_url": self.api.redoc_url,
                "debug": self.api.debug
            },
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "reload": self.server.reload,
                "workers": self.server.workers,
                "log_level": self.server.log_level,
                "access_log": self.server.access_log
            },
            "monitoring": {
                "enable_metrics": self.monitoring.enable_metrics,
                "metrics_port": self.monitoring.metrics_port,
                "enable_health_checks": self.monitoring.enable_health_checks,
                "health_check_interval": self.monitoring.health_check_interval,
                "enable_tracing": self.monitoring.enable_tracing,
                "tracing_endpoint": self.monitoring.tracing_endpoint
            }
        }
    
    def save_to_file(self, file_path: str):
        """Save configuration to file."""
        config_dict = self.to_dict()
        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'SVGXConfig':
        """Load configuration from file."""
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        
        # Create configuration from dictionary
        config = cls()
        
        # Update database config
        if "database" in config_dict:
            for key, value in config_dict["database"].items():
                setattr(config.database, key, value)
        
        # Update redis config
        if "redis" in config_dict:
            for key, value in config_dict["redis"].items():
                setattr(config.redis, key, value)
        
        # Update logging config
        if "logging" in config_dict:
            for key, value in config_dict["logging"].items():
                setattr(config.logging, key, value)
        
        # Update security config
        if "security" in config_dict:
            for key, value in config_dict["security"].items():
                setattr(config.security, key, value)
        
        # Update performance config
        if "performance" in config_dict:
            for key, value in config_dict["performance"].items():
                setattr(config.performance, key, value)
        
        # Update api config
        if "api" in config_dict:
            for key, value in config_dict["api"].items():
                setattr(config.api, key, value)
        
        # Update server config
        if "server" in config_dict:
            for key, value in config_dict["server"].items():
                setattr(config.server, key, value)
        
        # Update monitoring config
        if "monitoring" in config_dict:
            for key, value in config_dict["monitoring"].items():
                setattr(config.monitoring, key, value)
        
        return config


# Global configuration instance
_config: Optional[SVGXConfig] = None


def get_config() -> SVGXConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = SVGXConfig()
    return _config


def load_config(file_path: Optional[str] = None) -> SVGXConfig:
    """Load configuration from file or environment."""
    global _config
    if file_path and Path(file_path).exists():
        _config = SVGXConfig.load_from_file(file_path)
    else:
        _config = SVGXConfig()
    return _config


def reload_config():
    """Reload configuration from environment."""
    global _config
    _config = SVGXConfig()
    return _config 