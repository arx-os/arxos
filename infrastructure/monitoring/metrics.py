"""
Metrics Collector

This module provides metrics collection functionality for the infrastructure layer.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from datetime import datetime
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Metrics collector for gathering system metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.start_time = datetime.utcnow()
    
    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter metric."""
        self.counters[name] += value
        logger.debug(f"Incremented counter {name} by {value}")
    
    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge metric."""
        self.gauges[name] = value
        logger.debug(f"Set gauge {name} to {value}")
    
    def record_histogram(self, name: str, value: float) -> None:
        """Record a histogram metric."""
        self.histograms[name].append(value)
        logger.debug(f"Recorded histogram {name}: {value}")
    
    def start_timer(self, name: str) -> float:
        """Start a timer and return the start time."""
        start_time = time.time()
        logger.debug(f"Started timer {name}")
        return start_time
    
    def stop_timer(self, name: str, start_time: float) -> float:
        """Stop a timer and record the duration."""
        duration = time.time() - start_time
        self.timers[name].append(duration)
        logger.debug(f"Stopped timer {name}: {duration:.3f}s")
        return duration
    
    def get_counter(self, name: str) -> int:
        """Get a counter value."""
        return self.counters.get(name, 0)
    
    def get_gauge(self, name: str) -> Optional[float]:
        """Get a gauge value."""
        return self.gauges.get(name)
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics."""
        values = self.histograms.get(name, [])
        if not values:
            return {}
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "sum": sum(values)
        }
    
    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """Get timer statistics."""
        values = self.timers.get(name, [])
        if not values:
            return {}
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "sum": sum(values)
        }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                name: self.get_histogram_stats(name) 
                for name in self.histograms
            },
            "timers": {
                name: self.get_timer_stats(name) 
                for name in self.timers
            }
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.timers.clear()
        self.start_time = datetime.utcnow()
        logger.info("Reset all metrics")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on metrics collector."""
        return {
            "status": "healthy",
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "total_metrics": len(self.counters) + len(self.gauges) + len(self.histograms) + len(self.timers)
        } 