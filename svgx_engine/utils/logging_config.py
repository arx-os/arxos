"""
SVGX Engine - Logging Configuration

Comprehensive logging system with structured logging,
performance monitoring, and security logging.
"""

import logging
import logging.config
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    import structlog

    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


class LogLevel:
    """Log levels for SVGX Engine."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory:
    """Log categories for SVGX Engine."""

    GENERAL = "general"
    PARSER = "parser"
    RUNTIME = "runtime"
    COMPILER = "compiler"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DATABASE = "database"
    API = "api"
    TELEMETRY = "telemetry"


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for logs."""

    def format(self, record):
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
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

        return json.dumps(log_entry)


class PerformanceFormatter(logging.Formatter):
    """Performance-specific formatter."""

    def format(self, record):
        """Format performance log record."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "category": "performance",
            "operation": getattr(record, "operation", "unknown"),
            "duration_ms": getattr(record, "duration_ms", 0),
            "memory_mb": getattr(record, "memory_mb", 0),
            "cpu_percent": getattr(record, "cpu_percent", 0),
            "message": record.getMessage(),
        }

        return json.dumps(log_entry)


class SecurityFormatter(logging.Formatter):
    """Security-specific formatter."""

    def format(self, record):
        """Format security log record."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "category": "security",
            "event_type": getattr(record, "event_type", "unknown"),
            "user_id": getattr(record, "user_id", None),
            "ip_address": getattr(record, "ip_address", None),
            "action": getattr(record, "action", "unknown"),
            "resource": getattr(record, "resource", None),
            "message": record.getMessage(),
        }

        return json.dumps(log_entry)


class SVGXLogger:
    """Enhanced logger for SVGX Engine."""

    def __init__(self, name: str, category: str = LogCategory.GENERAL):
        self.name = name
        self.category = category
        self.logger = logging.getLogger(name)
        self._setup_logger()

    def _setup_logger(self):
        """Setup the logger with appropriate handlers."""
        # Don't add handlers if they already exist
        if self.logger.handlers:
            return

        # Create handlers based on category
        if self.category == LogCategory.PERFORMANCE:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(PerformanceFormatter())
        elif self.category == LogCategory.SECURITY:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(SecurityFormatter())
        else:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(StructuredFormatter())

        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def debug(self, message: str, **kwargs):
        """Log debug message with extra fields."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message with extra fields."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with extra fields."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message with extra fields."""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message with extra fields."""
        self._log(logging.CRITICAL, message, **kwargs)

    def _log(self, level: int, message: str, **kwargs):
        """Log message with extra fields."""
        record = self.logger.makeRecord(
            self.name, level, __file__, 0, message, (), None
        )

        # Add extra fields to record
        if kwargs:
            record.extra_fields = kwargs

        self.logger.handle(record)

    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        memory_mb: Optional[float] = None,
        cpu_percent: Optional[float] = None,
        **kwargs,
    ):
        """Log performance metric."""
        self.info(
            f"Performance: {operation} completed in {duration_ms:.2f}ms",
            operation=operation,
            duration_ms=duration_ms,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            **kwargs,
        )

    def log_security(
        self,
        event_type: str,
        action: str,
        resource: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        **kwargs,
    ):
        """Log security event."""
        self.warning(
            f"Security event: {event_type} - {action}",
            event_type=event_type,
            action=action,
            resource=resource,
            user_id=user_id,
            ip_address=ip_address,
            **kwargs,
        )


class LoggingManager:
    """Centralized logging manager for SVGX Engine."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        self.loggers: Dict[str, SVGXLogger] = {}
        self._setup_logging()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default logging configuration."""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "structured": {"()": StructuredFormatter},
                "performance": {"()": PerformanceFormatter},
                "security": {"()": SecurityFormatter},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "structured",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.FileHandler",
                    "level": "DEBUG",
                    "formatter": "structured",
                    "filename": "svgx_engine.log",
                    "mode": "a",
                },
                "performance": {
                    "class": "logging.FileHandler",
                    "level": "INFO",
                    "formatter": "performance",
                    "filename": "svgx_performance.log",
                    "mode": "a",
                },
                "security": {
                    "class": "logging.FileHandler",
                    "level": "WARNING",
                    "formatter": "security",
                    "filename": "svgx_security.log",
                    "mode": "a",
                },
            },
            "loggers": {
                "svgx_engine": {
                    "level": "INFO",
                    "handlers": ["console", "file"],
                    "propagate": False,
                },
                "svgx_engine.performance": {
                    "level": "INFO",
                    "handlers": ["performance"],
                    "propagate": False,
                },
                "svgx_engine.security": {
                    "level": "WARNING",
                    "handlers": ["security"],
                    "propagate": False,
                },
            },
        }

    def _setup_logging(self):
        """Setup logging configuration."""
        try:
            logging.config.dictConfig(self.config)
        except Exception as e:
            # Fallback to basic logging if config fails
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            print(f"Warning: Failed to setup structured logging: {e}")

    def get_logger(self, name: str, category: str = LogCategory.GENERAL) -> SVGXLogger:
        """Get a logger instance."""
        if name not in self.loggers:
            self.loggers[name] = SVGXLogger(name, category)
        return self.loggers[name]

    def get_performance_logger(self, name: str) -> SVGXLogger:
        """Get a performance logger."""
        return self.get_logger(f"{name}.performance", LogCategory.PERFORMANCE)

    def get_security_logger(self, name: str) -> SVGXLogger:
        """Get a security logger."""
        return self.get_logger(f"{name}.security", LogCategory.SECURITY)

    def get_parser_logger(self, name: str) -> SVGXLogger:
        """Get a parser logger."""
        return self.get_logger(f"{name}.parser", LogCategory.PARSER)

    def get_runtime_logger(self, name: str) -> SVGXLogger:
        """Get a runtime logger."""
        return self.get_logger(f"{name}.runtime", LogCategory.RUNTIME)

    def get_compiler_logger(self, name: str) -> SVGXLogger:
        """Get a compiler logger."""
        return self.get_logger(f"{name}.compiler", LogCategory.COMPILER)

    def get_api_logger(self, name: str) -> SVGXLogger:
        """Get an API logger."""
        return self.get_logger(f"{name}.api", LogCategory.API)

    def get_database_logger(self, name: str) -> SVGXLogger:
        """Get a database logger."""
        return self.get_logger(f"{name}.database", LogCategory.DATABASE)

    def get_telemetry_logger(self, name: str) -> SVGXLogger:
        """Get a telemetry logger."""
        return self.get_logger(f"{name}.telemetry", LogCategory.TELEMETRY)


# Global logging manager instance
_logging_manager = LoggingManager()


def get_logger(name: str, category: str = LogCategory.GENERAL) -> SVGXLogger:
    """Get a logger instance."""
    return _logging_manager.get_logger(name, category)


def get_performance_logger(name: str) -> SVGXLogger:
    """Get a performance logger."""
    return _logging_manager.get_performance_logger(name)


def get_security_logger(name: str) -> SVGXLogger:
    """Get a security logger."""
    return _logging_manager.get_security_logger(name)


def get_parser_logger(name: str) -> SVGXLogger:
    """Get a parser logger."""
    return _logging_manager.get_parser_logger(name)


def get_runtime_logger(name: str) -> SVGXLogger:
    """Get a runtime logger."""
    return _logging_manager.get_runtime_logger(name)


def get_compiler_logger(name: str) -> SVGXLogger:
    """Get a compiler logger."""
    return _logging_manager.get_compiler_logger(name)


def get_api_logger(name: str) -> SVGXLogger:
    """Get an API logger."""
    return _logging_manager.get_api_logger(name)


def get_database_logger(name: str) -> SVGXLogger:
    """Get a database logger."""
    return _logging_manager.get_database_logger(name)


def get_telemetry_logger(name: str) -> SVGXLogger:
    """Get a telemetry logger."""
    return _logging_manager.get_telemetry_logger(name)


def setup_logging(config: Optional[Dict[str, Any]] = None):
    """Setup logging with custom configuration."""
    global _logging_manager
    _logging_manager = LoggingManager(config)


def log_performance_metric(
    operation: str,
    duration_ms: float,
    memory_mb: Optional[float] = None,
    cpu_percent: Optional[float] = None,
    **kwargs,
):
    """Log a performance metric."""
    logger = get_performance_logger("svgx_engine")
    logger.log_performance(operation, duration_ms, memory_mb, cpu_percent, **kwargs)


def log_security_event(
    event_type: str,
    action: str,
    resource: Optional[str] = None,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    **kwargs,
):
    """Log a security event."""
    logger = get_security_logger("svgx_engine")
    logger.log_security(event_type, action, resource, user_id, ip_address, **kwargs)


def log_api_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
):
    """Log an API request."""
    logger = get_api_logger("svgx_engine")
    logger.info(
        f"API Request: {method} {path} - {status_code}",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms,
        user_id=user_id,
        ip_address=ip_address,
    )


def log_database_operation(
    operation: str,
    table: str,
    duration_ms: float,
    rows_affected: Optional[int] = None,
    **kwargs,
):
    """Log a database operation."""
    logger = get_database_logger("svgx_engine")
    logger.info(
        f"Database operation: {operation} on {table}",
        operation=operation,
        table=table,
        duration_ms=duration_ms,
        rows_affected=rows_affected,
        **kwargs,
    )


def log_telemetry_event(event_type: str, message: str, **kwargs):
    """Log a telemetry event."""
    logger = get_telemetry_logger("svgx_engine")
    logger.info(
        f"Telemetry: {event_type} - {message}",
        event_type=event_type,
        message=message,
        **kwargs,
    )
