import sys
import logging
import structlog
import os
from typing import Optional

def configure_logging(
    log_level: str = "INFO",
    enable_json: bool = True,
    enable_console: bool = True,
    enable_file: bool = False,
    log_file: Optional[str] = None
):
    """Configure structured logging with best practices."""
    
    # Basic logging setup
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # Structlog configuration
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add JSON renderer for production, console renderer for development
    if enable_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def setup_logging_for_environment():
    """Configure logging based on environment."""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        configure_logging(
            log_level="INFO",
            enable_json=True,
            enable_console=True,
            enable_file=True,
            log_file="/var/log/arx_svg_parser/app.log"
        )
    elif env == "development":
        configure_logging(
            log_level="DEBUG",
            enable_json=False,  # Human-readable in dev
            enable_console=True,
            enable_file=False
        )
    else:
        configure_logging(
            log_level="WARNING",
            enable_json=True,
            enable_console=True,
            enable_file=False
        ) 