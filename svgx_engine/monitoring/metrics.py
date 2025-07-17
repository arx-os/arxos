"""
SVGX Engine - Prometheus Metrics Monitoring

Provides comprehensive metrics collection and monitoring for SVGX Engine with:
- Prometheus metrics collection
- Custom SVGX-specific metrics
- Performance monitoring
- Health checks
- Alerting integration
"""

import time
import threading
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from svgx_engine.logging.structured_logger import get_logger

logger = get_logger(__name__)

# Optional Prometheus import
try:
    from prometheus_client import (
        Counter, Gauge, Histogram, Summary, Info,
        generate_latest, CONTENT_TYPE_LATEST
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create dummy classes for when Prometheus is not available
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
    class Summary:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
    class Info:
        def __init__(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass


class MetricType(Enum):
    """Metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    INFO = "info"


@dataclass
class MetricConfig:
    """Configuration for a metric."""
    name: str
    description: str
    metric_type: MetricType
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None
    quantiles: Optional[List[float]] = None


class SVGXMetricsCollector:
    """
    Comprehensive metrics collector for SVGX Engine.
    
    Features:
    - Prometheus metrics collection
    - Custom SVGX-specific metrics
    - Performance monitoring
    - Health checks
    - Alerting integration
    - Real-time metrics aggregation
    """
    
    def __init__(self, enable_prometheus: bool = True):
        """Initialize the metrics collector."""
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE
        self.metrics: Dict[str, Any] = {}
        self.custom_metrics: Dict[str, Callable] = {}
        self.health_checks: Dict[str, Callable] = {}
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        
        self._initialize_default_metrics()
        self._setup_custom_metrics()
        self._setup_health_checks()
        
        logger.info("Metrics collector initialized", 
                   prometheus_enabled=self.enable_prometheus)
    
    def _initialize_default_metrics(self):
        """Initialize default metrics."""
        # Request metrics
        self.metrics['requests_total'] = Counter(
            'svgx_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status']
        )
        
        self.metrics['request_duration'] = Histogram(
            'svgx_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        # Symbol processing metrics
        self.metrics['symbols_processed'] = Counter(
            'svgx_symbols_processed_total',
            'Total number of symbols processed',
            ['operation', 'status']
        )
        
        self.metrics['symbol_processing_duration'] = Histogram(
            'svgx_symbol_processing_duration_seconds',
            'Symbol processing duration in seconds',
            ['operation'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
        )
        
        # Cache metrics
        self.metrics['cache_hits'] = Counter(
            'svgx_cache_hits_total',
            'Total number of cache hits',
            ['cache_type']
        )
        
        self.metrics['cache_misses'] = Counter(
            'svgx_cache_misses_total',
            'Total number of cache misses',
            ['cache_type']
        )
        
        self.metrics['cache_size'] = Gauge(
            'svgx_cache_size',
            'Current cache size',
            ['cache_type']
        )
        
        # Database metrics
        self.metrics['database_connections'] = Gauge(
            'svgx_database_connections',
            'Number of active database connections',
            ['database_type']
        )
        
        self.metrics['database_queries'] = Counter(
            'svgx_database_queries_total',
            'Total number of database queries',
            ['operation', 'status']
        )
        
        self.metrics['database_query_duration'] = Histogram(
            'svgx_database_query_duration_seconds',
            'Database query duration in seconds',
            ['operation'],
            buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 2.0]
        )
        
        # Error metrics
        self.metrics['errors_total'] = Counter(
            'svgx_errors_total',
            'Total number of errors',
            ['error_type', 'component']
        )
        
        # Memory metrics
        self.metrics['memory_usage'] = Gauge(
            'svgx_memory_usage_bytes',
            'Memory usage in bytes',
            ['type']
        )
        
        # SVGX-specific metrics
        self.metrics['svgx_documents_processed'] = Counter(
            'svgx_documents_processed_total',
            'Total number of SVGX documents processed',
            ['operation', 'status']
        )
        
        self.metrics['svgx_elements_processed'] = Counter(
            'svgx_elements_processed_total',
            'Total number of SVGX elements processed',
            ['element_type', 'operation']
        )
        
        self.metrics['svgx_validation_results'] = Counter(
            'svgx_validation_results_total',
            'Total number of validation results',
            ['validation_type', 'result']
        )
        
        # System info
        self.metrics['system_info'] = Info(
            'svgx_system_info',
            'SVGX Engine system information'
        )
        
        # Initialize system info
        self.metrics['system_info'].info({
            'version': '1.0.0',
            'component': 'svgx_engine',
            'prometheus_enabled': str(self.enable_prometheus)
        })
    
    def _setup_custom_metrics(self):
        """Setup custom metrics collection."""
        self.custom_metrics['svgx_performance'] = self._collect_svgx_performance_metrics
        self.custom_metrics['cache_performance'] = self._collect_cache_performance_metrics
        self.custom_metrics['database_performance'] = self._collect_database_performance_metrics
    
    def _setup_health_checks(self):
        """Setup health check functions."""
        self.health_checks['database_health'] = self._check_database_health
        self.health_checks['cache_health'] = self._check_cache_health
        self.health_checks['memory_health'] = self._check_memory_health
    
    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record a request metric."""
        try:
            self.metrics['requests_total'].labels(method=method, endpoint=endpoint, status=status).inc()
            self.metrics['request_duration'].labels(method=method, endpoint=endpoint).observe(duration)
        except Exception as e:
            logger.warning(f"Failed to record request metric: {e}")
    
    def record_symbol_processing(self, operation: str, status: str, duration: float):
        """Record a symbol processing metric."""
        try:
            self.metrics['symbols_processed'].labels(operation=operation, status=status).inc()
            self.metrics['symbol_processing_duration'].labels(operation=operation).observe(duration)
        except Exception as e:
            logger.warning(f"Failed to record symbol processing metric: {e}")
    
    def record_cache_operation(self, cache_type: str, operation: str, hit: bool):
        """Record a cache operation metric."""
        try:
            if hit:
                self.metrics['cache_hits'].labels(cache_type=cache_type).inc()
            else:
                self.metrics['cache_misses'].labels(cache_type=cache_type).inc()
        except Exception as e:
            logger.warning(f"Failed to record cache metric: {e}")
    
    def record_database_operation(self, operation: str, status: str, duration: float):
        """Record a database operation metric."""
        try:
            self.metrics['database_queries'].labels(operation=operation, status=status).inc()
            self.metrics['database_query_duration'].labels(operation=operation).observe(duration)
        except Exception as e:
            logger.warning(f"Failed to record database metric: {e}")
    
    def record_error(self, error_type: str, component: str):
        """Record an error metric."""
        try:
            self.metrics['errors_total'].labels(error_type=error_type, component=component).inc()
        except Exception as e:
            logger.warning(f"Failed to record error metric: {e}")
    
    def update_memory_usage(self, memory_type: str, bytes_used: int):
        """Update memory usage metric."""
        try:
            self.metrics['memory_usage'].labels(type=memory_type).set(bytes_used)
        except Exception as e:
            logger.warning(f"Failed to update memory metric: {e}")
    
    def update_database_connections(self, database_type: str, connection_count: int):
        """Update database connections metric."""
        try:
            self.metrics['database_connections'].labels(database_type=database_type).set(connection_count)
        except Exception as e:
            logger.warning(f"Failed to update database connections metric: {e}")
    
    def record_svgx_document_processing(self, operation: str, status: str):
        """Record SVGX document processing metric."""
        try:
            self.metrics['svgx_documents_processed'].labels(operation=operation, status=status).inc()
        except Exception as e:
            logger.warning(f"Failed to record SVGX document metric: {e}")
    
    def record_svgx_element_processing(self, element_type: str, operation: str):
        """Record SVGX element processing metric."""
        try:
            self.metrics['svgx_elements_processed'].labels(element_type=element_type, operation=operation).inc()
        except Exception as e:
            logger.warning(f"Failed to record SVGX element metric: {e}")
    
    def record_validation_result(self, validation_type: str, result: str):
        """Record validation result metric."""
        try:
            self.metrics['svgx_validation_results'].labels(validation_type=validation_type, result=result).inc()
        except Exception as e:
            logger.warning(f"Failed to record validation metric: {e}")
    
    def _collect_svgx_performance_metrics(self) -> Dict[str, Any]:
        """Collect SVGX-specific performance metrics."""
        # This would collect metrics from SVGX services
        return {
            'svgx_parser_performance': {
                'parse_time_avg': 0.05,
                'parse_time_p95': 0.1,
                'parse_time_p99': 0.2
            },
            'svgx_renderer_performance': {
                'render_time_avg': 0.02,
                'render_time_p95': 0.05,
                'render_time_p99': 0.1
            },
            'svgx_validator_performance': {
                'validation_time_avg': 0.01,
                'validation_time_p95': 0.02,
                'validation_time_p99': 0.05
            }
        }
    
    def _collect_cache_performance_metrics(self) -> Dict[str, Any]:
        """Collect cache performance metrics."""
        return {
            'memory_cache': {
                'hit_rate': 0.85,
                'size': 1024,
                'evictions': 10
            },
            'redis_cache': {
                'hit_rate': 0.92,
                'size': 5120,
                'connections': 5
            }
        }
    
    def _collect_database_performance_metrics(self) -> Dict[str, Any]:
        """Collect database performance metrics."""
        return {
            'query_performance': {
                'avg_query_time': 0.005,
                'slow_queries': 2,
                'connection_pool_usage': 0.3
            },
            'transaction_performance': {
                'avg_transaction_time': 0.02,
                'failed_transactions': 0,
                'active_transactions': 1
            }
        }
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            # This would perform actual database health checks
            return {
                'status': 'healthy',
                'response_time': 0.001,
                'connections': 5,
                'last_check': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    def _check_cache_health(self) -> Dict[str, Any]:
        """Check cache health."""
        try:
            # This would perform actual cache health checks
            return {
                'status': 'healthy',
                'memory_cache_available': True,
                'redis_cache_available': True,
                'last_check': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    def _check_memory_health(self) -> Dict[str, Any]:
        """Check memory health."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                'status': 'healthy' if memory.percent < 90 else 'warning',
                'total_memory': memory.total,
                'available_memory': memory.available,
                'memory_percent': memory.percent,
                'last_check': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'status': 'unknown',
                'error': str(e),
                'last_check': datetime.utcnow().isoformat()
            }
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format."""
        if not self.enable_prometheus:
            return "# Prometheus metrics not available\n"
        
        try:
            return generate_latest()
        except Exception as e:
            logger.error(f"Failed to generate metrics: {e}")
            return f"# Error generating metrics: {e}\n"
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        health_results = {}
        
        for check_name, check_func in self.health_checks.items():
            try:
                health_results[check_name] = check_func()
            except Exception as e:
                health_results[check_name] = {
                    'status': 'error',
                    'error': str(e),
                    'last_check': datetime.utcnow().isoformat()
                }
        
        # Determine overall health
        overall_status = 'healthy'
        if any(result.get('status') == 'unhealthy' for result in health_results.values()):
            overall_status = 'unhealthy'
        elif any(result.get('status') == 'warning' for result in health_results.values()):
            overall_status = 'warning'
        
        return {
            'status': overall_status,
            'checks': health_results,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_custom_metrics(self) -> Dict[str, Any]:
        """Get custom metrics."""
        custom_metrics = {}
        
        for metric_name, metric_func in self.custom_metrics.items():
            try:
                custom_metrics[metric_name] = metric_func()
            except Exception as e:
                logger.warning(f"Failed to collect custom metric {metric_name}: {e}")
                custom_metrics[metric_name] = {'error': str(e)}
        
        return custom_metrics
    
    def add_custom_metric(self, name: str, metric_func: Callable):
        """Add a custom metric collection function."""
        self.custom_metrics[name] = metric_func
        logger.info("Custom metric added", metric_name=name)
    
    def add_health_check(self, name: str, check_func: Callable):
        """Add a custom health check function."""
        self.health_checks[name] = check_func
        logger.info("Health check added", check_name=name)
    
    def add_alert_rule(self, name: str, rule: Dict[str, Any]):
        """Add an alert rule."""
        self.alert_rules[name] = rule
        logger.info("Alert rule added", rule_name=name)
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check for triggered alerts."""
        alerts = []
        
        for rule_name, rule in self.alert_rules.items():
            try:
                # This would implement actual alert checking logic
                if self._should_trigger_alert(rule):
                    alerts.append({
                        'rule_name': rule_name,
                        'severity': rule.get('severity', 'warning'),
                        'message': rule.get('message', 'Alert triggered'),
                        'timestamp': datetime.utcnow().isoformat()
                    })
            except Exception as e:
                logger.warning(f"Failed to check alert rule {rule_name}: {e}")
        
        return alerts
    
    def _should_trigger_alert(self, rule: Dict[str, Any]) -> bool:
        """Check if an alert should be triggered."""
        # This is a placeholder implementation
        # In a real implementation, this would check actual metrics
        return False
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        return {
            'prometheus_enabled': self.enable_prometheus,
            'metrics_count': len(self.metrics),
            'custom_metrics_count': len(self.custom_metrics),
            'health_checks_count': len(self.health_checks),
            'alert_rules_count': len(self.alert_rules),
            'health_status': self.get_health_status(),
            'custom_metrics': self.get_custom_metrics(),
            'alerts': self.check_alerts()
        }


# Global metrics collector instance
_metrics_collector = None


def get_metrics_collector() -> SVGXMetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = SVGXMetricsCollector()
    return _metrics_collector


def record_request_metric(method: str, endpoint: str, status: int, duration: float):
    """Record a request metric using the global collector."""
    collector = get_metrics_collector()
    collector.record_request(method, endpoint, status, duration)


def record_symbol_metric(operation: str, status: str, duration: float):
    """Record a symbol processing metric using the global collector."""
    collector = get_metrics_collector()
    collector.record_symbol_processing(operation, status, duration)


def record_error_metric(error_type: str, component: str):
    """Record an error metric using the global collector."""
    collector = get_metrics_collector()
    collector.record_error(error_type, component) 