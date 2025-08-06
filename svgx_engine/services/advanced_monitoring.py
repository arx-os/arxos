"""
SVGX Engine - Advanced Monitoring Service

This module provides comprehensive monitoring and alerting capabilities for the SVGX Engine,
integrating with the Go notification API for enterprise-grade monitoring.

Features:
- Real-time system monitoring
- Performance metrics tracking
- Automated alerting via Go notification API
- Health checks and diagnostics
- Resource utilization monitoring
- Error tracking and reporting

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import asyncio
import logging
import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import json

from .notifications.go_client import (
    GoNotificationClient,
    NotificationRequest,
    NotificationType,
    NotificationPriority,
    NotificationChannelType,
)

logger = logging.getLogger(__name__)


class MonitoringLevel(str, Enum):
    """Monitoring levels for different types of alerts"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """Types of metrics that can be monitored"""

    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_IO = "network_io"
    PROCESS_COUNT = "process_count"
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    CUSTOM = "custom"


@dataclass
class MonitoringMetric:
    """Represents a monitoring metric"""

    name: str
    value: float
    unit: str
    timestamp: datetime
    metric_type: MetricType
    tags: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class AlertRule:
    """Defines an alert rule for monitoring"""

    name: str
    metric_type: MetricType
    threshold: float
    operator: str  # '>', '<', '>=', '<=', '=='
    duration: int  # seconds to maintain threshold before alerting
    level: MonitoringLevel
    channels: List[NotificationChannelType]
    recipients: List[int]
    message_template: str
    enabled: bool = True
    cooldown: int = 300  # seconds between alerts

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data["channels"] = [channel.value for channel in self.channels]
        return data


@dataclass
class AlertEvent:
    """Represents an alert event"""

    rule_name: str
    metric_name: str
    current_value: float
    threshold: float
    level: MonitoringLevel
    timestamp: datetime
    message: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["level"] = self.level.value
        return data


class AdvancedMonitoringService:
    """
    Advanced monitoring service with Go notification integration

    Provides comprehensive system monitoring, metric collection,
    and automated alerting via the Go notification API.
    """

    def __init__(
        self,
        go_notification_client: Optional[GoNotificationClient] = None,
        monitoring_interval: int = 60,
        alert_cooldown: int = 300,
        enable_system_metrics: bool = True,
        enable_custom_metrics: bool = True,
    ):
        """
        Initialize the advanced monitoring service

        Args:
            go_notification_client: Go notification client instance
            monitoring_interval: Monitoring interval in seconds
            alert_cooldown: Cooldown period between alerts in seconds
            enable_system_metrics: Enable system metrics collection
            enable_custom_metrics: Enable custom metrics collection
        """
        self.go_client = go_notification_client or GoNotificationClient()
        self.monitoring_interval = monitoring_interval
        self.alert_cooldown = alert_cooldown
        self.enable_system_metrics = enable_system_metrics
        self.enable_custom_metrics = enable_custom_metrics

        # Monitoring state
        self.is_running = False
        self.monitoring_thread = None
        self.metrics_history: List[MonitoringMetric] = []
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_history: List[AlertEvent] = []
        self.last_alert_times: Dict[str, datetime] = {}
        self.custom_metrics: Dict[str, Callable] = {}

        # System metrics
        self.cpu_threshold = 80.0
        self.memory_threshold = 85.0
        self.disk_threshold = 90.0

        # Performance tracking
        self.metrics_lock = threading.Lock()
        self.max_history_size = 1000

        logger.info("Advanced monitoring service initialized")

    def start_monitoring(self) -> None:
        """Start the monitoring service"""
        if self.is_running:
            logger.warning("Monitoring service is already running")
            return

        self.is_running = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()
        logger.info("Advanced monitoring service started")

    def stop_monitoring(self) -> None:
        """Stop the monitoring service"""
        if not self.is_running:
            logger.warning("Monitoring service is not running")
            return

        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Advanced monitoring service stopped")

    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Collect system metrics
                if self.enable_system_metrics:
                    self._collect_system_metrics()

                # Collect custom metrics
                if self.enable_custom_metrics:
                    self._collect_custom_metrics()

                # Check alert rules
                self._check_alert_rules()

                # Clean up old metrics
                self._cleanup_old_metrics()

                # Wait for next monitoring cycle
                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

    def _collect_system_metrics(self) -> None:
        """Collect system metrics"""
        try:
            timestamp = datetime.now()

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self._add_metric(
                name="cpu_usage",
                value=cpu_percent,
                unit="%",
                metric_type=MetricType.CPU_USAGE,
                timestamp=timestamp,
            )

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self._add_metric(
                name="memory_usage",
                value=memory_percent,
                unit="%",
                metric_type=MetricType.MEMORY_USAGE,
                timestamp=timestamp,
                metadata={
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                },
            )

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            self._add_metric(
                name="disk_usage",
                value=disk_percent,
                unit="%",
                metric_type=MetricType.DISK_USAGE,
                timestamp=timestamp,
                metadata={"total": disk.total, "used": disk.used, "free": disk.free},
            )

            # Network I/O
            network = psutil.net_io_counters()
            self._add_metric(
                name="network_bytes_sent",
                value=network.bytes_sent,
                unit="bytes",
                metric_type=MetricType.NETWORK_IO,
                timestamp=timestamp,
                metadata={"direction": "sent"},
            )
            self._add_metric(
                name="network_bytes_recv",
                value=network.bytes_recv,
                unit="bytes",
                metric_type=MetricType.NETWORK_IO,
                timestamp=timestamp,
                metadata={"direction": "received"},
            )

            # Process count
            process_count = len(psutil.pids())
            self._add_metric(
                name="process_count",
                value=process_count,
                unit="processes",
                metric_type=MetricType.PROCESS_COUNT,
                timestamp=timestamp,
            )

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    def _collect_custom_metrics(self) -> None:
        """Collect custom metrics"""
        timestamp = datetime.now()

        for metric_name, metric_func in self.custom_metrics.items():
            try:
                value = metric_func()
                self._add_metric(
                    name=metric_name,
                    value=value,
                    unit="custom",
                    metric_type=MetricType.CUSTOM,
                    timestamp=timestamp,
                )
            except Exception as e:
                logger.error(f"Error collecting custom metric {metric_name}: {e}")

    def _add_metric(self, **kwargs) -> None:
        """Add a metric to the history"""
        metric = MonitoringMetric(**kwargs)

        with self.metrics_lock:
            self.metrics_history.append(metric)

            # Limit history size
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history = self.metrics_history[-self.max_history_size :]

    def _check_alert_rules(self) -> None:
        """Check all alert rules and trigger alerts if needed"""
        current_time = datetime.now()

        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue

            # Check cooldown
            last_alert_time = self.last_alert_times.get(rule_name)
            if (
                last_alert_time
                and (current_time - last_alert_time).seconds < rule.cooldown
            ):
                continue

            # Get recent metrics for this rule
            recent_metrics = self._get_recent_metrics(rule.metric_type, rule.duration)

            if not recent_metrics:
                continue

            # Check if threshold is exceeded for the required duration
            threshold_exceeded = self._check_threshold_exceeded(
                recent_metrics, rule.threshold, rule.operator
            )

            if threshold_exceeded:
                self._trigger_alert(rule, recent_metrics[-1], current_time)

    def _get_recent_metrics(
        self, metric_type: MetricType, duration_seconds: int
    ) -> List[MonitoringMetric]:
        """Get recent metrics of a specific type"""
        cutoff_time = datetime.now() - timedelta(seconds=duration_seconds)

        with self.metrics_lock:
            return [
                metric
                for metric in self.metrics_history
                if metric.metric_type == metric_type and metric.timestamp >= cutoff_time
            ]

    def _check_threshold_exceeded(
        self, metrics: List[MonitoringMetric], threshold: float, operator: str
    ) -> bool:
        """Check if threshold is exceeded for all metrics in the list"""
        if not metrics:
            return False

        for metric in metrics:
            if operator == ">":
                if metric.value <= threshold:
                    return False
            elif operator == "<":
                if metric.value >= threshold:
                    return False
            elif operator == ">=":
                if metric.value < threshold:
                    return False
            elif operator == "<=":
                if metric.value > threshold:
                    return False
            elif operator == "==":
                if metric.value != threshold:
                    return False

        return True

    def _trigger_alert(
        self, rule: AlertRule, metric: MonitoringMetric, timestamp: datetime
    ) -> None:
        """Trigger an alert via Go notification API"""
        try:
            # Create alert message
            message = rule.message_template.format(
                metric_name=metric.name,
                current_value=metric.value,
                threshold=rule.threshold,
                unit=metric.unit,
            )

            # Create alert event
            alert_event = AlertEvent(
                rule_name=rule.name,
                metric_name=metric.name,
                current_value=metric.value,
                threshold=rule.threshold,
                level=rule.level,
                timestamp=timestamp,
                message=message,
                metadata={
                    "metric_type": metric.metric_type.value,
                    "unit": metric.unit,
                    "tags": metric.tags,
                },
            )

            # Add to alert history
            with self.metrics_lock:
                self.alert_history.append(alert_event)
                self.last_alert_times[rule.name] = timestamp

            # Send notification via Go API
            for recipient_id in rule.recipients:
                notification_request = NotificationRequest(
                    title=f"Monitoring Alert: {rule.name}",
                    message=message,
                    type=NotificationType.ALERT,
                    channels=rule.channels,
                    priority=self._get_priority_for_level(rule.level),
                    recipient_id=recipient_id,
                    metadata={
                        "alert_rule": rule.name,
                        "metric_name": metric.name,
                        "current_value": metric.value,
                        "threshold": rule.threshold,
                        "level": rule.level.value,
                    },
                )

                # Send notification (async if possible)
                try:
                    response = self.go_client.send_notification(notification_request)
                    if response.success:
                        logger.info(f"Alert sent successfully: {rule.name}")
                    else:
                        logger.error(f"Failed to send alert: {response.error}")
                except Exception as e:
                    logger.error(f"Error sending alert notification: {e}")

        except Exception as e:
            logger.error(f"Error triggering alert: {e}")

    def _get_priority_for_level(self, level: MonitoringLevel) -> NotificationPriority:
        """Convert monitoring level to notification priority"""
        if level == MonitoringLevel.CRITICAL:
            return NotificationPriority.URGENT
        elif level == MonitoringLevel.ERROR:
            return NotificationPriority.HIGH
        elif level == MonitoringLevel.WARNING:
            return NotificationPriority.NORMAL
        else:
            return NotificationPriority.LOW

    def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics from history"""
        cutoff_time = datetime.now() - timedelta(hours=24)  # Keep 24 hours

        with self.metrics_lock:
            self.metrics_history = [
                metric
                for metric in self.metrics_history
                if metric.timestamp >= cutoff_time
            ]

    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add an alert rule"""
        self.alert_rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def remove_alert_rule(self, rule_name: str) -> None:
        """Remove an alert rule"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")

    def add_custom_metric(self, name: str, metric_func: Callable[[], float]) -> None:
        """Add a custom metric function"""
        self.custom_metrics[name] = metric_func
        logger.info(f"Added custom metric: {name}")

    def remove_custom_metric(self, name: str) -> None:
        """Remove a custom metric"""
        if name in self.custom_metrics:
            del self.custom_metrics[name]
            logger.info(f"Removed custom metric: {name}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics"""
        with self.metrics_lock:
            if not self.metrics_history:
                return {"error": "No metrics available"}

            latest_metrics = {}
            for metric in self.metrics_history[-100:]:  # Last 100 metrics
                if metric.name not in latest_metrics:
                    latest_metrics[metric.name] = metric

            return {
                "timestamp": datetime.now().isoformat(),
                "metrics": [metric.to_dict() for metric in latest_metrics.values()],
                "total_metrics": len(self.metrics_history),
                "alert_rules": len(self.alert_rules),
                "recent_alerts": len(
                    [
                        a
                        for a in self.alert_history
                        if (datetime.now() - a.timestamp).seconds < 3600
                    ]
                ),
            }

    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history for the specified number of hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self.metrics_lock:
            recent_alerts = [
                alert for alert in self.alert_history if alert.timestamp >= cutoff_time
            ]

            return [alert.to_dict() for alert in recent_alerts]

    def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the monitoring service"""
        try:
            # Check if monitoring is running
            status = "healthy" if self.is_running else "stopped"

            # Check Go notification client
            go_client_health = self.go_client.health_check()

            # Get basic metrics
            with self.metrics_lock:
                metrics_count = len(self.metrics_history)
                alerts_count = len(self.alert_history)
                rules_count = len(self.alert_rules)

            return {
                "status": status,
                "monitoring_running": self.is_running,
                "metrics_count": metrics_count,
                "alerts_count": alerts_count,
                "rules_count": rules_count,
                "go_client_health": go_client_health,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def set_thresholds(
        self,
        cpu_threshold: Optional[float] = None,
        memory_threshold: Optional[float] = None,
        disk_threshold: Optional[float] = None,
    ) -> None:
        """Set monitoring thresholds"""
        if cpu_threshold is not None:
            self.cpu_threshold = cpu_threshold
        if memory_threshold is not None:
            self.memory_threshold = memory_threshold
        if disk_threshold is not None:
            self.disk_threshold = disk_threshold

        logger.info(
            f"Updated thresholds: CPU={self.cpu_threshold}%, "
            f"Memory={self.memory_threshold}%, Disk={self.disk_threshold}%"
        )


# Factory function for easy instantiation
def create_advanced_monitoring_service(
    go_notification_client: Optional[GoNotificationClient] = None,
    monitoring_interval: int = 60,
    alert_cooldown: int = 300,
    enable_system_metrics: bool = True,
    enable_custom_metrics: bool = True,
) -> AdvancedMonitoringService:
    """
    Create an advanced monitoring service

    Args:
        go_notification_client: Go notification client instance
        monitoring_interval: Monitoring interval in seconds
        alert_cooldown: Cooldown period between alerts in seconds
        enable_system_metrics: Enable system metrics collection
        enable_custom_metrics: Enable custom metrics collection

    Returns:
        Advanced monitoring service instance
    """
    return AdvancedMonitoringService(
        go_notification_client=go_notification_client,
        monitoring_interval=monitoring_interval,
        alert_cooldown=alert_cooldown,
        enable_system_metrics=enable_system_metrics,
        enable_custom_metrics=enable_custom_metrics,
    )


# Export main classes and functions
__all__ = [
    "AdvancedMonitoringService",
    "MonitoringLevel",
    "MetricType",
    "MonitoringMetric",
    "AlertRule",
    "AlertEvent",
    "create_advanced_monitoring_service",
]
