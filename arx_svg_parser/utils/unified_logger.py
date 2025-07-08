"""
Unified Logging Interface for Arxos Platform
Consolidates logging functionality across Python, JavaScript, and Go implementations
"""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Union
from enum import Enum
import threading
import time
import gzip
import shutil
from contextlib import contextmanager


class LogLevel(Enum):
    """Standardized log levels across all implementations"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LogFormat(Enum):
    """Supported log formats"""
    JSON = "json"
    TEXT = "text"
    STRUCTURED = "structured"


class UnifiedLogger:
    """
    Unified logging interface that provides consistent logging across
    Python, JavaScript, and Go implementations
    """
    
    def __init__(self, 
                 name: str = "arxos",
                 level: Union[LogLevel, str] = LogLevel.INFO,
                 format: LogFormat = LogFormat.JSON,
                 log_dir: Optional[Path] = None,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 enable_console: bool = True,
                 enable_file: bool = True,
                 enable_remote: bool = False,
                 remote_endpoint: Optional[str] = None):
        
        self.name = name
        self.level = self._parse_level(level)
        self.format = format
        self.log_dir = log_dir or Path("logs")
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_remote = enable_remote
        self.remote_endpoint = remote_endpoint
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize logging
        self._setup_logging()
        
        # Performance tracking
        self.metrics = {
            'total_logs': 0,
            'errors': 0,
            'warnings': 0,
            'last_rotation': None,
            'compressed_files': 0
        }
        self.metrics_lock = threading.Lock()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _parse_level(self, level: Union[LogLevel, str]) -> LogLevel:
        """Parse log level from string or enum"""
        if isinstance(level, LogLevel):
            return level
        
        level_map = {
            'debug': LogLevel.DEBUG,
            'info': LogLevel.INFO,
            'warning': LogLevel.WARNING,
            'error': LogLevel.ERROR,
            'critical': LogLevel.CRITICAL
        }
        
        return level_map.get(level.lower(), LogLevel.INFO)
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Create logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.level.value)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.level.value)
            console_handler.setFormatter(self._get_formatter())
            self.logger.addHandler(console_handler)
        
        # File handler
        if self.enable_file:
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_dir / f"{self.name}.log",
                maxBytes=self.max_file_size,
                backupCount=self.backup_count
            )
            file_handler.setLevel(self.level.value)
            file_handler.setFormatter(self._get_formatter())
            self.logger.addHandler(file_handler)
    
    def _get_formatter(self):
        """Get appropriate formatter based on format type"""
        if self.format == LogFormat.JSON:
            return logging.Formatter('%(message)s')
        elif self.format == LogFormat.STRUCTURED:
            return logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            )
        else:  # TEXT
            return logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
    
    def _create_log_entry(self, 
                         level: LogLevel, 
                         message: str, 
                         context: Optional[Dict[str, Any]] = None,
                         **kwargs) -> Dict[str, Any]:
        """Create standardized log entry"""
        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': level.name.lower(),
            'logger': self.name,
            'message': message,
            'environment': os.getenv('ARX_ENVIRONMENT', 'development'),
            'version': os.getenv('ARX_VERSION', '1.0.0'),
            'correlation_id': kwargs.get('correlation_id'),
            'request_id': kwargs.get('request_id'),
            'user_id': kwargs.get('user_id'),
            'session_id': kwargs.get('session_id')
        }
        
        if context:
            entry['context'] = context
        
        # Add any additional fields
        for key, value in kwargs.items():
            if key not in ['correlation_id', 'request_id', 'user_id', 'session_id']:
                entry[key] = value
        
        return entry
    
    def _log(self, level: LogLevel, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Internal logging method"""
        if level.value < self.level.value:
            return
        
        entry = self._create_log_entry(level, message, context, **kwargs)
        
        if self.format == LogFormat.JSON:
            log_message = json.dumps(entry, default=str)
        else:
            log_message = f"{entry['timestamp']} [{level.name}] {message}"
            if context:
                log_message += f" | Context: {json.dumps(context, default=str)}"
        
        # Log to handlers
        self.logger.log(level.value, log_message)
        
        # Update metrics
        with self.metrics_lock:
            self.metrics['total_logs'] += 1
            if level == LogLevel.ERROR:
                self.metrics['errors'] += 1
            elif level == LogLevel.WARNING:
                self.metrics['warnings'] += 1
        
        # Send to remote if enabled
        if self.enable_remote and self.remote_endpoint:
            self._send_to_remote(entry)
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log debug message"""
        self._log(LogLevel.DEBUG, message, context, **kwargs)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log info message"""
        self._log(LogLevel.INFO, message, context, **kwargs)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log warning message"""
        self._log(LogLevel.WARNING, message, context, **kwargs)
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log error message"""
        self._log(LogLevel.ERROR, message, context, **kwargs)
    
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log critical message"""
        self._log(LogLevel.CRITICAL, message, context, **kwargs)
    
    def exception(self, message: str, exc_info: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log exception with traceback"""
        if exc_info:
            kwargs['exception'] = {
                'type': type(exc_info).__name__,
                'message': str(exc_info),
                'traceback': self._get_traceback(exc_info)
            }
        
        self._log(LogLevel.ERROR, message, context, **kwargs)
    
    def _get_traceback(self, exc_info: Exception) -> str:
        """Get formatted traceback for exception"""
        import traceback
        return ''.join(traceback.format_exception(type(exc_info), exc_info, exc_info.__traceback__))
    
    def _send_to_remote(self, entry: Dict[str, Any]):
        """Send log entry to remote logging service"""
        try:
            import requests
            requests.post(self.remote_endpoint, json=entry, timeout=5)
        except Exception as e:
            # Don't log remote logging failures to avoid infinite loops
            print(f"Failed to send log to remote: {e}")
    
    def _start_background_tasks(self):
        """Start background tasks for log management"""
        # Log rotation task
        rotation_thread = threading.Thread(target=self._rotation_task, daemon=True)
        rotation_thread.start()
        
        # Compression task
        compression_thread = threading.Thread(target=self._compression_task, daemon=True)
        compression_thread.start()
        
        # Cleanup task
        cleanup_thread = threading.Thread(target=self._cleanup_task, daemon=True)
        cleanup_thread.start()
    
    def _rotation_task(self):
        """Background task for log rotation"""
        while True:
            try:
                time.sleep(60 * 60)  # 1 hour
                self._rotate_logs()
            except Exception as e:
                print(f"Log rotation error: {e}")
    
    def _rotate_logs(self):
        """Rotate log files"""
        try:
            for handler in self.logger.handlers:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    handler.doRollover()
            
            with self.metrics_lock:
                self.metrics['last_rotation'] = datetime.now()
            
            self.info("Log files rotated successfully")
            
        except Exception as e:
            self.error(f"Log rotation failed: {e}")
    
    def _compression_task(self):
        """Background task for log compression"""
        while True:
            try:
                time.sleep(60 * 60)  # 1 hour
                self._compress_old_logs()
            except Exception as e:
                print(f"Log compression error: {e}")
    
    def _compress_old_logs(self):
        """Compress log files older than 1 day"""
        try:
            cutoff_time = datetime.now() - timedelta(days=1)
            
            for log_file in self.log_dir.glob("*.log.*"):
                if log_file.stat().st_mtime < cutoff_time.timestamp():
                    if not log_file.name.endswith('.gz'):
                        self._compress_file(log_file)
                        
        except Exception as e:
            self.error(f"Log compression failed: {e}")
    
    def _compress_file(self, file_path: Path):
        """Compress a single log file"""
        try:
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            file_path.unlink()
            
            with self.metrics_lock:
                self.metrics['compressed_files'] += 1
            
            self.info(f"Compressed log file: {file_path.name}")
            
        except Exception as e:
            self.error(f"Failed to compress {file_path}: {e}")
    
    def _cleanup_task(self):
        """Background task for log cleanup"""
        while True:
            try:
                time.sleep(24 * 60 * 60)  # 24 hours
                self._cleanup_old_logs()
            except Exception as e:
                print(f"Log cleanup error: {e}")
    
    def _cleanup_old_logs(self):
        """Clean up old log files based on retention policy"""
        try:
            # Keep logs for 30 days
            cutoff_time = datetime.now() - timedelta(days=30)
            
            for log_file in self.log_dir.glob("*.log.*.gz"):
                if log_file.stat().st_mtime < cutoff_time.timestamp():
                    log_file.unlink()
                    self.info(f"Cleaned up old log file: {log_file.name}")
                    
        except Exception as e:
            self.error(f"Log cleanup failed: {e}")
    
    @contextmanager
    def context(self, **context_data):
        """Context manager for adding context to log messages"""
        old_context = getattr(self, '_context', {})
        self._context = {**old_context, **context_data}
        
        try:
            yield self
        finally:
            self._context = old_context
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get logging metrics"""
        with self.metrics_lock:
            return self.metrics.copy()
    
    def set_level(self, level: Union[LogLevel, str]):
        """Set log level"""
        self.level = self._parse_level(level)
        self.logger.setLevel(self.level.value)
    
    def add_context(self, **context_data):
        """Add context data to subsequent log messages"""
        if not hasattr(self, '_context'):
            self._context = {}
        self._context.update(context_data)
    
    def clear_context(self):
        """Clear context data"""
        if hasattr(self, '_context'):
            del self._context


# Global logger instance
logger = UnifiedLogger()

# Convenience functions
def debug(message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
    """Global debug logging"""
    logger.debug(message, context, **kwargs)

def info(message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
    """Global info logging"""
    logger.info(message, context, **kwargs)

def warning(message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
    """Global warning logging"""
    logger.warning(message, context, **kwargs)

def error(message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
    """Global error logging"""
    logger.error(message, context, **kwargs)

def critical(message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
    """Global critical logging"""
    logger.critical(message, context, **kwargs)

def exception(message: str, exc_info: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None, **kwargs):
    """Global exception logging"""
    logger.exception(message, exc_info, context, **kwargs)


# Utility functions for correlation IDs and request tracking
def generate_correlation_id() -> str:
    """Generate a unique correlation ID"""
    import uuid
    return str(uuid.uuid4())

def generate_request_id() -> str:
    """Generate a unique request ID"""
    import uuid
    return str(uuid.uuid4())


# Export the main logger instance
__all__ = [
    'UnifiedLogger', 'LogLevel', 'LogFormat', 'logger',
    'debug', 'info', 'warning', 'error', 'critical', 'exception',
    'generate_correlation_id', 'generate_request_id'
] 