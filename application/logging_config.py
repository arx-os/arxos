"""
Application Logging Configuration

This module provides comprehensive logging configuration for the application
layer with structured logging, different log levels, and proper formatting
for development and production environments.
"""

import logging
import logging.config
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


class DevelopmentFormatter(logging.Formatter):
    """Human-readable formatter for development environment."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for human readability."""
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname.ljust(8)
        logger = record.name.ljust(20)
        message = record.getMessage()

        formatted = f"{timestamp} | {level} | {logger} | {message}"

        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


class ApplicationLogger:
    """Application logger with structured logging capabilities."""

    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

    def _log_with_context(self, level: int, message: str, **context):
        """Log message with additional context."""
        extra_fields = {"context": context, "timestamp": datetime.utcnow().isoformat()}

        # Create a new log record with extra fields
        record = self.logger.makeRecord(
            self.logger.name, level, "", 0, message, (), None
        )
        record.extra_fields = extra_fields

        self.logger.handle(record)

    def info(self, message: str, **context):
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, **context)

    def warning(self, message: str, **context):
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, **context)

    def error(self, message: str, **context):
        """Log error message with context."""
        self._log_with_context(logging.ERROR, message, **context)

    def debug(self, message: str, **context):
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, **context)

    def critical(self, message: str, **context):
        """Log critical message with context."""
        self._log_with_context(logging.CRITICAL, message, **context)

    def exception(self, message: str, **context):
        """Log exception message with context."""
        self._log_with_context(logging.ERROR, message, **context)

    def log_operation(
        self, operation: str, resource: str, resource_id: str = None, **context
    ):
        """Log operation with standardized format."""
        message = f"Operation: {operation} | Resource: {resource}"
        if resource_id:
            message += f" | ID: {resource_id}"

        self.info(
            message,
            operation=operation,
            resource=resource,
            resource_id=resource_id,
            **context,
        )

    def log_performance(self, operation: str, duration_ms: float, **context):
        """Log performance metrics."""
        self.info(
            f"Performance: {operation} took {duration_ms:.2f}ms",
            operation=operation,
            duration_ms=duration_ms,
            **context,
        )


def setup_logging(
    environment: str = "development",
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True,
) -> None:
    """Setup logging configuration for the application."""

    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure logging based on environment
    if environment == "production":
        setup_production_logging(log_level, log_file, enable_console)
    else:
        setup_development_logging(log_level, log_file, enable_console)


def setup_development_logging(
    log_level: str = "INFO", log_file: Optional[str] = None, enable_console: bool = True
) -> None:
    """Setup logging for development environment."""

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "development": {
                "()": DevelopmentFormatter,
                "format": "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
            },
            "structured": {"()": StructuredFormatter},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "development",
                "stream": sys.stdout,
            }
        },
        "loggers": {
            "arxos": {"level": log_level, "handlers": ["console"], "propagate": False},
            "application": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "domain": {"level": log_level, "handlers": ["console"], "propagate": False},
            "infrastructure": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {"level": "WARNING", "handlers": ["console"]},
    }

    # Add file handler if specified
    if log_file:
        config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "level": log_level,
            "formatter": "development",
            "filename": log_file,
            "mode": "a",
        }

        # Add file handler to all loggers
        for logger_config in config["loggers"].values():
            logger_config["handlers"].append("file")

    logging.config.dictConfig(config)


def setup_production_logging(
    log_level: str = "INFO", log_file: Optional[str] = None, enable_console: bool = True
) -> None:
    """Setup logging for production environment."""

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"structured": {"()": StructuredFormatter}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "structured",
                "stream": sys.stdout,
            }
        },
        "loggers": {
            "arxos": {"level": log_level, "handlers": ["console"], "propagate": False},
            "application": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "domain": {"level": log_level, "handlers": ["console"], "propagate": False},
            "infrastructure": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {"level": "WARNING", "handlers": ["console"]},
    }

    # Add file handler if specified
    if log_file:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "structured",
            "filename": log_file,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
        }

        # Add file handler to all loggers
        for logger_config in config["loggers"].values():
            logger_config["handlers"].append("file")

    logging.config.dictConfig(config)


def get_logger(name: str) -> ApplicationLogger:
    """Get an application logger instance."""
    return ApplicationLogger(name)


def log_function_call(func):
    """Decorator to log function calls with parameters and timing."""

    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)

        # Log function entry
        logger.debug(
            f"Function call: {func.__name__}",
            function=func.__name__,
            module=func.__module__,
            args_count=len(args),
            kwargs_count=len(kwargs),
        )

        try:
            start_time = datetime.utcnow()
            result = func(*args, **kwargs)
            end_time = datetime.utcnow()

            # Log successful completion
            duration_ms = (end_time - start_time).total_seconds() * 1000
            logger.log_performance(
                f"Function: {func.__name__}",
                duration_ms,
                function=func.__name__,
                status="success",
            )

            return result

        except Exception as e:
            # Log error
            logger.error(
                f"Function error: {func.__name__} - {str(e)}",
                function=func.__name__,
                error=str(e),
                status="error",
            )
            raise

    return wrapper


def log_database_operation(operation: str, table: str, record_id: str = None):
    """Decorator to log database operations."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger("database")

            logger.log_operation(
                operation=operation, resource=f"database.{table}", resource_id=record_id
            )

            try:
                start_time = datetime.utcnow()
                result = func(*args, **kwargs)
                end_time = datetime.utcnow()

                duration_ms = (end_time - start_time).total_seconds() * 1000
                logger.log_performance(
                    f"Database: {operation}",
                    duration_ms,
                    table=table,
                    operation=operation,
                )

                return result

            except Exception as e:
                logger.error(
                    f"Database error: {operation} on {table} - {str(e)}",
                    operation=operation,
                    table=table,
                    error=str(e),
                )
                raise

        return wrapper

    return decorator


def log_api_request(method: str, endpoint: str):
    """Decorator to log API requests."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger("api")

            logger.log_operation(operation=f"HTTP {method}", resource=f"api.{endpoint}")

            try:
                start_time = datetime.utcnow()
                result = func(*args, **kwargs)
                end_time = datetime.utcnow()

                duration_ms = (end_time - start_time).total_seconds() * 1000
                logger.log_performance(
                    f"API: {method} {endpoint}",
                    duration_ms,
                    method=method,
                    endpoint=endpoint,
                )

                return result

            except Exception as e:
                logger.error(
                    f"API error: {method} {endpoint} - {str(e)}",
                    method=method,
                    endpoint=endpoint,
                    error=str(e),
                )
                raise

        return wrapper

    return decorator


# Initialize logging with default configuration
setup_logging()
