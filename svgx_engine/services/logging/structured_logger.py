"""
SVGX Engine - Structured Logger

Provides structured logging functionality for SVGX Engine with
proper formatting, levels, and context management.
"""

import logging
import structlog
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SVGXLogger:
    """Structured logger for SVGX Engine."""
    
    def __init__(self, name: str = "svgx_engine"):
        """Initialize SVGX logger."""
        self.name = name
        self.logger = structlog.get_logger(name)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, **kwargs)


def get_logger(name: str = "svgx_engine") -> SVGXLogger:
    """Get a logger instance."""
    return SVGXLogger(name)


def setup_logging(level: str = "INFO", format: str = "json"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def logging_context(**kwargs):
    """Context manager for logging with additional context."""
    return structlog.contextvars.bind_contextvars(**kwargs) 