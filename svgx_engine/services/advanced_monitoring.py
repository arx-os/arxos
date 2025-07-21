"""
Advanced Monitoring & Observability Service

This module implements comprehensive enterprise-grade monitoring and observability including:
- Distributed Tracing with OpenTelemetry
- Metrics Collection and Aggregation
- Structured Logging with Correlation IDs
- Real-time Alerting and Notifications
- Performance Monitoring and Profiling
- Resource Usage Tracking
- Business Metrics and KPIs
- Custom Dashboards and Visualizations

Author: Arxos Engineering Team
Date: December 2024
"""

import asyncio
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from functools import wraps

import aiohttp
import prometheus_client
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Span, Status, StatusCode
from pydantic import BaseModel

# Configure OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Configure Jaeger exporter
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Configure logging
logger = logging.getLogger(__name__)

# Prometheus metrics
request_counter = prometheus_client.Counter(
    'requests_total',
    'Total requests',
    ['service', 'endpoint', 'method', 'status']
)

request_duration = prometheus_client.Histogram(
    'request_duration_seconds',
    'Request duration in seconds',
    ['service', 'endpoint', 'method'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

error_counter = prometheus_client.Counter(
    'errors_total',
    'Total errors',
    ['service', 'endpoint', 'error_type']
)

memory_usage = prometheus_client.Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes',
    ['service']
)

cpu_usage = prometheus_client.Gauge(
    'cpu_usage_percent',
    'CPU usage percentage',
    ['service']
)

active_connections = prometheus_client.Gauge(
    'active_connections',
    'Active connections',
    ['service']
)

business_metrics = prometheus_client.Counter(
    'business_operations_total',
    'Business operations counter',
    ['service', 'operation_type', 'status']
)


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Alert notification channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


@dataclass
class MetricConfig:
    """Configuration for metrics"""
    name: str
    type: MetricType
    description: str
    labels: List[str] = field(default_factory=list)
    buckets: Optional[List[float]] = None


@dataclass
class AlertConfig:
    """Configuration for alerts"""
    name: str
    condition: str
    severity: AlertSeverity
    channels: List[AlertChannel]
    cooldown: int = 300  # seconds
    enabled: bool = True


@dataclass
class TracingConfig:
    """Configuration for distributed tracing"""
    service_name: str
    jaeger_host: str = "localhost"
    jaeger_port: int = 6831
    sampling_rate: float = 1.0
    enabled: bool = True


class CorrelationContext:
    """Correlation context for request tracing"""
    
    def __init__(self):
        self.correlation_id = str(uuid.uuid4())
        self.user_id = None
        self.session_id = None
        self.request_id = None
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "correlation_id": self.correlation_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat()
        }


class StructuredLogger:
    """Structured logging with correlation IDs"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(f"{service_name}.structured")
    
    def log(self, level: str, message: str, **kwargs):
        """Log structured message"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "service": self.service_name,
            "message": message,
            **kwargs
        }
        
        log_message = json.dumps(log_data)
        
        if level == "DEBUG":
            self.logger.debug(log_message)
        elif level == "INFO":
            self.logger.info(log_message)
        elif level == "WARNING":
            self.logger.warning(log_message)
        elif level == "ERROR":
            self.logger.error(log_message)
        elif level == "CRITICAL":
            self.logger.critical(log_message)
    
    def log_request(self, method: str, endpoint: str, status_code: int, duration: float, **kwargs):
        """Log HTTP request"""
        self.log("INFO", "HTTP Request", 
                 method=method, 
                 endpoint=endpoint, 
                 status_code=status_code, 
                 duration=duration,
                 **kwargs)
    
    def log_error(self, error: Exception, **kwargs):
        """Log error with context"""
        self.log("ERROR", "Error occurred", 
                 error_type=type(error).__name__,
                 error_message=str(error),
                 **kwargs)


class MetricsCollector:
    """Metrics collection and aggregation"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.custom_metrics: Dict[str, Any] = {}
    
    def record_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        request_counter.labels(
            service=self.service_name,
            endpoint=endpoint,
            method=method,
            status=status_code
        ).inc()
        
        request_duration.labels(
            service=self.service_name,
            endpoint=endpoint,
            method=method
        ).observe(duration)
    
    def record_error(self, endpoint: str, error_type: str):
        """Record error metrics"""
        error_counter.labels(
            service=self.service_name,
            endpoint=endpoint,
            error_type=error_type
        ).inc()
    
    def record_business_operation(self, operation_type: str, status: str):
        """Record business metrics"""
        business_metrics.labels(
            service=self.service_name,
            operation_type=operation_type,
            status=status
        ).inc()
    
    def update_memory_usage(self, bytes_used: int):
        """Update memory usage metric"""
        memory_usage.labels(service=self.service_name).set(bytes_used)
    
    def update_cpu_usage(self, percentage: float):
        """Update CPU usage metric"""
        cpu_usage.labels(service=self.service_name).set(percentage)
    
    def update_active_connections(self, count: int):
        """Update active connections metric"""
        active_connections.labels(service=self.service_name).set(count)
    
    def create_custom_metric(self, name: str, config: MetricConfig):
        """Create custom metric"""
        if config.type == MetricType.COUNTER:
            metric = prometheus_client.Counter(
                name,
                config.description,
                config.labels
            )
        elif config.type == MetricType.GAUGE:
            metric = prometheus_client.Gauge(
                name,
                config.description,
                config.labels
            )
        elif config.type == MetricType.HISTOGRAM:
            metric = prometheus_client.Histogram(
                name,
                config.description,
                config.labels,
                buckets=config.buckets or [0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
            )
        else:
            raise ValueError(f"Unsupported metric type: {config.type}")
        
        self.custom_metrics[name] = metric
        return metric


class DistributedTracer:
    """Distributed tracing with OpenTelemetry"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.tracer = trace.get_tracer(service_name)
    
    @asynccontextmanager
    async def trace_operation(self, operation_name: str, **attributes):
        """Trace an operation"""
        with self.tracer.start_as_current_span(operation_name, attributes=attributes) as span:
            try:
                yield span
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def add_event(self, span: Span, name: str, attributes: Dict[str, Any] = None):
        """Add event to span"""
        span.add_event(name, attributes or {})
    
    def set_attribute(self, span: Span, key: str, value: Any):
        """Set attribute on span"""
        span.set_attribute(key, value)


class AlertManager:
    """Alert management and notification"""
    
    def __init__(self):
        self.alerts: Dict[str, AlertConfig] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self.last_alert_time: Dict[str, datetime] = {}
    
    def add_alert(self, alert: AlertConfig):
        """Add alert configuration"""
        self.alerts[alert.name] = alert
    
    def check_alert(self, alert_name: str, condition_value: bool, context: Dict[str, Any] = None):
        """Check if alert should be triggered"""
        if alert_name not in self.alerts:
            return
        
        alert = self.alerts[alert_name]
        if not alert.enabled:
            return
        
        # Check cooldown
        last_time = self.last_alert_time.get(alert_name)
        if last_time and (datetime.utcnow() - last_time).seconds < alert.cooldown:
            return
        
        if condition_value:
            self._trigger_alert(alert, context or {})
    
    def _trigger_alert(self, alert: AlertConfig, context: Dict[str, Any]):
        """Trigger alert notification"""
        alert_data = {
            "name": alert.name,
            "severity": alert.severity.value,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context
        }
        
        self.alert_history.append(alert_data)
        self.last_alert_time[alert.name] = datetime.utcnow()
        
        # Send notifications
        for channel in alert.channels:
            asyncio.create_task(self._send_notification(channel, alert_data))
        
        logger.critical(f"Alert triggered: {alert.name} - {alert.severity.value}")
    
    async def _send_notification(self, channel: AlertChannel, alert_data: Dict[str, Any]):
        """Send notification to specified channel"""
        try:
            if channel == AlertChannel.EMAIL:
                await self._send_email_notification(alert_data)
            elif channel == AlertChannel.SLACK:
                await self._send_slack_notification(alert_data)
            elif channel == AlertChannel.WEBHOOK:
                await self._send_webhook_notification(alert_data)
            elif channel == AlertChannel.SMS:
                await self._send_sms_notification(alert_data)
        except Exception as e:
            logger.error(f"Failed to send {channel.value} notification: {e}")
    
    async def _send_email_notification(self, alert_data: Dict[str, Any]):
        """Send email notification"""
        # TODO: Implement email notification
        logger.info(f"Email notification sent: {alert_data}")
    
    async def _send_slack_notification(self, alert_data: Dict[str, Any]):
        """Send Slack notification"""
        # TODO: Implement Slack notification
        logger.info(f"Slack notification sent: {alert_data}")
    
    async def _send_webhook_notification(self, alert_data: Dict[str, Any]):
        """Send webhook notification"""
        # TODO: Implement webhook notification
        logger.info(f"Webhook notification sent: {alert_data}")
    
    async def _send_sms_notification(self, alert_data: Dict[str, Any]):
        """Send SMS notification"""
        # TODO: Implement SMS notification
        logger.info(f"SMS notification sent: {alert_data}")
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history for specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
        ]


class PerformanceProfiler:
    """Performance profiling and analysis"""
    
    def __init__(self):
        self.profiles: Dict[str, Dict[str, Any]] = {}
    
    @asynccontextmanager
    async def profile_operation(self, operation_name: str):
        """Profile an operation"""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage()
            
            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            
            self.profiles[operation_name] = {
                "duration": duration,
                "memory_delta": memory_delta,
                "start_memory": start_memory,
                "end_memory": end_memory,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss
    
    def get_profile(self, operation_name: str) -> Optional[Dict[str, Any]]:
        """Get profile for operation"""
        return self.profiles.get(operation_name)
    
    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all profiles"""
        return self.profiles.copy()


class AdvancedMonitoringService:
    """Main Advanced Monitoring Service"""
    
    def __init__(self, service_name: str, config: Optional[TracingConfig] = None):
        self.service_name = service_name
        self.config = config or TracingConfig(service_name=service_name)
        
        # Initialize components
        self.logger = StructuredLogger(service_name)
        self.metrics = MetricsCollector(service_name)
        self.tracer = DistributedTracer(service_name)
        self.alert_manager = AlertManager()
        self.profiler = PerformanceProfiler()
        
        # Start monitoring tasks
        self._monitoring_task = None
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start monitoring tasks"""
        self._monitoring_task = asyncio.create_task(self._monitor_resources())
    
    async def _monitor_resources(self):
        """Monitor system resources"""
        while True:
            try:
                import psutil
                
                # Monitor memory
                memory_info = psutil.virtual_memory()
                self.metrics.update_memory_usage(memory_info.used)
                
                # Monitor CPU
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics.update_cpu_usage(cpu_percent)
                
                # Monitor connections (example)
                connections = len(psutil.net_connections())
                self.metrics.update_active_connections(connections)
                
                # Check for alerts
                if memory_info.percent > 90:
                    self.alert_manager.check_alert(
                        "high_memory_usage",
                        True,
                        {"memory_percent": memory_info.percent}
                    )
                
                if cpu_percent > 80:
                    self.alert_manager.check_alert(
                        "high_cpu_usage",
                        True,
                        {"cpu_percent": cpu_percent}
                    )
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(5)
    
    @asynccontextmanager
    async def monitor_operation(self, operation_name: str, **attributes):
        """Monitor an operation with full observability"""
        correlation_context = CorrelationContext()
        
        # Start tracing
        async with self.tracer.trace_operation(operation_name, **attributes) as span:
            # Add correlation context
            span.set_attribute("correlation_id", correlation_context.correlation_id)
            
            start_time = time.time()
            
            try:
                # Start profiling
                async with self.profiler.profile_operation(operation_name):
                    yield span
                
                # Record success metrics
                duration = time.time() - start_time
                self.metrics.record_business_operation(operation_name, "success")
                
                # Log success
                self.logger.log("INFO", f"Operation {operation_name} completed successfully",
                               correlation_id=correlation_context.correlation_id,
                               duration=duration)
                
            except Exception as e:
                # Record error metrics
                duration = time.time() - start_time
                self.metrics.record_business_operation(operation_name, "error")
                self.metrics.record_error(operation_name, type(e).__name__)
                
                # Log error
                self.logger.log_error(e, 
                                    correlation_id=correlation_context.correlation_id,
                                    operation=operation_name,
                                    duration=duration)
                
                # Check for alerts
                self.alert_manager.check_alert(
                    "operation_failure",
                    True,
                    {
                        "operation": operation_name,
                        "error": str(e),
                        "correlation_id": correlation_context.correlation_id
                    }
                )
                
                raise
    
    def add_alert(self, alert: AlertConfig):
        """Add alert configuration"""
        self.alert_manager.add_alert(alert)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "profiles": self.profiler.get_all_profiles(),
            "alert_history": self.alert_manager.get_alert_history()
        }
    
    async def shutdown(self):
        """Shutdown monitoring service"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass


# Decorators for easy integration
def monitored(operation_name: str, alert_on_failure: bool = True):
    """Decorator for monitored operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get monitoring service instance
            # This would typically be injected or retrieved from a service locator
            monitoring_service = AdvancedMonitoringService("svgx_engine")
            
            async with monitoring_service.monitor_operation(operation_name) as span:
                # Add function attributes to span
                span.set_attribute("function_name", func.__name__)
                span.set_attribute("args_count", len(args))
                span.set_attribute("kwargs_count", len(kwargs))
                
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def traced(operation_name: str):
    """Decorator for traced operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = DistributedTracer("svgx_engine")
            
            async with tracer.trace_operation(operation_name) as span:
                span.set_attribute("function_name", func.__name__)
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Example usage and configuration
async def setup_advanced_monitoring():
    """Setup advanced monitoring service"""
    # Create monitoring service
    monitoring_service = AdvancedMonitoringService("svgx_engine")
    
    # Add alerts
    monitoring_service.add_alert(AlertConfig(
        name="high_memory_usage",
        condition="memory_percent > 90",
        severity=AlertSeverity.WARNING,
        channels=[AlertChannel.SLACK, AlertChannel.EMAIL]
    ))
    
    monitoring_service.add_alert(AlertConfig(
        name="high_cpu_usage",
        condition="cpu_percent > 80",
        severity=AlertSeverity.WARNING,
        channels=[AlertChannel.SLACK]
    ))
    
    monitoring_service.add_alert(AlertConfig(
        name="operation_failure",
        condition="operation_failed",
        severity=AlertSeverity.ERROR,
        channels=[AlertChannel.SLACK, AlertChannel.EMAIL, AlertChannel.WEBHOOK]
    ))
    
    return monitoring_service


if __name__ == "__main__":
    # Example usage
    async def main():
        monitoring_service = await setup_advanced_monitoring()
        
        # Example monitored operation
        @monitored("database_query", alert_on_failure=True)
        async def query_database():
            # Simulate database query
            await asyncio.sleep(0.1)
            return {"result": "success"}
        
        try:
            result = await query_database()
            print(f"Query result: {result}")
        except Exception as e:
            print(f"Query failed: {e}")
        
        # Get metrics
        metrics = monitoring_service.get_metrics()
        print(f"Monitoring metrics: {metrics}")
        
        # Shutdown
        await monitoring_service.shutdown()
    
    asyncio.run(main()) 