"""
Application Configuration Management

This module provides configuration management for the application,
supporting loading from environment variables, configuration files,
and providing default values for development.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from application.exceptions import ConfigurationError
from application.logging_config import get_logger


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "arxos"
    username: str = "arxos_user"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False


@dataclass
class CacheConfig:
    """Cache configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 10
    ttl_default: int = 3600


@dataclass
class MessageQueueConfig:
    """Message queue configuration."""
    host: str = "localhost"
    port: int = 5672
    username: Optional[str] = None
    password: Optional[str] = None
    virtual_host: str = "/"


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    file: Optional[str] = None
    format: str = "development"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class ApplicationConfig:
    """Main application configuration."""
    environment: str = "development"
    debug: bool = False
    database: DatabaseConfig = None
    cache: CacheConfig = None
    message_queue: MessageQueueConfig = None
    logging: LoggingConfig = None
    
    def __post_init__(self):
        """Initialize default configurations if not provided."""
        if self.database is None:
            self.database = DatabaseConfig()
        if self.cache is None:
            self.cache = CacheConfig()
        if self.message_queue is None:
            self.message_queue = MessageQueueConfig()
        if self.logging is None:
            self.logging = LoggingConfig()


class ConfigManager:
    """Manages application configuration loading and validation."""
    
    def __init__(self):
        """Initialize configuration manager."""
        self.logger = get_logger("config")
        self.config: Optional[ApplicationConfig] = None
    
    def load_from_environment(self) -> ApplicationConfig:
        """Load configuration from environment variables."""
        try:
            # Database configuration
            db_config = DatabaseConfig(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                database=os.getenv("DB_NAME", "arxos"),
                username=os.getenv("DB_USER", "arxos_user"),
                password=os.getenv("DB_PASSWORD", ""),
                pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
                echo=os.getenv("DB_ECHO", "false").lower() == "true"
            )
            
            # Cache configuration
            cache_config = CacheConfig(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=int(os.getenv("REDIS_DB", "0")),
                password=os.getenv("REDIS_PASSWORD"),
                max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "10")),
                ttl_default=int(os.getenv("REDIS_TTL_DEFAULT", "3600"))
            )
            
            # Message queue configuration
            mq_config = MessageQueueConfig(
                host=os.getenv("MQ_HOST", "localhost"),
                port=int(os.getenv("MQ_PORT", "5672")),
                username=os.getenv("MQ_USERNAME"),
                password=os.getenv("MQ_PASSWORD"),
                virtual_host=os.getenv("MQ_VIRTUAL_HOST", "/")
            )
            
            # Logging configuration
            logging_config = LoggingConfig(
                level=os.getenv("LOG_LEVEL", "INFO"),
                file=os.getenv("LOG_FILE"),
                format=os.getenv("LOG_FORMAT", "development"),
                max_bytes=int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024))),
                backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5"))
            )
            
            # Main application configuration
            config = ApplicationConfig(
                environment=os.getenv("ARXOS_ENV", "development"),
                debug=os.getenv("ARXOS_DEBUG", "false").lower() == "true",
                database=db_config,
                cache=cache_config,
                message_queue=mq_config,
                logging=logging_config
            )
            
            self.logger.info("Configuration loaded from environment variables")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration from environment: {e}")
            raise ConfigurationError("env_loading", f"Failed to load environment configuration: {e}")
    
    def load_from_file(self, config_file: str) -> ApplicationConfig:
        """Load configuration from JSON file."""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                raise ConfigurationError("file_not_found", f"Configuration file not found: {config_file}")
            
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            
            # Parse configuration data
            db_config = DatabaseConfig(**config_data.get("database", {}))
            cache_config = CacheConfig(**config_data.get("cache", {}))
            mq_config = MessageQueueConfig(**config_data.get("message_queue", {}))
            logging_config = LoggingConfig(**config_data.get("logging", {}))
            
            config = ApplicationConfig(
                environment=config_data.get("environment", "development"),
                debug=config_data.get("debug", False),
                database=db_config,
                cache=cache_config,
                message_queue=mq_config,
                logging=logging_config
            )
            
            self.logger.info(f"Configuration loaded from file: {config_file}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration from file {config_file}: {e}")
            raise ConfigurationError("file_loading", f"Failed to load file configuration: {e}")
    
    def load_config(self, config_file: Optional[str] = None) -> ApplicationConfig:
        """Load configuration from file or environment."""
        try:
            if config_file and Path(config_file).exists():
                self.config = self.load_from_file(config_file)
            else:
                self.config = self.load_from_environment()
            
            self.validate_config(self.config)
            return self.config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def validate_config(self, config: ApplicationConfig) -> None:
        """Validate configuration values."""
        try:
            # Validate database configuration
            if not config.database.host:
                raise ConfigurationError("db_host", "Database host is required")
            if config.database.port <= 0 or config.database.port > 65535:
                raise ConfigurationError("db_port", "Database port must be between 1 and 65535")
            if not config.database.database:
                raise ConfigurationError("db_name", "Database name is required")
            
            # Validate cache configuration
            if not config.cache.host:
                raise ConfigurationError("redis_host", "Redis host is required")
            if config.cache.port <= 0 or config.cache.port > 65535:
                raise ConfigurationError("redis_port", "Redis port must be between 1 and 65535")
            
            # Validate message queue configuration
            if not config.message_queue.host:
                raise ConfigurationError("mq_host", "Message queue host is required")
            if config.message_queue.port <= 0 or config.message_queue.port > 65535:
                raise ConfigurationError("mq_port", "Message queue port must be between 1 and 65535")
            
            # Validate logging configuration
            valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if config.logging.level.upper() not in valid_log_levels:
                raise ConfigurationError("log_level", f"Invalid log level. Must be one of: {valid_log_levels}")
            
            self.logger.info("Configuration validation passed")
            
        except ConfigurationError:
            raise
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            raise ConfigurationError("validation", f"Configuration validation failed: {e}")
    
    def get_config(self) -> ApplicationConfig:
        """Get the current configuration."""
        if self.config is None:
            self.config = self.load_config()
        return self.config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        config = self.get_config()
        return {
            "environment": config.environment,
            "debug": config.debug,
            "database": {
                "host": config.database.host,
                "port": config.database.port,
                "database": config.database.database,
                "username": config.database.username,
                "password": "***" if config.database.password else None,
                "pool_size": config.database.pool_size,
                "max_overflow": config.database.max_overflow,
                "echo": config.database.echo
            },
            "cache": {
                "host": config.cache.host,
                "port": config.cache.port,
                "db": config.cache.db,
                "password": "***" if config.cache.password else None,
                "max_connections": config.cache.max_connections,
                "ttl_default": config.cache.ttl_default
            },
            "message_queue": {
                "host": config.message_queue.host,
                "port": config.message_queue.port,
                "username": config.message_queue.username,
                "password": "***" if config.message_queue.password else None,
                "virtual_host": config.message_queue.virtual_host
            },
            "logging": {
                "level": config.logging.level,
                "file": config.logging.file,
                "format": config.logging.format,
                "max_bytes": config.logging.max_bytes,
                "backup_count": config.logging.backup_count
            }
        }


# Global configuration manager instance
config_manager = ConfigManager()


def load_config(config_file: Optional[str] = None) -> ApplicationConfig:
    """Load application configuration."""
    return config_manager.load_config(config_file)


def get_config() -> ApplicationConfig:
    """Get current application configuration."""
    return config_manager.get_config()


def get_config_dict() -> Dict[str, Any]:
    """Get configuration as dictionary."""
    return config_manager.to_dict() 