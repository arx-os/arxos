"""
SVGX Engine - Logging Services

Provides structured logging functionality for SVGX Engine including:
- Structured logging
- Log formatting
- Log levels and contexts
"""

try:
    from svgx_engine.services.logging.structured_logger import SVGXLogger, get_logger, setup_logging, logging_context
except ImportError:
    # Fallback for direct execution
    from .structured_logger import SVGXLogger, get_logger, setup_logging, logging_context

__all__ = [
    'SVGXLogger',
    'get_logger',
    'setup_logging',
    'logging_context'
] 