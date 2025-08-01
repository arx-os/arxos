"""
Configuration utilities for the Arxos Platform shared library.

This module provides centralized configuration management for the core.shared package,
including settings loading, validation, and environment-specific configurations.
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SharedConfig:
    """Configuration settings for the core.shared package."""
    
    # Package settings
    package_name: str = "core.shared"
    version: str = "1.0.0"
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"
    enable_structured_logging: bool = True
    
    # Date/time settings
    default_timezone: str = "UTC"
    timestamp_format: str = "ISO"
    
    # Object utilities settings
    max_object_depth: int = 10
    max_object_size: int = 1024 * 1024  # 1MB
    enable_object_validation: bool = True
    
    # Request utilities settings
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    enable_request_logging: bool = True
    enable_rate_limiting: bool = True
    rate_limit_window: int = 60  # seconds
    rate_limit_max_requests: int = 100
    
    # Error handling settings
    enable_detailed_errors: bool = False
    error_log_level: str = "ERROR"
    
    # Cache settings
    enable_caching: bool = True
    cache_ttl: int = 300  # 5 minutes
    max_cache_size: int = 1000
    
    # Development settings
    debug_mode: bool = False
    enable_metrics: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_settings()
    
    def _validate_settings(self):
        """Validate configuration settings."""
        if self.max_object_depth < 1:
            raise ValueError("max_object_depth must be at least 1")
        
        if self.max_object_size < 1024:
            raise ValueError("max_object_size must be at least 1KB")
        
        if self.max_request_size < 1024:
            raise ValueError("max_request_size must be at least 1KB")
        
        if self.rate_limit_window < 1:
            raise ValueError("rate_limit_window must be at least 1 second")
        
        if self.rate_limit_max_requests < 1:
            raise ValueError("rate_limit_max_requests must be at least 1")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "package_name": self.package_name,
            "version": self.version,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "enable_structured_logging": self.enable_structured_logging,
            "default_timezone": self.default_timezone,
            "timestamp_format": self.timestamp_format,
            "max_object_depth": self.max_object_depth,
            "max_object_size": self.max_object_size,
            "enable_object_validation": self.enable_object_validation,
            "max_request_size": self.max_request_size,
            "enable_request_logging": self.enable_request_logging,
            "enable_rate_limiting": self.enable_rate_limiting,
            "rate_limit_window": self.rate_limit_window,
            "rate_limit_max_requests": self.rate_limit_max_requests,
            "enable_detailed_errors": self.enable_detailed_errors,
            "error_log_level": self.error_log_level,
            "enable_caching": self.enable_caching,
            "cache_ttl": self.cache_ttl,
            "max_cache_size": self.max_cache_size,
            "debug_mode": self.debug_mode,
            "enable_metrics": self.enable_metrics,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SharedConfig":
        """Create configuration from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> "SharedConfig":
        """Create configuration from environment variables."""
        return cls(
            log_level=os.getenv("ARXOS_LOG_LEVEL", "INFO"),
            log_format=os.getenv("ARXOS_LOG_FORMAT", "json"),
            enable_structured_logging=os.getenv("ARXOS_ENABLE_STRUCTURED_LOGGING", "true").lower() == "true",
            default_timezone=os.getenv("ARXOS_DEFAULT_TIMEZONE", "UTC"),
            timestamp_format=os.getenv("ARXOS_TIMESTAMP_FORMAT", "ISO"),
            max_object_depth=int(os.getenv("ARXOS_MAX_OBJECT_DEPTH", "10")),
            max_object_size=int(os.getenv("ARXOS_MAX_OBJECT_SIZE", str(1024 * 1024))),
            enable_object_validation=os.getenv("ARXOS_ENABLE_OBJECT_VALIDATION", "true").lower() == "true",
            max_request_size=int(os.getenv("ARXOS_MAX_REQUEST_SIZE", str(10 * 1024 * 1024))),
            enable_request_logging=os.getenv("ARXOS_ENABLE_REQUEST_LOGGING", "true").lower() == "true",
            enable_rate_limiting=os.getenv("ARXOS_ENABLE_RATE_LIMITING", "true").lower() == "true",
            rate_limit_window=int(os.getenv("ARXOS_RATE_LIMIT_WINDOW", "60")),
            rate_limit_max_requests=int(os.getenv("ARXOS_RATE_LIMIT_MAX_REQUESTS", "100")),
            enable_detailed_errors=os.getenv("ARXOS_ENABLE_DETAILED_ERRORS", "false").lower() == "true",
            error_log_level=os.getenv("ARXOS_ERROR_LOG_LEVEL", "ERROR"),
            enable_caching=os.getenv("ARXOS_ENABLE_CACHING", "true").lower() == "true",
            cache_ttl=int(os.getenv("ARXOS_CACHE_TTL", "300")),
            max_cache_size=int(os.getenv("ARXOS_MAX_CACHE_SIZE", "1000")),
            debug_mode=os.getenv("ARXOS_DEBUG_MODE", "false").lower() == "true",
            enable_metrics=os.getenv("ARXOS_ENABLE_METRICS", "true").lower() == "true",
        )


# Global configuration instance
_config: Optional[SharedConfig] = None


def get_settings() -> SharedConfig:
    """Get the global configuration settings."""
    global _config
    
    if _config is None:
        _config = SharedConfig.from_env()
    
    return _config


def update_settings(config: SharedConfig) -> None:
    """Update the global configuration settings."""
    global _config
    _config = config


def reset_settings() -> None:
    """Reset the global configuration to default."""
    global _config
    _config = None


def load_config_from_file(file_path: str) -> SharedConfig:
    """Load configuration from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return SharedConfig.from_dict(data)
    except Exception as e:
        raise ValueError(f"Failed to load configuration from {file_path}: {e}")


def save_config_to_file(config: SharedConfig, file_path: str) -> None:
    """Save configuration to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)
    except Exception as e:
        raise ValueError(f"Failed to save configuration to {file_path}: {e}")


def get_config_summary() -> Dict[str, Any]:
    """Get a summary of the current configuration."""
    config = get_settings()
    return {
        "package": config.package_name,
        "version": config.version,
        "environment": {
            "log_level": config.log_level,
            "debug_mode": config.debug_mode,
            "enable_metrics": config.enable_metrics,
        },
        "features": {
            "structured_logging": config.enable_structured_logging,
            "object_validation": config.enable_object_validation,
            "request_logging": config.enable_request_logging,
            "rate_limiting": config.enable_rate_limiting,
            "caching": config.enable_caching,
            "detailed_errors": config.enable_detailed_errors,
        },
        "limits": {
            "max_object_depth": config.max_object_depth,
            "max_object_size": config.max_object_size,
            "max_request_size": config.max_request_size,
            "rate_limit_window": config.rate_limit_window,
            "rate_limit_max_requests": config.rate_limit_max_requests,
            "cache_ttl": config.cache_ttl,
            "max_cache_size": config.max_cache_size,
        },
    } 