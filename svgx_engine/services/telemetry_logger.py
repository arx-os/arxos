"""
SVGX Engine - Telemetry Logger Service

Provides telemetry logging functionality for performance monitoring
and operational insights.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TelemetryEventType(Enum):
    """Types of telemetry events."""

    PERFORMANCE = "performance"
    OPERATION = "operation"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


@dataclass
class TelemetryEvent:
    """Represents a telemetry event."""

    event_type: TelemetryEventType
    operation_name: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


class TelemetryLogger:
    """Telemetry logger for performance monitoring and operational insights."""

    def __init__(self):
        self.events: List[TelemetryEvent] = []
        self.enabled = True

    def log_event(
        self,
        event_type: TelemetryEventType,
        operation_name: str,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ):
        """Log a telemetry event."""
        if not self.enabled:
            return

        event = TelemetryEvent(
            event_type=event_type,
            operation_name=operation_name,
            duration_ms=duration_ms,
            metadata=metadata or {},
            error_message=error_message,
        )

        self.events.append(event)

        # Log to standard logger
        log_message = f"Telemetry: {event_type.value} - {operation_name}"
        if duration_ms:
            log_message += f" ({duration_ms:.2f}ms)"
        if error_message:
            log_message += f" - Error: {error_message}"

        if event_type == TelemetryEventType.ERROR:
            logger.error(log_message)
        elif event_type == TelemetryEventType.WARNING:
            logger.warning(log_message)
        elif event_type == TelemetryEventType.PERFORMANCE:
            logger.info(log_message)
        else:
            logger.debug(log_message)

    def log_performance(
        self,
        operation_name: str,
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log a performance event."""
        self.log_event(
            TelemetryEventType.PERFORMANCE, operation_name, duration_ms, metadata
        )

    def log_operation(
        self, operation_name: str, metadata: Optional[Dict[str, Any]] = None
    ):
        """Log an operation event."""
        self.log_event(TelemetryEventType.OPERATION, operation_name, metadata=metadata)

    def log_error(
        self,
        operation_name: str,
        error_message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log an error event."""
        self.log_event(
            TelemetryEventType.ERROR,
            operation_name,
            error_message=error_message,
            metadata=metadata,
        )

    def log_warning(
        self,
        operation_name: str,
        warning_message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log a warning event."""
        self.log_event(TelemetryEventType.WARNING, operation_name, metadata=metadata)

    def get_statistics(self) -> Dict[str, Any]:
        """Get telemetry statistics."""
        if not self.events:
            return {"total_events": 0}

        total_events = len(self.events)
        events_by_type = {}
        total_duration = 0
        error_count = 0

        for event in self.events:
            event_type = event.event_type.value
            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1

            if event.duration_ms:
                total_duration += event.duration_ms

            if event.event_type == TelemetryEventType.ERROR:
                error_count += 1

        return {
            "total_events": total_events,
            "events_by_type": events_by_type,
            "total_duration_ms": total_duration,
            "average_duration_ms": (
                total_duration / total_events if total_events > 0 else 0
            ),
            "error_count": error_count,
            "error_rate": error_count / total_events if total_events > 0 else 0,
        }

    def clear_events(self):
        """Clear all logged events."""
        self.events.clear()


# Global telemetry logger instance
telemetry_logger = TelemetryLogger()


# Telemetry instrumentation decorator
def telemetry_instrumentation(operation_name: str):
    """Decorator for telemetry instrumentation."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                telemetry_logger.log_performance(operation_name, duration_ms)
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                telemetry_logger.log_error(operation_name, str(e))
                raise

        return wrapper

    return decorator
