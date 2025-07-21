import time
import threading
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    """
    External metrics collector for SVGX Engine performance and usage tracking.
    Supports Prometheus-style metrics with counters, gauges, histograms, and custom metrics.
    """
    
    def __init__(self):
        self.counters = defaultdict(int)  # metric_name -> value
        self.gauges = defaultdict(float)  # metric_name -> value
        self.histograms = defaultdict(list)  # metric_name -> list of values
        self.custom_metrics = defaultdict(dict)  # metric_name -> custom data
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        # Initialize default metrics
        self._init_default_metrics()
    
    def _init_default_metrics(self):
        """Initialize default system metrics."""
        self.record_counter("svgx_engine_startups", 1)
        self.record_gauge("svgx_engine_uptime_seconds", 0)
        self.record_gauge("active_sessions", 0)
        self.record_gauge("active_canvases", 0)
        self.record_gauge("total_objects", 0)
    
    def record_counter(self, metric_name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Record a counter metric (monotonically increasing)."""
        with self.lock:
            key = self._build_metric_key(metric_name, labels)
            self.counters[key] += value
            logger.debug(f"Counter metric recorded: {key} = {self.counters[key]}")
    
    def record_gauge(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a gauge metric (can increase or decrease)."""
        with self.lock:
            key = self._build_metric_key(metric_name, labels)
            self.gauges[key] = value
            logger.debug(f"Gauge metric recorded: {key} = {value}")
    
    def record_histogram(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram metric (distribution of values)."""
        with self.lock:
            key = self._build_metric_key(metric_name, labels)
            self.histograms[key].append(value)
            # Keep only last 1000 values to prevent memory issues
            if len(self.histograms[key]) > 1000:
                self.histograms[key] = self.histograms[key][-1000:]
            logger.debug(f"Histogram metric recorded: {key} = {value}")
    
    def record_custom_metric(self, metric_name: str, data: Dict[str, Any], labels: Optional[Dict[str, str]] = None):
        """Record a custom metric with arbitrary data."""
        with self.lock:
            key = self._build_metric_key(metric_name, labels)
            self.custom_metrics[key] = {
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.debug(f"Custom metric recorded: {key}")
    
    def _build_metric_key(self, metric_name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Build a metric key with optional labels."""
        if not labels:
            return metric_name
        label_str = ",".join([f"{k}={v}" for k, v in sorted(labels.items())])
        return f"{metric_name}{{{label_str}}}"
    
    def record_ui_event(self, event_type: str, processing_time_ms: float, success: bool, 
                       canvas_id: Optional[str] = None, user_id: Optional[str] = None):
        """Record UI event metrics."""
        labels = {"event_type": event_type}
        if canvas_id:
            labels["canvas_id"] = canvas_id
        if user_id:
            labels["user_id"] = user_id
        
        # Record event counter
        self.record_counter("ui_events_total", 1, labels)
        
        # Record success/failure
        status = "success" if success else "error"
        self.record_counter("ui_events_by_status", 1, {**labels, "status": status})
        
        # Record processing time histogram
        self.record_histogram("ui_event_processing_time_ms", processing_time_ms, labels)
        
        # Record event type distribution
        self.record_counter("ui_events_by_type", 1, {"event_type": event_type})
    
    def record_performance_metric(self, operation: str, duration_ms: float, 
                                success: bool, additional_labels: Optional[Dict[str, str]] = None):
        """Record performance metrics for operations."""
        labels = {"operation": operation}
        if additional_labels:
            labels.update(additional_labels)
        
        # Record operation counter
        self.record_counter("operations_total", 1, labels)
        
        # Record success/failure
        status = "success" if success else "error"
        self.record_counter("operations_by_status", 1, {**labels, "status": status})
        
        # Record duration histogram
        self.record_histogram("operation_duration_ms", duration_ms, labels)
    
    def record_system_health(self, component: str, status: str, details: Optional[Dict[str, Any]] = None):
        """Record system health metrics."""
        labels = {"component": component}
        
        # Record health status
        self.record_gauge("system_health_status", 1 if status == "healthy" else 0, labels)
        
        # Record custom health details
        if details:
            self.record_custom_metric("system_health_details", details, labels)
    
    def record_collaboration_metric(self, action: str, canvas_id: str, user_id: str, 
                                  object_id: Optional[str] = None):
        """Record collaboration metrics (locks, conflicts, etc.)."""
        labels = {"action": action, "canvas_id": canvas_id, "user_id": user_id}
        if object_id:
            labels["object_id"] = object_id
        
        self.record_counter("collaboration_actions_total", 1, labels)
        self.record_counter("collaboration_actions_by_type", 1, {"action": action})
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all collected metrics."""
        with self.lock:
            # Update uptime
            uptime = time.time() - self.start_time
            self.gauges["svgx_engine_uptime_seconds"] = uptime
            
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {
                    name: {
                        "count": len(values),
                        "sum": sum(values),
                        "min": min(values) if values else 0,
                        "max": max(values) if values else 0,
                        "avg": sum(values) / len(values) if values else 0,
                        "p95": self._percentile(values, 95),
                        "p99": self._percentile(values, 99)
                    }
                    for name, values in self.histograms.items()
                },
                "custom_metrics": dict(self.custom_metrics),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format."""
        with self.lock:
            lines = []
            
            # Export counters
            for name, value in self.counters.items():
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {value}")
            
            # Export gauges
            for name, value in self.gauges.items():
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {value}")
            
            # Export histograms
            for name, values in self.histograms.items():
                if values:
                    lines.append(f"# TYPE {name} histogram")
                    lines.append(f"{name}_count {len(values)}")
                    lines.append(f"{name}_sum {sum(values)}")
                    lines.append(f"{name}_min {min(values)}")
                    lines.append(f"{name}_max {max(values)}")
                    lines.append(f"{name}_avg {sum(values) / len(values)}")
            
            return "\n".join(lines)
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)."""
        with self.lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.custom_metrics.clear()
            self._init_default_metrics()

# Global metrics collector instance
metrics_collector = MetricsCollector() 