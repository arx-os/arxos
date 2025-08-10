"""
Advanced Performance Monitoring and Metrics Collection.

Provides comprehensive performance monitoring, metrics collection, 
and alerting capabilities for system optimization.
"""

import time
import psutil
import threading
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from contextlib import contextmanager
from enum import Enum
import statistics
import json

from infrastructure.logging.structured_logging import get_logger, performance_logger


logger = get_logger(__name__)


class MetricType(Enum):
    """Types of performance metrics."""
    COUNTER = "counter"           # Monotonically increasing values
    GAUGE = "gauge"              # Point-in-time values that can go up/down
    HISTOGRAM = "histogram"      # Distribution of values
    TIMER = "timer"              # Duration measurements
    RATE = "rate"                # Rate of change over time


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "tags": self.tags
        }


@dataclass
class PerformanceThreshold:
    """Performance threshold configuration."""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison_operator: str = ">"  # >, <, >=, <=, ==, !=
    evaluation_window: int = 300   # seconds
    min_samples: int = 5
    
    def evaluate(self, values: List[float]) -> Optional[AlertSeverity]:
        """Evaluate threshold against values."""
        if len(values) < self.min_samples:
            return None
        
        # Use different aggregations based on metric type
        avg_value = statistics.mean(values)
        
        if self.comparison_operator == ">":
            if avg_value > self.critical_threshold:
                return AlertSeverity.CRITICAL
            elif avg_value > self.warning_threshold:
                return AlertSeverity.HIGH
        elif self.comparison_operator == "<":
            if avg_value < self.critical_threshold:
                return AlertSeverity.CRITICAL
            elif avg_value < self.warning_threshold:
                return AlertSeverity.HIGH
        # Add other operators as needed
        
        return None


class MetricCollector:
    """Collects and stores performance metrics."""
    
    def __init__(self, max_points_per_metric: int = 10000):
        self.metrics = defaultdict(lambda: deque(maxlen=max_points_per_metric))
        self.metadata = {}
        self.lock = threading.RLock()
        
    def record_metric(self, name: str, value: float, 
                     metric_type: MetricType = MetricType.GAUGE,
                     tags: Optional[Dict[str, str]] = None) -> None:
        """Record a metric value."""
        with self.lock:
            point = MetricPoint(
                timestamp=datetime.now(timezone.utc),
                value=value,
                tags=tags or {}
            )
            
            self.metrics[name].append(point)
            self.metadata[name] = {
                "type": metric_type,
                "last_updated": point.timestamp,
                "point_count": len(self.metrics[name])
            }
    
    def increment_counter(self, name: str, increment: float = 1.0,
                         tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        with self.lock:
            current_value = 0.0
            if name in self.metrics and self.metrics[name]:
                current_value = self.metrics[name][-1].value
            
            self.record_metric(name, current_value + increment, 
                             MetricType.COUNTER, tags)
    
    def set_gauge(self, name: str, value: float,
                  tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value."""
        self.record_metric(name, value, MetricType.GAUGE, tags)
    
    def record_timer(self, name: str, duration: float,
                    tags: Optional[Dict[str, str]] = None) -> None:
        """Record a timer metric (duration in seconds)."""
        self.record_metric(name, duration, MetricType.TIMER, tags)
    
    def get_recent_values(self, name: str, window_seconds: int = 300) -> List[float]:
        """Get recent metric values within time window."""
        with self.lock:
            if name not in self.metrics:
                return []
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
            recent_points = [
                point for point in self.metrics[name]
                if point.timestamp >= cutoff_time
            ]
            
            return [point.value for point in recent_points]
    
    def get_metric_statistics(self, name: str, window_seconds: int = 300) -> Dict[str, Any]:
        """Get statistical summary of a metric."""
        values = self.get_recent_values(name, window_seconds)
        
        if not values:
            return {"count": 0}
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "p95": self._percentile(values, 95),
            "p99": self._percentile(values, 99)
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_all_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        with self.lock:
            summary = {}
            for name, points in self.metrics.items():
                if points:
                    latest_point = points[-1]
                    summary[name] = {
                        "latest_value": latest_point.value,
                        "latest_timestamp": latest_point.timestamp.isoformat(),
                        "type": self.metadata.get(name, {}).get("type", "unknown"),
                        "point_count": len(points)
                    }
            return summary


class SystemResourceMonitor:
    """Monitors system resources (CPU, memory, disk, network)."""
    
    def __init__(self, collector: MetricCollector):
        self.collector = collector
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_interval = 30  # seconds
        
    def start_monitoring(self) -> None:
        """Start system resource monitoring."""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True
            )
            self.monitor_thread.start()
            logger.info("System resource monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop system resource monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("System resource monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring:
            try:
                self._collect_system_metrics()
                time.sleep(self.monitor_interval)
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                time.sleep(self.monitor_interval)
    
    def _collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        self.collector.set_gauge("system.cpu.usage_percent", cpu_percent)
        
        cpu_count = psutil.cpu_count()
        self.collector.set_gauge("system.cpu.count", cpu_count)
        
        load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
        self.collector.set_gauge("system.cpu.load_1m", load_avg[0])
        self.collector.set_gauge("system.cpu.load_5m", load_avg[1])
        self.collector.set_gauge("system.cpu.load_15m", load_avg[2])
        
        # Memory metrics
        memory = psutil.virtual_memory()
        self.collector.set_gauge("system.memory.total_bytes", memory.total)
        self.collector.set_gauge("system.memory.available_bytes", memory.available)
        self.collector.set_gauge("system.memory.used_bytes", memory.used)
        self.collector.set_gauge("system.memory.usage_percent", memory.percent)
        
        # Swap metrics
        swap = psutil.swap_memory()
        self.collector.set_gauge("system.swap.total_bytes", swap.total)
        self.collector.set_gauge("system.swap.used_bytes", swap.used)
        self.collector.set_gauge("system.swap.usage_percent", swap.percent)
        
        # Disk metrics
        try:
            disk_usage = psutil.disk_usage('/')
            self.collector.set_gauge("system.disk.total_bytes", disk_usage.total)
            self.collector.set_gauge("system.disk.used_bytes", disk_usage.used)
            self.collector.set_gauge("system.disk.free_bytes", disk_usage.free)
            self.collector.set_gauge("system.disk.usage_percent", 
                                   (disk_usage.used / disk_usage.total) * 100)
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                self.collector.set_gauge("system.disk.read_bytes", disk_io.read_bytes)
                self.collector.set_gauge("system.disk.write_bytes", disk_io.write_bytes)
                self.collector.set_gauge("system.disk.read_count", disk_io.read_count)
                self.collector.set_gauge("system.disk.write_count", disk_io.write_count)
        except Exception as e:
            logger.warning(f"Could not collect disk metrics: {e}")
        
        # Network metrics
        try:
            network_io = psutil.net_io_counters()
            if network_io:
                self.collector.set_gauge("system.network.bytes_sent", network_io.bytes_sent)
                self.collector.set_gauge("system.network.bytes_recv", network_io.bytes_recv)
                self.collector.set_gauge("system.network.packets_sent", network_io.packets_sent)
                self.collector.set_gauge("system.network.packets_recv", network_io.packets_recv)
        except Exception as e:
            logger.warning(f"Could not collect network metrics: {e}")
        
        # Process-specific metrics
        try:
            process = psutil.Process()
            self.collector.set_gauge("process.cpu_percent", process.cpu_percent())
            
            memory_info = process.memory_info()
            self.collector.set_gauge("process.memory.rss_bytes", memory_info.rss)
            self.collector.set_gauge("process.memory.vms_bytes", memory_info.vms)
            
            # File descriptors (Unix only)
            if hasattr(process, 'num_fds'):
                self.collector.set_gauge("process.file_descriptors", process.num_fds())
            
            # Thread count
            self.collector.set_gauge("process.threads", process.num_threads())
            
        except Exception as e:
            logger.warning(f"Could not collect process metrics: {e}")


class DatabasePerformanceMonitor:
    """Monitors database performance metrics."""
    
    def __init__(self, collector: MetricCollector):
        self.collector = collector
        self.connection_pool_stats = {}
        self.query_stats = defaultdict(list)
        
    def record_query_performance(self, query_type: str, duration: float,
                                rows_examined: int = 0, rows_returned: int = 0,
                                table_name: str = None) -> None:
        """Record database query performance."""
        tags = {"query_type": query_type}
        if table_name:
            tags["table"] = table_name
        
        self.collector.record_timer("database.query.duration_seconds", duration, tags)
        self.collector.set_gauge("database.query.rows_examined", rows_examined, tags)
        self.collector.set_gauge("database.query.rows_returned", rows_returned, tags)
        
        # Calculate query efficiency ratio
        if rows_examined > 0:
            efficiency = rows_returned / rows_examined
            self.collector.set_gauge("database.query.efficiency_ratio", efficiency, tags)
        
        # Track slow queries
        if duration > 1.0:  # Slow query threshold
            self.collector.increment_counter("database.slow_queries_total", 1.0, tags)
    
    def record_connection_pool_stats(self, pool_name: str, size: int, 
                                   checked_out: int, overflow: int, invalid: int) -> None:
        """Record connection pool statistics."""
        tags = {"pool": pool_name}
        
        self.collector.set_gauge("database.pool.size", size, tags)
        self.collector.set_gauge("database.pool.checked_out", checked_out, tags)
        self.collector.set_gauge("database.pool.overflow", overflow, tags)
        self.collector.set_gauge("database.pool.invalid", invalid, tags)
        
        # Calculate utilization
        utilization = (checked_out / size) * 100 if size > 0 else 0
        self.collector.set_gauge("database.pool.utilization_percent", utilization, tags)


class ApplicationPerformanceMonitor:
    """Monitors application-specific performance metrics."""
    
    def __init__(self, collector: MetricCollector):
        self.collector = collector
        
    def record_request_performance(self, endpoint: str, method: str, 
                                 status_code: int, duration: float,
                                 user_id: str = None) -> None:
        """Record HTTP request performance."""
        tags = {
            "endpoint": endpoint,
            "method": method,
            "status_code": str(status_code)
        }
        
        self.collector.record_timer("http.request.duration_seconds", duration, tags)
        self.collector.increment_counter("http.requests_total", 1.0, tags)
        
        # Track error rates
        if status_code >= 400:
            self.collector.increment_counter("http.errors_total", 1.0, tags)
    
    def record_cache_performance(self, operation: str, hit: bool, 
                               duration: float, key_pattern: str = None) -> None:
        """Record cache performance metrics."""
        tags = {
            "operation": operation,
            "result": "hit" if hit else "miss"
        }
        if key_pattern:
            tags["key_pattern"] = key_pattern
        
        self.collector.record_timer("cache.operation.duration_seconds", duration, tags)
        self.collector.increment_counter("cache.operations_total", 1.0, tags)
        
        if hit:
            self.collector.increment_counter("cache.hits_total", 1.0, tags)
        else:
            self.collector.increment_counter("cache.misses_total", 1.0, tags)
    
    def record_business_metric(self, metric_name: str, value: float,
                             tags: Optional[Dict[str, str]] = None) -> None:
        """Record business-specific metrics."""
        business_tags = {"category": "business"}
        if tags:
            business_tags.update(tags)
        
        self.collector.set_gauge(f"business.{metric_name}", value, business_tags)


class AlertManager:
    """Manages performance alerts and notifications."""
    
    def __init__(self, collector: MetricCollector):
        self.collector = collector
        self.thresholds = {}
        self.active_alerts = {}
        self.alert_callbacks = []
        
    def add_threshold(self, threshold: PerformanceThreshold) -> None:
        """Add performance threshold for monitoring."""
        self.thresholds[threshold.metric_name] = threshold
        logger.info(f"Added performance threshold for {threshold.metric_name}")
    
    def add_alert_callback(self, callback: Callable[[str, AlertSeverity, Dict], None]) -> None:
        """Add callback function for alert notifications."""
        self.alert_callbacks.append(callback)
    
    def check_thresholds(self) -> List[Dict[str, Any]]:
        """Check all thresholds and trigger alerts."""
        alerts = []
        
        for metric_name, threshold in self.thresholds.items():
            values = self.collector.get_recent_values(
                metric_name, 
                threshold.evaluation_window
            )
            
            severity = threshold.evaluate(values)
            
            if severity:
                alert_key = f"{metric_name}_{severity.value}"
                
                # Only trigger new alerts or escalations
                if alert_key not in self.active_alerts:
                    alert_info = {
                        "metric_name": metric_name,
                        "severity": severity,
                        "current_value": statistics.mean(values) if values else 0,
                        "threshold": threshold,
                        "timestamp": datetime.now(timezone.utc)
                    }
                    
                    self.active_alerts[alert_key] = alert_info
                    alerts.append(alert_info)
                    
                    # Trigger callbacks
                    for callback in self.alert_callbacks:
                        try:
                            callback(metric_name, severity, alert_info)
                        except Exception as e:
                            logger.error(f"Alert callback failed: {e}")
            else:
                # Clear resolved alerts
                resolved_keys = [
                    key for key in self.active_alerts.keys()
                    if key.startswith(f"{metric_name}_")
                ]
                for key in resolved_keys:
                    del self.active_alerts[key]
        
        return alerts
    
    def get_active_alerts(self) -> Dict[str, Any]:
        """Get currently active alerts."""
        return self.active_alerts.copy()


class PerformanceMonitor:
    """Main performance monitoring system."""
    
    def __init__(self):
        self.collector = MetricCollector()
        self.system_monitor = SystemResourceMonitor(self.collector)
        self.db_monitor = DatabasePerformanceMonitor(self.collector)
        self.app_monitor = ApplicationPerformanceMonitor(self.collector)
        self.alert_manager = AlertManager(self.collector)
        
        self.monitoring_active = False
        self.alert_check_thread = None
        
        # Set up default thresholds
        self._setup_default_thresholds()
    
    def _setup_default_thresholds(self) -> None:
        """Set up default performance thresholds."""
        thresholds = [
            PerformanceThreshold(
                metric_name="system.cpu.usage_percent",
                warning_threshold=70.0,
                critical_threshold=90.0,
                comparison_operator=">"
            ),
            PerformanceThreshold(
                metric_name="system.memory.usage_percent",
                warning_threshold=80.0,
                critical_threshold=95.0,
                comparison_operator=">"
            ),
            PerformanceThreshold(
                metric_name="system.disk.usage_percent",
                warning_threshold=85.0,
                critical_threshold=95.0,
                comparison_operator=">"
            ),
            PerformanceThreshold(
                metric_name="database.query.duration_seconds",
                warning_threshold=1.0,
                critical_threshold=5.0,
                comparison_operator=">"
            ),
            PerformanceThreshold(
                metric_name="http.request.duration_seconds",
                warning_threshold=2.0,
                critical_threshold=10.0,
                comparison_operator=">"
            )
        ]
        
        for threshold in thresholds:
            self.alert_manager.add_threshold(threshold)
    
    def start_monitoring(self) -> None:
        """Start all performance monitoring."""
        if not self.monitoring_active:
            self.monitoring_active = True
            
            # Start system resource monitoring
            self.system_monitor.start_monitoring()
            
            # Start alert checking
            self._start_alert_checking()
            
            logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop all performance monitoring."""
        self.monitoring_active = False
        
        # Stop system monitoring
        self.system_monitor.stop_monitoring()
        
        # Stop alert checking
        if self.alert_check_thread:
            self.alert_check_thread.join(timeout=5)
        
        logger.info("Performance monitoring stopped")
    
    def _start_alert_checking(self) -> None:
        """Start alert checking thread."""
        self.alert_check_thread = threading.Thread(
            target=self._alert_check_loop,
            daemon=True
        )
        self.alert_check_thread.start()
    
    def _alert_check_loop(self) -> None:
        """Main alert checking loop."""
        while self.monitoring_active:
            try:
                self.alert_manager.check_thresholds()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in alert checking: {e}")
                time.sleep(60)
    
    @contextmanager
    def measure_operation(self, operation_name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager to measure operation duration."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.collector.record_timer(f"operation.{operation_name}.duration_seconds", 
                                      duration, tags)
    
    def record_custom_metric(self, name: str, value: float, 
                           metric_type: MetricType = MetricType.GAUGE,
                           tags: Optional[Dict[str, str]] = None) -> None:
        """Record a custom performance metric."""
        self.collector.record_metric(name, value, metric_type, tags)
    
    def get_performance_report(self, include_system: bool = True,
                             include_database: bool = True,
                             include_application: bool = True) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "monitoring_active": self.monitoring_active
        }
        
        if include_system:
            report["system_metrics"] = {
                name: self.collector.get_metric_statistics(name)
                for name in self.collector.metrics.keys()
                if name.startswith("system.")
            }
        
        if include_database:
            report["database_metrics"] = {
                name: self.collector.get_metric_statistics(name)
                for name in self.collector.metrics.keys()
                if name.startswith("database.")
            }
        
        if include_application:
            report["application_metrics"] = {
                name: self.collector.get_metric_statistics(name)
                for name in self.collector.metrics.keys()
                if name.startswith(("http.", "cache.", "business."))
            }
        
        report["active_alerts"] = self.alert_manager.get_active_alerts()
        report["metrics_summary"] = self.collector.get_all_metrics_summary()
        
        return report


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_performance(operation_name: str, tags: Optional[Dict[str, str]] = None):
    """Decorator to automatically monitor function performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with performance_monitor.measure_operation(operation_name, tags):
                return func(*args, **kwargs)
        return wrapper
    return decorator