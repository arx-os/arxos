"""
Comprehensive logging configuration for Arxos SVG-BIM Integration System.

This module provides centralized logging configuration with:
- Structured logging with JSON format
- Different log levels for development and production
- File and console handlers
- Performance monitoring
- Error tracking
- Security audit logging
"""

import logging
import logging.config
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to log records."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        if not log_record.get('timestamp'):
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        
        # Add log level
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname
        
        # Add module and function info
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add process and thread info
        log_record['process'] = record.process
        log_record['thread'] = record.thread
        
        # Add application context
        log_record['application'] = 'arx_svg_parser'
        log_record['version'] = '1.0.0'


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_json: bool = True,
    enable_console: bool = True,
    enable_file: bool = True,
    log_format: str = "json"
) -> None:
    """
    Set up comprehensive logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        enable_json: Enable JSON formatted logs
        enable_console: Enable console output
        enable_file: Enable file output
        log_format: Log format ('json' or 'text')
    """
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Determine handlers based on configuration
    handlers = []
    
    if enable_console:
        console_handler = {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': 'json' if enable_json and log_format == 'json' else 'text',
            'stream': 'ext://sys.stdout'
        }
        handlers.append(('console', console_handler))
    
    if enable_file and log_file:
        file_handler = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'json' if enable_json and log_format == 'json' else 'text',
            'filename': log_file,
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
        handlers.append(('file', file_handler))
    
    # Define formatters
    formatters = {}
    
    if enable_json and log_format == 'json':
        formatters['json'] = {
            '()': CustomJsonFormatter,
            'format': '%(timestamp)s %(level)s %(name)s %(module)s %(function)s %(line)s %(message)s'
        }
    
    formatters['text'] = {
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S'
    }
    
    # Configure logging
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': formatters,
        'handlers': dict(handlers),
        'loggers': {
            '': {  # Root logger
                'handlers': list(dict(handlers).keys()),
                'level': log_level,
                'propagate': False
            },
            'arx_svg_parser': {
                'handlers': list(dict(handlers).keys()),
                'level': log_level,
                'propagate': False
            },
            'arx_svg_parser.api': {
                'handlers': list(dict(handlers).keys()),
                'level': log_level,
                'propagate': False
            },
            'arx_svg_parser.services': {
                'handlers': list(dict(handlers).keys()),
                'level': log_level,
                'propagate': False
            },
            'arx_svg_parser.models': {
                'handlers': list(dict(handlers).keys()),
                'level': log_level,
                'propagate': False
            },
            'arx_svg_parser.utils': {
                'handlers': list(dict(handlers).keys()),
                'level': log_level,
                'propagate': False
            },
            'uvicorn': {
                'handlers': list(dict(handlers).keys()),
                'level': 'INFO',
                'propagate': False
            },
            'fastapi': {
                'handlers': list(dict(handlers).keys()),
                'level': 'INFO',
                'propagate': False
            }
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(logging_config)
    
    # Set up structlog for structured logging
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
            structlog.processors.JSONRenderer() if enable_json and log_format == 'json' else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_performance(func):
    """Decorator to log function performance."""
    def wrapper(*args, **kwargs):
        logger = get_logger(f"{func.__module__}.{func.__name__}")
        start_time = datetime.utcnow()
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(
                "Function completed successfully",
                function=func.__name__,
                duration=duration,
                status="success"
            )
            return result
        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.error(
                "Function failed",
                function=func.__name__,
                duration=duration,
                error=str(e),
                status="error"
            )
            raise
    
    return wrapper


def log_security_event(event_type: str, user_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
    """
    Log security-related events.
    
    Args:
        event_type: Type of security event
        user_id: User ID (if applicable)
        details: Additional event details
    """
    logger = get_logger("arx_svg_parser.security")
    
    log_data = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "security_event": True
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    if details:
        log_data.update(details)
    
    logger.warning("Security event detected", **log_data)


def log_api_request(method: str, path: str, user_id: Optional[str] = None, status_code: Optional[int] = None):
    """
    Log API request details.
    
    Args:
        method: HTTP method
        path: Request path
        user_id: User ID (if authenticated)
        status_code: Response status code
    """
    logger = get_logger("arx_svg_parser.api")
    
    log_data = {
        "method": method,
        "path": path,
        "timestamp": datetime.utcnow().isoformat(),
        "api_request": True
    }
    
    if user_id:
        log_data["user_id"] = user_id
    
    if status_code:
        log_data["status_code"] = status_code
    
    logger.info("API request", **log_data)


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """
    Log error with context.
    
    Args:
        error: Exception to log
        context: Additional context information
    """
    logger = get_logger("arx_svg_parser.errors")
    
    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat(),
        "error": True
    }
    
    if context:
        log_data.update(context)
    
    logger.error("Application error", **log_data, exc_info=True)


# Initialize logging with default configuration
def initialize_logging():
    """Initialize logging with default configuration."""
    # Get configuration from environment variables
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "logs/arx_svg_parser.log")
    enable_json = os.getenv("LOG_JSON", "true").lower() == "true"
    enable_console = os.getenv("LOG_CONSOLE", "true").lower() == "true"
    enable_file = os.getenv("LOG_FILE_ENABLED", "true").lower() == "true"
    log_format = os.getenv("LOG_FORMAT", "json")
    
    setup_logging(
        log_level=log_level,
        log_file=log_file,
        enable_json=enable_json,
        enable_console=enable_console,
        enable_file=enable_file,
        log_format=log_format
    )


if __name__ == "__main__":
    # Test logging configuration
    initialize_logging()
    logger = get_logger(__name__)
    
    logger.info("Logging system initialized successfully")
    logger.warning("This is a test warning")
    logger.error("This is a test error")
    
    # Test performance logging
    @log_performance
    def test_function():
        import time
        time.sleep(0.1)
        return "test result"
    
    test_function()
    
    # Test security logging
    log_security_event("login_attempt", user_id="user123", details={"ip": "192.168.1.1"})
    
    # Test API request logging
    log_api_request("GET", "/api/symbols", user_id="user123", status_code=200)
    
    print("Logging configuration test completed successfully!") 