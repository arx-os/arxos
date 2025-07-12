import logging
import logging.handlers
import json
import os
import sys
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union
from contextvars import ContextVar
import traceback
from functools import wraps
import threading
from dataclasses import dataclass, asdict
from pathlib import Path
import gzip
import shutil
from queue import Queue
import asyncio
import aiofiles
import aiohttp

# Context variables for correlation tracking
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
request_id: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
session_id: ContextVar[Optional[str]] = ContextVar('session_id', default=None)

@dataclass
class LogContext:
    """Structured log context for correlation and tracing"""
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    building_id: Optional[str] = None
    floor_id: Optional[str] = None
    object_id: Optional[str] = None
    object_type: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    component: Optional[str] = None
    service: str = "arx-svg-parser"
    version: str = "1.0.0"
    environment: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class StructuredJSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def __init__(self):
        super().__init__()
        self.default_fields = {
            'timestamp': None,
            'level': None,
            'logger': None,
            'message': None,
            'correlation_id': None,
            'request_id': None,
            'user_id': None,
            'session_id': None,
            'building_id': None,
            'floor_id': None,
            'object_id': None,
            'object_type': None,
            'endpoint': None,
            'method': None,
            'ip_address': None,
            'user_agent': None,
            'component': None,
            'service': None,
            'version': None,
            'environment': None,
            'metadata': None,
            'exception': None,
            'stack_trace': None,
            'performance': None,
        }
    
    def format(self, record):
        # Get context values
        ctx_correlation_id = correlation_id.get()
        ctx_request_id = request_id.get()
        ctx_user_id = user_id.get()
        ctx_session_id = session_id.get()
        
        # Create structured log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': ctx_correlation_id,
            'request_id': ctx_request_id,
            'user_id': ctx_user_id,
            'session_id': ctx_session_id,
        }
        
        # Add extra fields from record
        if hasattr(record, 'building_id'):
            log_entry['building_id'] = record.building_id
        if hasattr(record, 'floor_id'):
            log_entry['floor_id'] = record.floor_id
        if hasattr(record, 'object_id'):
            log_entry['object_id'] = record.object_id
        if hasattr(record, 'object_type'):
            log_entry['object_type'] = record.object_type
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        if hasattr(record, 'user_agent'):
            log_entry['user_agent'] = record.user_agent
        if hasattr(record, 'component'):
            log_entry['component'] = record.component
        if hasattr(record, 'service'):
            log_entry['service'] = record.service
        if hasattr(record, 'version'):
            log_entry['version'] = record.version
        if hasattr(record, 'environment'):
            log_entry['environment'] = record.environment
        if hasattr(record, 'metadata'):
            log_entry['metadata'] = record.metadata
        if hasattr(record, 'performance'):
            log_entry['performance'] = record.performance
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'stack_trace': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_entry, default=str)

class ArxLogger:
    """
    Enhanced ArxLogger with performance optimizations, structured logging,
    and comprehensive monitoring capabilities.
    """
    
    def __init__(self, name: str = "arx_svg_parser", log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Performance tracking
        self.processing_times = []
        self.entry_sizes = []
        self.performance_lock = threading.Lock()
        
        # Context variables for correlation tracking
        self.context_vars = threading.local()
        self.context_vars.correlation_id = None
        self.context_vars.request_id = None
        self.context_vars.user_id = None
        self.context_vars.building_id = None
        
        # Log buffer for async processing
        self.log_buffer = Queue(maxsize=1000)
        self.buffer_worker = threading.Thread(target=self._buffer_worker, daemon=True)
        self.buffer_worker.start()
        
        # Performance metrics
        self.metrics = {
            'total_logs': 0,
            'total_size': 0,
            'avg_processing_time': 0.0,
            'slow_logs': 0,
            'large_logs': 0,
            'errors': 0,
            'last_rotation': datetime.now(),
            'compressed_files': 0
        }
        self.metrics_lock = threading.Lock()
        
        # Setup loggers with performance optimizations
        self._setup_loggers()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _setup_loggers(self):
        """Setup loggers with performance optimizations and rotation"""
        # Main logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler with performance optimizations
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with rotation and compression
        log_file = self.log_dir / f"{self.name}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=30,  # 30 days retention
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # JSON formatter for structured logging
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno,
                    'correlation_id': getattr(record, 'correlation_id', None),
                    'request_id': getattr(record, 'request_id', None),
                    'user_id': getattr(record, 'user_id', None),
                    'building_id': getattr(record, 'building_id', None),
                    'processing_time_ms': getattr(record, 'processing_time_ms', None),
                    'entry_size': getattr(record, 'entry_size', None)
                }
                
                # Add extra fields
                if hasattr(record, 'extra_fields'):
                    log_entry.update(record.extra_fields)
                
                return json.dumps(log_entry, ensure_ascii=False)
        
        file_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(file_handler)
        
        # Error handler for critical errors
        error_file = self.log_dir / f"{self.name}_error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=30,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(error_handler)
        
        # Performance handler for slow operations
        perf_file = self.log_dir / f"{self.name}_performance.log"
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_file,
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=7,  # 7 days for performance logs
            encoding='utf-8'
        )
        perf_handler.setLevel(logging.WARNING)
        perf_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(perf_handler)
    
    def _buffer_worker(self):
        """Background worker for processing log entries asynchronously"""
        while True:
            try:
                entry = self.log_buffer.get(timeout=1)
                if entry is None:  # Shutdown signal
                    break
                
                self._process_log_entry(entry)
                self.log_buffer.task_done()
                
            except Exception as e:
                # Fallback to synchronous logging
                print(f"Buffer worker error: {e}")
    
    def _process_log_entry(self, entry: Dict[str, Any]):
        """Process a single log entry with performance monitoring"""
        start_time = time.time()
        
        # Check entry size
        entry_size = len(json.dumps(entry))
        if entry_size > 1024:  # 1KB limit
            # Truncate message if too large
            if len(entry.get('message', '')) > 512:
                entry['message'] = entry['message'][:512] + "... [truncated]"
                entry['truncated'] = True
            
            with self.metrics_lock:
                self.metrics['large_logs'] += 1
        
        # Create log record
        record = logging.LogRecord(
            name=entry.get('logger', self.name),
            level=entry.get('level', logging.INFO),
            pathname=entry.get('pathname', ''),
            lineno=entry.get('lineno', 0),
            msg=entry.get('message', ''),
            args=(),
            exc_info=entry.get('exc_info')
        )
        
        # Add custom attributes
        record.correlation_id = entry.get('correlation_id')
        record.request_id = entry.get('request_id')
        record.user_id = entry.get('user_id')
        record.building_id = entry.get('building_id')
        record.processing_time_ms = entry.get('processing_time_ms')
        record.entry_size = entry_size
        record.extra_fields = entry.get('extra_fields', {})
        
        # Log the record
        self.logger.handle(record)
        
        # Track processing time
        processing_time = time.time() - start_time
        if processing_time > 0.001:  # 1ms target
            with self.metrics_lock:
                self.metrics['slow_logs'] += 1
            
            # Log slow processing as warning
            self.warning(
                "Log entry processing exceeded target time",
                extra_fields={
                    'processing_time_ms': processing_time * 1000,
                    'target_time_ms': 1000,
                    'entry_size': entry_size,
                    'level': entry.get('level')
                }
            )
        
        # Update metrics
        with self.metrics_lock:
            self.metrics['total_logs'] += 1
            self.metrics['total_size'] += entry_size
            self.metrics['avg_processing_time'] = (
                (self.metrics['avg_processing_time'] * (self.metrics['total_logs'] - 1) + processing_time) 
                / self.metrics['total_logs']
            )
    
    def _start_background_tasks(self):
        """Start background tasks for maintenance"""
        # Log rotation task
        rotation_thread = threading.Thread(target=self._rotation_task, daemon=True)
        rotation_thread.start()
        
        # Compression task
        compression_thread = threading.Thread(target=self._compression_task, daemon=True)
        compression_thread.start()
        
        # Retention cleanup task
        cleanup_thread = threading.Thread(target=self._cleanup_task, daemon=True)
        cleanup_thread.start()
        
        # Metrics reporting task
        metrics_thread = threading.Thread(target=self._metrics_task, daemon=True)
        metrics_thread.start()
    
    def _rotation_task(self):
        """Daily log rotation task"""
        while True:
            try:
                time.sleep(24 * 60 * 60)  # 24 hours
                self._rotate_logs()
            except Exception as e:
                print(f"Log rotation error: {e}")
    
    def _rotate_logs(self):
        """Rotate log files"""
        try:
            # Trigger rotation for all handlers
            for handler in self.logger.handlers:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    handler.doRollover()
            
            with self.metrics_lock:
                self.metrics['last_rotation'] = datetime.now()
            
            self.info("Log files rotated successfully")
            
        except Exception as e:
            self.error(f"Log rotation failed: {e}")
    
    def _compression_task(self):
        """Compress old log files"""
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
        """Clean up old log files based on retention policy"""
        while True:
            try:
                time.sleep(24 * 60 * 60)  # 24 hours
                self._cleanup_old_logs()
            except Exception as e:
                print(f"Log cleanup error: {e}")
    
    def _cleanup_old_logs(self):
        """Clean up old log files based on retention policy"""
        try:
            now = datetime.now()
            
            for log_file in self.log_dir.glob("*.log*"):
                file_age = now - datetime.fromtimestamp(log_file.stat().st_mtime)
                
                # Determine retention based on file type
                retention_days = 30  # Default
                
                if 'debug' in log_file.name.lower():
                    retention_days = 7
                elif 'error' in log_file.name.lower():
                    retention_days = 30
                elif 'performance' in log_file.name.lower():
                    retention_days = 30
                
                if file_age.days > retention_days:
                    log_file.unlink()
                    self.info(f"Deleted old log file: {log_file.name} (age: {file_age.days} days)")
                    
        except Exception as e:
            self.error(f"Log cleanup failed: {e}")
    
    def _metrics_task(self):
        """Report metrics periodically"""
        while True:
            try:
                time.sleep(300)  # 5 minutes
                self._report_metrics()
            except Exception as e:
                print(f"Metrics reporting error: {e}")
    
    def _report_metrics(self):
        """Report current metrics"""
        with self.metrics_lock:
            metrics = self.metrics.copy()
        
        self.info(
            "Logging metrics report",
            extra_fields={
                'total_logs': metrics['total_logs'],
                'total_size_mb': round(metrics['total_size'] / (1024 * 1024), 2),
                'avg_processing_time_ms': round(metrics['avg_processing_time'] * 1000, 3),
                'slow_logs': metrics['slow_logs'],
                'large_logs': metrics['large_logs'],
                'errors': metrics['errors'],
                'compressed_files': metrics['compressed_files']
            }
        )
    
    def set_context(self, correlation_id: str = None, request_id: str = None, 
                   user_id: int = None, building_id: int = None):
        """Set context variables for correlation tracking"""
        if correlation_id:
            self.context_vars.correlation_id = correlation_id
        if request_id:
            self.context_vars.request_id = request_id
        if user_id:
            self.context_vars.user_id = user_id
        if building_id:
            self.context_vars.building_id = building_id
    
    def clear_context(self):
        """Clear context variables"""
        self.context_vars.correlation_id = None
        self.context_vars.request_id = None
        self.context_vars.user_id = None
        self.context_vars.building_id = None
    
    def _log(self, level: int, message: str, extra_fields: Dict[str, Any] = None):
        """Internal logging method with performance optimizations"""
        start_time = time.time()
        
        # Check message size
        if len(message) > 1024 // 2:
            message = message[:1024 // 2] + "... [truncated]"
        
        # Create log entry
        entry = {
            'logger': self.name,
            'level': level,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'correlation_id': getattr(self.context_vars, 'correlation_id', None),
            'request_id': getattr(self.context_vars, 'request_id', None),
            'user_id': getattr(self.context_vars, 'user_id', None),
            'building_id': getattr(self.context_vars, 'building_id', None),
            'extra_fields': extra_fields or {},
            'pathname': __file__,
            'lineno': 0
        }
        
        # Add to buffer for async processing
        try:
            self.log_buffer.put_nowait(entry)
        except Exception:
            # Buffer full, process synchronously
            self._process_log_entry(entry)
        
        # Track performance
        processing_time = time.time() - start_time
        with self.performance_lock:
            self.processing_times.append(processing_time)
            if len(self.processing_times) > 1000:
                self.processing_times.pop(0)
    
    def debug(self, message: str, extra_fields: Dict[str, Any] = None):
        """Log debug message"""
        self._log(logging.DEBUG, message, extra_fields)
    
    def info(self, message: str, extra_fields: Dict[str, Any] = None):
        """Log info message"""
        self._log(logging.INFO, message, extra_fields)
    
    def warning(self, message: str, extra_fields: Dict[str, Any] = None):
        """Log warning message"""
        self._log(logging.WARNING, message, extra_fields)
    
    def error(self, message: str, extra_fields: Dict[str, Any] = None):
        """Log error message"""
        with self.metrics_lock:
            self.metrics['errors'] += 1
        self._log(logging.ERROR, message, extra_fields)
    
    def critical(self, message: str, extra_fields: Dict[str, Any] = None):
        """Log critical message"""
        with self.metrics_lock:
            self.metrics['errors'] += 1
        self._log(logging.CRITICAL, message, extra_fields)
    
    def performance(self, operation: str, duration: float, metadata: Dict[str, Any] = None):
        """Log performance metrics"""
        extra_fields = {
            'operation': operation,
            'duration_ms': round(duration * 1000, 3),
            'performance_metric': True
        }
        if metadata:
            extra_fields.update(metadata)
        
        self._log(logging.WARNING, f"Performance: {operation}", extra_fields)
    
    def business_event(self, event_type: str, event_name: str, metrics: Dict[str, Any] = None):
        """Log business events"""
        extra_fields = {
            'event_type': event_type,
            'event_name': event_name,
            'business_event': True
        }
        if metrics:
            extra_fields.update(metrics)
        
        self._log(logging.INFO, f"Business event: {event_type} - {event_name}", extra_fields)
    
    def api_request(self, method: str, endpoint: str, status_code: int, 
                   duration: float, response_size: int = None):
        """Log API requests"""
        extra_fields = {
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'duration_ms': round(duration * 1000, 3),
            'api_request': True
        }
        if response_size:
            extra_fields['response_size'] = response_size
        
        level = logging.INFO if status_code < 400 else logging.WARNING
        self._log(level, f"API {method} {endpoint} - {status_code}", extra_fields)
    
    def api_error(self, method: str, endpoint: str, error: Exception, 
                 status_code: int = None):
        """Log API errors"""
        extra_fields = {
            'method': method,
            'endpoint': endpoint,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'api_error': True
        }
        if status_code:
            extra_fields['status_code'] = status_code
        
        self._log(logging.ERROR, f"API Error {method} {endpoint}", 
                 extra_fields)
    
    def security_event(self, event_type: str, severity: str, 
                      details: Dict[str, Any] = None):
        """Log security events"""
        extra_fields = {
            'event_type': event_type,
            'severity': severity,
            'security_event': True
        }
        if details:
            extra_fields.update(details)
        
        level = logging.WARNING if severity == 'low' else logging.ERROR
        self._log(level, f"Security event: {event_type}", extra_fields)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current logging metrics"""
        with self.metrics_lock:
            metrics = self.metrics.copy()
        
        with self.performance_lock:
            if self.processing_times:
                metrics['recent_avg_processing_time_ms'] = round(
                    sum(self.processing_times) / len(self.processing_times) * 1000, 
                    3
                )
            else:
                metrics['recent_avg_processing_time_ms'] = 0.0
        
        return metrics
    
    def performance_tracker(self, operation: str):
        """Decorator for tracking function performance"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.performance(operation, duration)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.performance(operation, duration, {'error': str(e)})
                    raise
            return wrapper
        return decorator
    
    async def async_performance_tracker(self, operation: str):
        """Decorator for tracking async function performance"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.performance(operation, duration)
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.performance(operation, duration, {'error': str(e)})
                    raise
            return wrapper
        return decorator
    
    def shutdown(self):
        """Shutdown the logger gracefully"""
        # Send shutdown signal to buffer worker
        self.log_buffer.put(None)
        
        # Wait for buffer to be processed
        self.log_buffer.join()
        
        # Report final metrics
        self._report_metrics()
        
        # Close handlers
        for handler in self.logger.handlers:
            handler.close()

# Global logger instance
logger = ArxLogger()

# Set environment from environment variable
logger.logger.environment = os.getenv('ARX_ENVIRONMENT', 'development')

def get_logger(name: str = None) -> ArxLogger:
    """Get logger instance for compatibility"""
    return logger 