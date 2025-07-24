"""
SVGX Engine - Notification Monitoring and Observability

This module provides comprehensive monitoring and observability for the notification system:
- Prometheus metrics for notification delivery
- Structured logging with correlation IDs
- Health checks for notification channels
- Alerting for notification failures
- Dashboard for notification statistics

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import threading
from collections import defaultdict, Counter
import functools

# Prometheus metrics (optional)
try:
    from prometheus_client import (
        Counter, Histogram, Gauge, Summary,
        generate_latest, CONTENT_TYPE_LATEST
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Mock classes for when prometheus_client is not available
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
    class Summary:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass

from .go_client import (
    NotificationChannelType,
    NotificationPriority,
    NotificationType,
    NotificationStatus
)

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics for monitoring"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class NotificationMetrics:
    """Notification metrics data structure"""
    total_sent: int = 0
    total_delivered: int = 0
    total_failed: int = 0
    total_pending: int = 0
    success_rate: float = 0.0
    avg_delivery_time: float = 0.0
    avg_response_time: float = 0.0
    rate_limit_hits: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    active_connections: int = 0
    background_jobs: int = 0


@dataclass
class ChannelHealth:
    """Channel health status"""
    channel: NotificationChannelType
    status: str  # "healthy", "degraded", "unhealthy"
    response_time: float
    success_rate: float
    last_check: datetime
    error_count: int = 0
    total_requests: int = 0


@dataclass
class AlertEvent:
    """Alert event for notification failures"""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class StructuredLogger:
    """Structured logger with correlation IDs"""
    
    def __init__(self, logger_name: str = "notification_system"):
        self.logger = logging.getLogger(logger_name)
        self.correlation_id = None
        self._lock = threading.Lock()
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for current context"""
        self.correlation_id = correlation_id
    
    def _get_extra_fields(self) -> Dict[str, Any]:
        """Get extra fields for structured logging"""
        extra = {}
        if self.correlation_id:
            extra['correlation_id'] = self.correlation_id
        return extra
    
    def info(self, message: str, **kwargs):
        """Log info message with structured data"""
        extra = self._get_extra_fields()
        extra.update(kwargs)
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with structured data"""
        extra = self._get_extra_fields()
        extra.update(kwargs)
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, **kwargs):
        """Log error message with structured data"""
        extra = self._get_extra_fields()
        extra.update(kwargs)
        self.logger.error(message, extra=extra)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with structured data"""
        extra = self._get_extra_fields()
        extra.update(kwargs)
        self.logger.critical(message, extra=extra)


class PrometheusMetrics:
    """Prometheus metrics for notification system"""
    
    def __init__(self):
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not available, metrics disabled")
            return
        
        # Notification counters
        self.notifications_sent = Counter(
            'notifications_sent_total',
            'Total notifications sent',
            ['channel', 'type', 'priority']
        )
        
        self.notifications_delivered = Counter(
            'notifications_delivered_total',
            'Total notifications delivered',
            ['channel', 'type', 'priority']
        )
        
        self.notifications_failed = Counter(
            'notifications_failed_total',
            'Total notifications failed',
            ['channel', 'type', 'priority', 'error_type']
        )
        
        # Response time histograms
        self.notification_duration = Histogram(
            'notification_duration_seconds',
            'Notification delivery duration',
            ['channel', 'type'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )
        
        self.api_response_time = Histogram(
            'api_response_time_seconds',
            'API response time',
            ['endpoint', 'method'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
        )
        
        # Gauges
        self.active_notifications = Gauge(
            'active_notifications',
            'Number of active notifications',
            ['status']
        )
        
        self.cache_hit_ratio = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio'
        )
        
        self.rate_limit_remaining = Gauge(
            'rate_limit_remaining',
            'Remaining rate limit capacity'
        )
        
        # Summaries
        self.notification_size = Summary(
            'notification_size_bytes',
            'Notification size in bytes',
            ['channel', 'type']
        )
    
    def record_notification_sent(self, channel: str, notification_type: str, priority: str):
        """Record notification sent"""
        if PROMETHEUS_AVAILABLE:
            self.notifications_sent.labels(
                channel=channel,
                type=notification_type,
                priority=priority
            ).inc()
    
    def record_notification_delivered(self, channel: str, notification_type: str, priority: str):
        """Record notification delivered"""
        if PROMETHEUS_AVAILABLE:
            self.notifications_delivered.labels(
                channel=channel,
                type=notification_type,
                priority=priority
            ).inc()
    
    def record_notification_failed(self, channel: str, notification_type: str, priority: str, error_type: str):
        """Record notification failed"""
        if PROMETHEUS_AVAILABLE:
            self.notifications_failed.labels(
                channel=channel,
                type=notification_type,
                priority=priority,
                error_type=error_type
            ).inc()
    
    def record_delivery_duration(self, channel: str, notification_type: str, duration: float):
        """Record delivery duration"""
        if PROMETHEUS_AVAILABLE:
            self.notification_duration.labels(
                channel=channel,
                type=notification_type
            ).observe(duration)
    
    def record_api_response_time(self, endpoint: str, method: str, duration: float):
        """Record API response time"""
        if PROMETHEUS_AVAILABLE:
            self.api_response_time.labels(
                endpoint=endpoint,
                method=method
            ).observe(duration)
    
    def set_active_notifications(self, status: str, count: int):
        """Set active notifications count"""
        if PROMETHEUS_AVAILABLE:
            self.active_notifications.labels(status=status).set(count)
    
    def set_cache_hit_ratio(self, ratio: float):
        """Set cache hit ratio"""
        if PROMETHEUS_AVAILABLE:
            self.cache_hit_ratio.set(ratio)
    
    def set_rate_limit_remaining(self, remaining: int):
        """Set rate limit remaining capacity"""
        if PROMETHEUS_AVAILABLE:
            self.rate_limit_remaining.set(remaining)
    
    def record_notification_size(self, channel: str, notification_type: str, size: int):
        """Record notification size"""
        if PROMETHEUS_AVAILABLE:
            self.notification_size.labels(
                channel=channel,
                type=notification_type
            ).observe(size)


class HealthChecker:
    """Health checker for notification channels"""
    
    def __init__(self, go_client):
        self.go_client = go_client
        self.channel_health: Dict[NotificationChannelType, ChannelHealth] = {}
        self._lock = threading.Lock()
        self.structured_logger = StructuredLogger("health_checker")
    
    async def check_channel_health(self, channel: NotificationChannelType) -> ChannelHealth:
        """Check health of a specific channel"""
        start_time = time.time()
        
        try:
            # Create a test notification for health check
            test_request = {
                "title": "Health Check",
                "message": "This is a health check notification",
                "type": "system",
                "channels": [channel.value],
                "priority": "normal",
                "recipient_id": 1
            }
            
            # Send health check notification
            response = await self.go_client.send_notification_async(test_request)
            
            response_time = time.time() - start_time
            
            # Determine status based on response
            if response.success:
                status = "healthy"
                success_rate = 1.0
                error_count = 0
            else:
                status = "unhealthy"
                success_rate = 0.0
                error_count = 1
            
            health = ChannelHealth(
                channel=channel,
                status=status,
                response_time=response_time,
                success_rate=success_rate,
                last_check=datetime.now(),
                error_count=error_count,
                total_requests=1
            )
            
            with self._lock:
                self.channel_health[channel] = health
            
            self.structured_logger.info(
                f"Channel health check completed",
                channel=channel.value,
                status=status,
                response_time=response_time,
                success_rate=success_rate
            )
            
            return health
            
        except Exception as e:
            response_time = time.time() - start_time
            
            health = ChannelHealth(
                channel=channel,
                status="unhealthy",
                response_time=response_time,
                success_rate=0.0,
                last_check=datetime.now(),
                error_count=1,
                total_requests=1
            )
            
            with self._lock:
                self.channel_health[channel] = health
            
            self.structured_logger.error(
                f"Channel health check failed",
                channel=channel.value,
                error=str(e),
                response_time=response_time
            )
            
            return health
    
    async def check_all_channels(self) -> Dict[NotificationChannelType, ChannelHealth]:
        """Check health of all channels"""
        channels = [
            NotificationChannelType.EMAIL,
            NotificationChannelType.SLACK,
            NotificationChannelType.SMS,
            NotificationChannelType.WEBHOOK,
            NotificationChannelType.PUSH,
            NotificationChannelType.IN_APP
        ]
        
        tasks = [self.check_channel_health(channel) for channel in channels]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        health_results = {}
        for channel, result in zip(channels, results):
            if isinstance(result, Exception):
                health_results[channel] = ChannelHealth(
                    channel=channel,
                    status="unhealthy",
                    response_time=0.0,
                    success_rate=0.0,
                    last_check=datetime.now(),
                    error_count=1,
                    total_requests=0
                )
            else:
                health_results[channel] = result
        
        return health_results
    
    def get_channel_health(self, channel: NotificationChannelType) -> Optional[ChannelHealth]:
        """Get cached health status for a channel"""
        with self._lock:
            return self.channel_health.get(channel)
    
    def get_all_channel_health(self) -> Dict[NotificationChannelType, ChannelHealth]:
        """Get all cached channel health status"""
        with self._lock:
            return self.channel_health.copy()


class AlertManager:
    """Alert manager for notification failures"""
    
    def __init__(self):
        self.alerts: List[AlertEvent] = []
        self.alert_handlers: List[Callable] = []
        self._lock = threading.Lock()
        self.structured_logger = StructuredLogger("alert_manager")
    
    def add_alert_handler(self, handler: Callable[[AlertEvent], None]):
        """Add alert handler"""
        self.alert_handlers.append(handler)
    
    def create_alert(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AlertEvent:
        """Create and dispatch an alert"""
        alert = AlertEvent(
            id=str(uuid.uuid4()),
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.now(),
            correlation_id=correlation_id,
            metadata=metadata
        )
        
        with self._lock:
            self.alerts.append(alert)
        
        # Dispatch to handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.structured_logger.error(
                    f"Alert handler failed",
                    handler=str(handler),
                    error=str(e)
                )
        
        self.structured_logger.warning(
            f"Alert created",
            alert_id=alert.id,
            severity=alert.severity.value,
            title=alert.title,
            correlation_id=alert.correlation_id
        )
        
        return alert
    
    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        hours: int = 24
    ) -> List[AlertEvent]:
        """Get alerts with optional filtering"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            filtered_alerts = [
                alert for alert in self.alerts
                if alert.timestamp >= cutoff_time
                and (severity is None or alert.severity == severity)
            ]
        
        return filtered_alerts
    
    def clear_old_alerts(self, hours: int = 168):  # 7 days
        """Clear old alerts"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            self.alerts = [
                alert for alert in self.alerts
                if alert.timestamp >= cutoff_time
            ]


class NotificationDashboard:
    """Dashboard for notification statistics"""
    
    def __init__(self, go_client, metrics: PrometheusMetrics, health_checker: HealthChecker, alert_manager: AlertManager):
        self.go_client = go_client
        self.metrics = metrics
        self.health_checker = health_checker
        self.alert_manager = alert_manager
        self.structured_logger = StructuredLogger("dashboard")
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            # Get notification statistics
            stats = await self.go_client.get_notification_statistics_async()
            
            # Get channel health
            channel_health = await self.health_checker.check_all_channels()
            
            # Get recent alerts
            recent_alerts = self.alert_manager.get_alerts(hours=24)
            
            # Get performance metrics
            performance_metrics = self.go_client.get_performance_metrics()
            
            dashboard_data = {
                "timestamp": datetime.now().isoformat(),
                "statistics": {
                    "total_sent": stats.total_sent if stats else 0,
                    "total_delivered": stats.total_delivered if stats else 0,
                    "total_failed": stats.total_failed if stats else 0,
                    "success_rate": stats.success_rate if stats else 0.0,
                    "avg_delivery_time": stats.avg_delivery_time if stats else 0.0
                },
                "channel_health": {
                    channel.value: {
                        "status": health.status,
                        "response_time": health.response_time,
                        "success_rate": health.success_rate,
                        "last_check": health.last_check.isoformat(),
                        "error_count": health.error_count
                    }
                    for channel, health in channel_health.items()
                },
                "recent_alerts": [
                    {
                        "id": alert.id,
                        "severity": alert.severity.value,
                        "title": alert.title,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "correlation_id": alert.correlation_id
                    }
                    for alert in recent_alerts
                ],
                "performance": {
                    "cache_hit_ratio": performance_metrics.get("cache_hit_ratio", 0.0),
                    "avg_response_time": performance_metrics.get("avg_response_time", 0.0),
                    "active_connections": performance_metrics.get("active_connections", 0),
                    "background_jobs": performance_metrics.get("background_jobs", 0)
                }
            }
            
            self.structured_logger.info(
                "Dashboard data generated",
                total_sent=dashboard_data["statistics"]["total_sent"],
                success_rate=dashboard_data["statistics"]["success_rate"],
                alert_count=len(dashboard_data["recent_alerts"])
            )
            
            return dashboard_data
            
        except Exception as e:
            self.structured_logger.error(
                "Failed to generate dashboard data",
                error=str(e)
            )
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format"""
        if PROMETHEUS_AVAILABLE:
            return generate_latest()
        else:
            return "# Prometheus metrics not available\n"


class NotificationMonitoring:
    """Comprehensive notification monitoring system"""
    
    def __init__(
        self,
        go_client,
        enable_prometheus: bool = True,
        health_check_interval: int = 300,
        alert_retention_hours: int = 168
    ):
        self.go_client = go_client
        self.structured_logger = StructuredLogger("notification_monitoring")
        
        # Initialize components
        self.metrics = PrometheusMetrics() if enable_prometheus else None
        self.health_checker = HealthChecker(go_client)
        self.alert_manager = AlertManager()
        self.dashboard = NotificationDashboard(
            go_client, self.metrics, self.health_checker, self.alert_manager
        )
        
        # Configuration
        self.health_check_interval = health_check_interval
        self.alert_retention_hours = alert_retention_hours
        
        # Background tasks
        self._health_check_task = None
        self._cleanup_task = None
        self._running = False
    
    async def start_monitoring(self):
        """Start monitoring background tasks"""
        if self._running:
            return
        
        self._running = True
        
        # Start health check task
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        self.structured_logger.info("Notification monitoring started")
    
    async def stop_monitoring(self):
        """Stop monitoring background tasks"""
        if not self._running:
            return
        
        self._running = False
        
        if self._health_check_task:
            self._health_check_task.cancel()
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        self.structured_logger.info("Notification monitoring stopped")
    
    async def _health_check_loop(self):
        """Background health check loop"""
        while self._running:
            try:
                await self.health_checker.check_all_channels()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.structured_logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while self._running:
            try:
                self.alert_manager.clear_old_alerts(self.alert_retention_hours)
                await asyncio.sleep(3600)  # Run every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.structured_logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(300)  # Wait before retry
    
    def record_notification_event(
        self,
        event_type: str,
        channel: str,
        notification_type: str,
        priority: str,
        duration: float = 0.0,
        success: bool = True,
        error_type: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """Record notification event for monitoring"""
        self.structured_logger.set_correlation_id(correlation_id or str(uuid.uuid4()))
        
        if self.metrics:
            if event_type == "sent":
                self.metrics.record_notification_sent(channel, notification_type, priority)
            elif event_type == "delivered":
                self.metrics.record_notification_delivered(channel, notification_type, priority)
                self.metrics.record_delivery_duration(channel, notification_type, duration)
            elif event_type == "failed":
                self.metrics.record_notification_failed(channel, notification_type, priority, error_type or "unknown")
        
        # Create alert for failures
        if event_type == "failed":
            self.alert_manager.create_alert(
                severity=AlertSeverity.ERROR,
                title="Notification Delivery Failed",
                message=f"Failed to deliver {notification_type} notification via {channel}",
                correlation_id=correlation_id,
                metadata={
                    "channel": channel,
                    "type": notification_type,
                    "priority": priority,
                    "error_type": error_type
                }
            )
        
        self.structured_logger.info(
            f"Notification event recorded",
            event_type=event_type,
            channel=channel,
            type=notification_type,
            priority=priority,
            duration=duration,
            success=success,
            error_type=error_type
        )
    
    async def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary"""
        dashboard_data = await self.dashboard.get_dashboard_data()
        
        summary = {
            "monitoring_status": "active" if self._running else "inactive",
            "dashboard": dashboard_data,
            "health_check_interval": self.health_check_interval,
            "alert_retention_hours": self.alert_retention_hours
        }
        
        return summary


# Factory functions
def create_notification_monitoring(
    go_client,
    enable_prometheus: bool = True,
    health_check_interval: int = 300,
    alert_retention_hours: int = 168
) -> NotificationMonitoring:
    """
    Create notification monitoring system
    
    Args:
        go_client: Go notification client
        enable_prometheus: Enable Prometheus metrics
        health_check_interval: Health check interval in seconds
        alert_retention_hours: Alert retention period in hours
        
    Returns:
        Notification monitoring system
    """
    return NotificationMonitoring(
        go_client=go_client,
        enable_prometheus=enable_prometheus,
        health_check_interval=health_check_interval,
        alert_retention_hours=alert_retention_hours
    )


def create_structured_logger(logger_name: str = "notification_system") -> StructuredLogger:
    """
    Create structured logger
    
    Args:
        logger_name: Logger name
        
    Returns:
        Structured logger
    """
    return StructuredLogger(logger_name)


# Export main classes and functions
__all__ = [
    'NotificationMonitoring',
    'StructuredLogger',
    'PrometheusMetrics',
    'HealthChecker',
    'AlertManager',
    'NotificationDashboard',
    'AlertEvent',
    'AlertSeverity',
    'ChannelHealth',
    'NotificationMetrics',
    'create_notification_monitoring',
    'create_structured_logger'
] 