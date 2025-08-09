"""
SVGX Engine - Telemetry Utilities

This module provides telemetry logging utilities for SVGX Engine.
"""

import time
import threading
import json
import platform
import os
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from contextlib import contextmanager

logger = None
try:
    from structlog import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log levels for telemetry."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class TelemetryType(Enum):
    """Telemetry types."""
    SVGX_PERFORMANCE = "svgx_performance"
    SVGX_OPERATION = "svgx_operation"
    SVGX_ERROR = "svgx_error"
    SVGX_SECURITY = "svgx_security"


class TelemetrySeverity(Enum):
    """Telemetry severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class TelemetryRecord:
    """Telemetry record structure."""
    timestamp: float
    source: str
    type: TelemetryType
    value: Dict[str, Any]
    namespace: str = "svgx_engine"
    component: str = "utils"
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    status: str = "OK"
    severity: TelemetrySeverity = TelemetrySeverity.INFO
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TelemetryConfig:
    """Configuration for telemetry logging."""
    enabled: bool = True
    buffer_size: int = 10000
    enable_persistence: bool = True
    log_to_console: bool = True
    log_to_file: bool = False
    log_file_path: Optional[str] = None
    include_system_info: bool = True
    include_performance_metrics: bool = True
    namespace: str = "svgx_engine"
    component: str = "utils"


class TelemetryBuffer:
    """Simple telemetry buffer."""

    def __init__(self, max_size: int = 10000, enable_persistence: bool = True):
    """
    Perform __init__ operation

Args:
        max_size: Description of max_size
        enable_persistence: Description of enable_persistence

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.max_size = max_size
        self.enable_persistence = enable_persistence
        self.records: List[TelemetryRecord] = []
        self._lock = threading.Lock()
        self._running = False

    def start(self):
        """Start the buffer."""
        self._running = True

    def stop(self):
        """Stop the buffer."""
        self._running = False

    def ingest(self, record: TelemetryRecord):
        """Add a record to the buffer."""
        if not self._running:
            return

        with self._lock:
            self.records.append(record)
            if len(self.records) > self.max_size:
                self.records.pop(0)

    def get_records(self) -> List[TelemetryRecord]:
        """Get all records."""
        with self._lock:
            return self.records.copy()

    def clear(self):
        """Clear all records."""
        with self._lock:
            self.records.clear()


def create_svgx_telemetry_buffer(max_size: int = 10000, enable_persistence: bool = True) -> TelemetryBuffer:
    """Create a telemetry buffer."""
    return TelemetryBuffer(max_size=max_size, enable_persistence=enable_persistence)


class TelemetryLogger:
    """Comprehensive telemetry logger for SVGX Engine."""

    def __init__(self, config: Optional[TelemetryConfig] = None):
        """Initialize the telemetry logger."""
        self.config = config or TelemetryConfig()
        self.buffer = create_svgx_telemetry_buffer(
            max_size=self.config.buffer_size,
            enable_persistence=self.config.enable_persistence
        )
        self.session_id = self._generate_session_id()
        self.user_id = None
        self._lock = threading.Lock()

        # Start the buffer if enabled
        if self.config.enabled:
            self.buffer.start()

        if logger:
            logger.info("TelemetryLogger initialized", config=self.config)

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"session_{int(time.time())}_{threading.get_ident()}"

    def set_user_id(self, user_id: str):
        """Set the current user ID for telemetry."""
        self.user_id = user_id
        if logger:
            logger.debug("User ID set for telemetry", user_id=user_id)

    def log_event(self, event_type: str, message: str, level: LogLevel = LogLevel.INFO,
                  metadata: Optional[Dict[str, Any]] = None, duration_ms: Optional[float] = None):
        """Log a telemetry event."""
        if not self.config.enabled:
            return

        try:
            # Map log level to telemetry severity
            severity_map = {
                LogLevel.DEBUG: TelemetrySeverity.DEBUG,
                LogLevel.INFO: TelemetrySeverity.INFO,
                LogLevel.WARNING: TelemetrySeverity.WARNING,
                LogLevel.ERROR: TelemetrySeverity.ERROR,
                LogLevel.CRITICAL: TelemetrySeverity.CRITICAL
            }

            # Create telemetry record
            record = TelemetryRecord(
                timestamp=time.time(),
                source=self.config.component,
                type=TelemetryType.SVGX_PERFORMANCE,  # Default type
                value={
                    'event_type': event_type,
                    'message': message,
                    'level': level.value,
                    'metadata': metadata or {}
                },
                namespace=self.config.namespace,
                component=self.config.component,
                user_id=self.user_id,
                session_id=self.session_id,
                status="OK",
                severity=severity_map[level],
                duration_ms=duration_ms,
                memory_usage_mb=self._get_memory_usage(),
                cpu_usage_percent=self._get_cpu_usage(),
                meta={
                    'platform': platform.system(),
                    'python_version': platform.python_version(),
                    'timestamp_iso': datetime.now().isoformat()
                }
            )

            # Add to buffer
            self.buffer.ingest(record)

            # Console logging if enabled
            if self.config.log_to_console:
                self._log_to_console(level, event_type, message, metadata)

            # File logging if enabled
            if self.config.log_to_file and self.config.log_file_path:
                self._log_to_file(record)

        except Exception as e:
            if logger:
                logger.error(f"Failed to log telemetry event: {e}")

    def log_operation(self, operation_name: str, operation_type: TelemetryType,
                      metadata: Optional[Dict[str, Any]] = None):
        """Log an operation with context manager support."""
        return OperationLogger(self, operation_name, operation_type, metadata)

    def log_error(self, error_type: str, error_message: str,
                  error_details: Optional[Dict[str, Any]] = None):
        """Log an error event."""
        metadata = {
            'error_type': error_type,
            'error_details': error_details or {}
        }
        self.log_event(
            event_type="error",
            message=error_message,
            level=LogLevel.ERROR,
            metadata=metadata
        )

    def log_performance(self, operation_name: str, duration_ms: float,
                       metadata: Optional[Dict[str, Any]] = None):
        """Log a performance metric."""
        perf_metadata = {
            'operation_name': operation_name,
            'duration_ms': duration_ms,
            **(metadata or {})
        }
        self.log_event(
            event_type="performance",
            message=f"Operation '{operation_name}' completed in {duration_ms:.2f}ms",
            level=LogLevel.INFO,
            metadata=perf_metadata,
            duration_ms=duration_ms
        )

    def log_security(self, security_event: str, details: Optional[Dict[str, Any]] = None):
        """Log a security event."""
        security_metadata = {
            'security_event': security_event,
            'details': details or {}
        }
        self.log_event(
            event_type="security",
            message=f"Security event: {security_event}",
            level=LogLevel.WARNING,
            metadata=security_metadata
        )

    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return None
        except Exception:
            return None

    def _get_cpu_usage(self) -> Optional[float]:
        """Get current CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return None
        except Exception:
            return None

    def _log_to_console(self, level: LogLevel, event_type: str, message: str,
                        metadata: Optional[Dict[str, Any]] = None):
        """Log to console."""
        if logger:
            log_data = {
                'event_type': event_type,
                'message': message,
                'level': level.value,
                'metadata': metadata or {}
            }
            logger.info("Telemetry event", **log_data)

    def _log_to_file(self, record: TelemetryRecord):
        """Log to file."""
        try:
            with open(self.config.log_file_path, 'a') as f:
                f.write(json.dumps(record.__dict__, default=str) + '\n')
        except Exception as e:
            if logger:
                logger.error(f"Failed to write to telemetry file: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get telemetry statistics."""
        records = self.buffer.get_records()
        if not records:
            return {}

        return {
            'total_records': len(records),
            'session_id': self.session_id,
            'user_id': self.user_id,
            'enabled': self.config.enabled
        }

    def clear_statistics(self):
        """Clear telemetry statistics."""
        self.buffer.clear()

    def shutdown(self):
        """Shutdown the telemetry logger."""
        self.buffer.stop()
        if logger:
            logger.info("TelemetryLogger shutdown")


class OperationLogger:
    """
    Perform __init__ operation

Args:
        telemetry_logger: Description of telemetry_logger
        operation_name: Description of operation_name
        operation_type: Description of operation_type
        metadata: Description of metadata

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Context manager for logging operations."""

    def __init__(self, telemetry_logger: TelemetryLogger, operation_name: str,
                 operation_type: TelemetryType, metadata: Optional[Dict[str, Any]] = None):
        self.telemetry_logger = telemetry_logger
        self.operation_name = operation_name
        self.operation_type = operation_type
        self.metadata = metadata or {}
        self.start_time = None

    def __enter__(self):
        """Enter the operation context."""
        self.start_time = time.time()
        self.telemetry_logger.log_event(
            event_type="operation_start",
            message=f"Starting operation: {self.operation_name}",
            level=LogLevel.INFO,
            metadata=self.metadata
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the operation context."""
        duration_ms = (time.time() - self.start_time) * 1000 if self.start_time else 0

        if exc_type is None:
            # Operation completed successfully
            self.telemetry_logger.log_event(
                event_type="operation_complete",
                message=f"Operation completed: {self.operation_name}",
                level=LogLevel.INFO,
                metadata={**self.metadata, 'duration_ms': duration_ms},
                duration_ms=duration_ms
            )
        else:
            # Operation failed
            self.telemetry_logger.log_event(
                event_type="operation_error",
                message=f"Operation failed: {self.operation_name} - {exc_val}",
                level=LogLevel.ERROR,
                metadata={**self.metadata, 'duration_ms': duration_ms, 'error': str(exc_val)},
                duration_ms=duration_ms
            )


def get_telemetry_logger(config: Optional[TelemetryConfig] = None) -> TelemetryLogger:
    """Get a telemetry logger instance."""
    return TelemetryLogger(config)


def log_telemetry_event(event_type: str, message: str, level: LogLevel = LogLevel.INFO,
                        metadata: Optional[Dict[str, Any]] = None):
    """Log a telemetry event using the default logger."""
    logger = get_telemetry_logger()
    logger.log_event(event_type, message, level, metadata)


def log_telemetry_operation(operation_name: str, operation_type: TelemetryType,
                           metadata: Optional[Dict[str, Any]] = None):
    """Log a telemetry operation using the default logger."""
    logger = get_telemetry_logger()
    return logger.log_operation(operation_name, operation_type, metadata)


def shutdown_telemetry():
    """Shutdown the default telemetry logger."""
    logger = get_telemetry_logger()
    logger.shutdown()
