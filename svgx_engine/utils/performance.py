"""
SVGX Engine - Performance Monitor

This module provides performance monitoring utilities for SVGX Engine services.
"""

import time
import threading
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from datetime import datetime
from collections import defaultdict

from structlog import get_logger

logger = get_logger()


class PerformanceMonitor:
    """Performance monitoring utility for SVGX Engine."""

    def __init__(self):
        """Initialize the performance monitor."""
        self.metrics = defaultdict(list)
        self.active_operations = {}
        self.lock = threading.Lock()

    @contextmanager
    def monitor(self, operation_name: str):
        """
        Context manager for monitoring operation performance.

        Args:
            operation_name: Name of the operation to monitor
        """
        start_time = time.time()
        thread_id = threading.get_ident()

        try:
            with self.lock:
                self.active_operations[thread_id] = {
                    "operation": operation_name,
                    "start_time": start_time,
                }

            yield

        finally:
            end_time = time.time()
            duration = end_time - start_time

            with self.lock:
                if thread_id in self.active_operations:
                    del self.active_operations[thread_id]

                self.metrics[operation_name].append(
                    {
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration": duration,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            logger.debug(
                "Operation completed", operation=operation_name, duration=duration
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        with self.lock:
            result = {}

            for operation_name, measurements in self.metrics.items():
                if measurements:
                    durations = [m["duration"] for m in measurements]
                    result[operation_name] = {
                        "count": len(measurements),
                        "total_time": sum(durations),
                        "average_time": sum(durations) / len(durations),
                        "min_time": min(durations),
                        "max_time": max(durations),
                        "recent_measurements": measurements[
                            -10:
                        ],  # Last 10 measurements
                    }

            result["active_operations"] = len(self.active_operations)
            result["active_operation_details"] = [
                {
                    "operation": op["operation"],
                    "start_time": op["start_time"],
                    "elapsed": time.time() - op["start_time"],
                }
                for op in self.active_operations.values()
            ]

            return result

    def get_operation_metrics(self, operation_name: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific operation."""
        metrics = self.get_metrics()
        return metrics.get(operation_name)

    def record_operation(self, operation_name: str, duration: float):
        """
        Record an operation with its duration.

        Args:
            operation_name: Name of the operation
            duration: Duration in seconds
        """
        with self.lock:
            self.metrics[operation_name].append(
                {
                    "start_time": time.time() - duration,
                    "end_time": time.time(),
                    "duration": duration,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        logger.debug("Operation recorded", operation=operation_name, duration=duration)

    def clear_metrics(self):
        """Clear all performance metrics."""
        with self.lock:
            self.metrics.clear()
            self.active_operations.clear()

    def get_slow_operations(
        self, threshold_seconds: float = 1.0
    ) -> List[Dict[str, Any]]:
        """Get operations that took longer than the threshold."""
        slow_operations = []

        with self.lock:
            for operation_name, measurements in self.metrics.items():
                for measurement in measurements:
                    if measurement["duration"] > threshold_seconds:
                        slow_operations.append(
                            {
                                "operation": operation_name,
                                "duration": measurement["duration"],
                                "timestamp": measurement["timestamp"],
                            }
                        )

        return sorted(slow_operations, key=lambda x: x["duration"], reverse=True)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a comprehensive performance summary."""
        metrics = self.get_metrics()

        if not metrics:
            return {"message": "No performance data available"}

        # Calculate overall statistics
        all_durations = []
        for operation_data in metrics.values():
            if (
                isinstance(operation_data, dict)
                and "recent_measurements" in operation_data
            ):
                all_durations.extend(
                    [m["duration"] for m in operation_data["recent_measurements"]]
                )

        summary = {
            "total_operations": sum(
                data["count"]
                for data in metrics.values()
                if isinstance(data, dict) and "count" in data
            ),
            "total_time": sum(
                data["total_time"]
                for data in metrics.values()
                if isinstance(data, dict) and "total_time" in data
            ),
            "average_operation_time": (
                sum(all_durations) / len(all_durations) if all_durations else 0
            ),
            "slowest_operation": max(all_durations) if all_durations else 0,
            "fastest_operation": min(all_durations) if all_durations else 0,
            "active_operations": metrics.get("active_operations", 0),
            "operation_breakdown": {
                name: data
                for name, data in metrics.items()
                if isinstance(data, dict) and "count" in data
            },
        }

        return summary


# Global performance monitor instance
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def monitor_operation(operation_name: str):
    """Decorator for monitoring function performance."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            with monitor.monitor(operation_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def get_performance_report() -> Dict[str, Any]:
    """Get a comprehensive performance report."""
    monitor = get_performance_monitor()
    return monitor.get_performance_summary()


def clear_performance_data():
    """Clear all performance data."""
    monitor = get_performance_monitor()
    monitor.clear_metrics()
