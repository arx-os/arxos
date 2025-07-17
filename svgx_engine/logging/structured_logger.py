"""
SVGX Engine - Structured Logging

Provides structured logging functionality for SVGX Engine with:
- JSON formatting for machine-readable logs
- Configurable log levels and handlers
- Performance monitoring integration
- Request/response correlation
- Error tracking and reporting
"""

import os
import json
import logging
import logging.handlers
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import contextmanager
import uuid
import traceback

logger = logging.getLogger(__name__)


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for SVGX Engine logs."""
    
    def __init__(self, include_timestamp: bool = True, include_level: bool = True):
        """Initialize structured formatter."""
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if self.include_timestamp:
            log_entry["timestamp"] = datetime.utcnow().isoformat()
        
        if self.include_level:
            log_entry["level"] = record.levelname
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class SVGXLogger:
    """Structured logger for SVGX Engine."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize SVGX logger."""
        self.name = name
        self.config = config or self._load_config()
        self.logger = logging.getLogger(name)
        self.request_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.user_id: Optional[str] = None
        
        self._setup_logger()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load logging configuration from environment."""
        return {
            "level": os.getenv("SVGX_LOG_LEVEL", "INFO"),
            "format": os.getenv("SVGX_LOG_FORMAT", "json"),
            "file_path": os.getenv("SVGX_LOG_FILE"),
            "max_bytes": int(os.getenv("SVGX_LOG_MAX_BYTES", "10485760")),  # 10MB
            "backup_count": int(os.getenv("SVGX_LOG_BACKUP_COUNT", "5")),
            "console_output": os.getenv("SVGX_LOG_CONSOLE", "true").lower() == "true",
            "include_timestamp": os.getenv("SVGX_LOG_INCLUDE_TIMESTAMP", "true").lower() == "true",
            "include_level": os.getenv("SVGX_LOG_INCLUDE_LEVEL", "true").lower() == "true"
        }
    
    def _setup_logger(self):
        """Set up logger with handlers and formatters."""
        # Set log level
        level = getattr(logging, self.config["level"].upper(), logging.INFO)
        self.logger.setLevel(level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        if self.config["format"] == "json":
            formatter = StructuredFormatter(
                include_timestamp=self.config["include_timestamp"],
                include_level=self.config["include_level"]
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        # Add console handler if enabled
        if self.config["console_output"]:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Add file handler if file path is specified
        if self.config["file_path"]:
            try:
                file_handler = logging.handlers.RotatingFileHandler(
                    self.config["file_path"],
                    maxBytes=self.config["max_bytes"],
                    backupCount=self.config["backup_count"]
                )
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                print(f"Failed to set up file logging: {e}")
    
    def set_context(self, request_id: Optional[str] = None, 
                   session_id: Optional[str] = None, 
                   user_id: Optional[str] = None):
        """Set logging context for correlation."""
        self.request_id = request_id
        self.session_id = session_id
        self.user_id = user_id
    
    def _get_extra_fields(self) -> Dict[str, Any]:
        """Get extra fields for structured logging."""
        extra = {}
        if self.request_id:
            extra["request_id"] = self.request_id
        if self.session_id:
            extra["session_id"] = self.session_id
        if self.user_id:
            extra["user_id"] = self.user_id
        return extra
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        extra = {**self._get_extra_fields(), **kwargs}
        self.logger.debug(message, extra=extra)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        extra = {**self._get_extra_fields(), **kwargs}
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        extra = {**self._get_extra_fields(), **kwargs}
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        extra = {**self._get_extra_fields(), **kwargs}
        self.logger.error(message, extra=extra)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        extra = {**self._get_extra_fields(), **kwargs}
        self.logger.critical(message, extra=extra)
    
    def exception(self, message: str, exc_info: bool = True, **kwargs):
        """Log exception with traceback."""
        extra = {**self._get_extra_fields(), **kwargs}
        self.logger.exception(message, extra=extra)
    
    def performance(self, operation: str, duration_ms: float, **kwargs):
        """Log performance metrics."""
        extra = {
            **self._get_extra_fields(),
            "operation": operation,
            "duration_ms": duration_ms,
            "metric_type": "performance",
            **kwargs
        }
        self.logger.info(f"Performance: {operation} took {duration_ms:.2f}ms", extra=extra)
    
    def request(self, method: str, path: str, status_code: int, 
                duration_ms: float, **kwargs):
        """Log HTTP request."""
        extra = {
            **self._get_extra_fields(),
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "metric_type": "request",
            **kwargs
        }
        self.logger.info(f"Request: {method} {path} -> {status_code} ({duration_ms:.2f}ms)", extra=extra)
    
    def database(self, operation: str, table: str, duration_ms: float, **kwargs):
        """Log database operations."""
        extra = {
            **self._get_extra_fields(),
            "operation": operation,
            "table": table,
            "duration_ms": duration_ms,
            "metric_type": "database",
            **kwargs
        }
        self.logger.info(f"Database: {operation} on {table} took {duration_ms:.2f}ms", extra=extra)
    
    def cache(self, operation: str, key: str, hit: bool, duration_ms: float, **kwargs):
        """Log cache operations."""
        extra = {
            **self._get_extra_fields(),
            "operation": operation,
            "key": key,
            "hit": hit,
            "duration_ms": duration_ms,
            "metric_type": "cache",
            **kwargs
        }
        cache_type = "HIT" if hit else "MISS"
        self.logger.info(f"Cache {cache_type}: {operation} {key} ({duration_ms:.2f}ms)", extra=extra)
    
    def security(self, event: str, user_id: Optional[str] = None, **kwargs):
        """Log security events."""
        extra = {
            **self._get_extra_fields(),
            "event": event,
            "user_id": user_id or self.user_id,
            "metric_type": "security",
            **kwargs
        }
        self.logger.warning(f"Security: {event}", extra=extra)
    
    def business(self, event: str, **kwargs):
        """Log business events."""
        extra = {
            **self._get_extra_fields(),
            "event": event,
            "metric_type": "business",
            **kwargs
        }
        self.logger.info(f"Business: {event}", extra=extra)


class LoggingContext:
    """Context manager for logging correlation."""
    
    def __init__(self, logger: SVGXLogger, request_id: Optional[str] = None,
                 session_id: Optional[str] = None, user_id: Optional[str] = None):
        """Initialize logging context."""
        self.logger = logger
        self.request_id = request_id or str(uuid.uuid4())
        self.session_id = session_id
        self.user_id = user_id
        self.previous_context = None
    
    def __enter__(self):
        """Enter logging context."""
        self.previous_context = (
            self.logger.request_id,
            self.logger.session_id,
            self.logger.user_id
        )
        self.logger.set_context(
            request_id=self.request_id,
            session_id=self.session_id,
            user_id=self.user_id
        )
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit logging context."""
        if self.previous_context:
            self.logger.set_context(*self.previous_context)


# Global logger instances
_loggers: Dict[str, SVGXLogger] = {}


def get_logger(name: str) -> SVGXLogger:
    """Get or create logger instance."""
    if name not in _loggers:
        _loggers[name] = SVGXLogger(name)
    return _loggers[name]


def setup_logging(config: Optional[Dict[str, Any]] = None):
    """Set up global logging configuration."""
    # Create default logger
    default_logger = SVGXLogger("svgx_engine", config)
    _loggers["svgx_engine"] = default_logger
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add console handler
    console_handler = logging.StreamHandler()
    formatter = StructuredFormatter()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


@contextmanager
def logging_context(logger_name: str = "svgx_engine", 
                   request_id: Optional[str] = None,
                   session_id: Optional[str] = None,
                   user_id: Optional[str] = None):
    """Context manager for logging correlation."""
    logger = get_logger(logger_name)
    with LoggingContext(logger, request_id, session_id, user_id) as ctx_logger:
        yield ctx_logger 