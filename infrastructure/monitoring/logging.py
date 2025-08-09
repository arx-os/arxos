"""
Structured Logger

This module provides structured logging functionality for the infrastructure layer.
"""

import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime
import structlog

logger = logging.getLogger(__name__)


class StructuredLogger:
    """Structured logger for consistent log formatting."""

    def __init__(self, name: str = "arxos", level: str = "INFO"):
        """Initialize structured logger."""
        self.name = name
        self.level = getattr(logging, level.upper())

        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        self.logger = structlog.get_logger(name)

    def log(self, level: str, message: str, **kwargs) -> None:
        """Log a message with structured data."""
        log_method = getattr(self.logger, level.lower())
        log_method(message, **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message."""
        self.log("debug", message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log an info message."""
        self.log("info", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message."""
        self.log("warning", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log an error message."""
        self.log("error", message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message."""
        self.log("critical", message, **kwargs)

    def log_event(self, event_type: str, event_data: Dict[str, Any],
                  level: str = "info", **kwargs) -> None:
        """Log an event with structured data."""
        log_data = {
            "event_type": event_type,
            "event_data": event_data,
            **kwargs
        }
        self.log(level, f"Event: {event_type}", **log_data)

    def log_metric(self, metric_name: str, metric_value: Any,
                   metric_type: str = "gauge", **kwargs) -> None:
        """Log a metric."""
        log_data = {
            "metric_name": metric_name,
            "metric_value": metric_value,
            "metric_type": metric_type,
            **kwargs
        }
        self.log("info", f"Metric: {metric_name}", **log_data)

    def log_request(self, method: str, path: str, status_code: int,
                   duration_ms: float, **kwargs) -> None:
        """Log an HTTP request."""
        log_data = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            **kwargs
        }
        self.log("info", f"Request: {method} {path}", **log_data)

    def log_database_query(self, query: str, duration_ms: float,
                          rows_affected: Optional[int] = None, **kwargs) -> None:
        """Log a database query."""
        log_data = {
            "query": query,
            "duration_ms": duration_ms,
            "rows_affected": rows_affected,
            **kwargs
        }
        self.log("debug", f"Database query: {duration_ms:.2f}ms", **log_data)

    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log an error with context."""
        log_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            **kwargs
        }
        self.log("error", f"Error: {type(error).__name__}", **log_data)

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on structured logger."""
        return {
            "status": "healthy",
            "name": self.name,
            "level": logging.getLevelName(self.level)
        }
