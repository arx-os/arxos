"""
Monitoring and Alerting Service.

Application service for comprehensive monitoring, alerting, and observability
including metrics collection, alert management, and dashboard operations.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import asdict
import json
import uuid
from collections import defaultdict, deque

from domain.entities.monitoring_entity import (
    Metric, MetricDataPoint, AlertRule, Alert, Dashboard,
    MetricType, AlertSeverity, AlertStatus, NotificationChannel,
    DashboardType, AnomalyDetectionMethod
)
from application.dto.monitoring_dto import (
    CreateMetricRequest, CreateMetricResponse,
    MetricDataRequest, MetricDataResponse,
    CreateAlertRuleRequest, CreateAlertRuleResponse,
    AlertResponse, ListAlertsResponse,
    CreateDashboardRequest, CreateDashboardResponse,
    DashboardResponse, SystemHealthResponse,
    MetricStatsResponse, AlertStatsResponse
)
from infrastructure.services.alert_engine import AlertEngine
from infrastructure.services.notification_service import NotificationService
from infrastructure.logging.structured_logging import get_logger, log_context
from infrastructure.performance.monitoring import monitor_performance, performance_monitor
from infrastructure.security.authorization import require_permission, Permission


logger = get_logger(__name__)


class MonitoringService:
    """Comprehensive monitoring and alerting service."""
    
    def __init__(self, alert_engine: AlertEngine = None,
                 notification_service: NotificationService = None):
        self.alert_engine = alert_engine
        self.notification_service = notification_service
        
        # In-memory storage (production would use time-series database)
        self.metrics: Dict[str, Metric] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.dashboards: Dict[str, Dashboard] = {}
        
        # System metrics tracking
        self.system_metrics = {
            "service_started_at": datetime.now(timezone.utc),
            "total_metrics": 0,
            "total_data_points": 0,
            "total_alert_rules": 0,
            "active_alerts_count": 0,
            "total_dashboards": 0
        }
        
        # Built-in system metrics
        self._initialize_system_metrics()
        
        # Background tasks
        self._evaluation_task = None
        self._cleanup_task = None

    def _initialize_system_metrics(self) -> None:
        """Initialize built-in system metrics."""
        system_metrics_definitions = [
            {
                "name": "system.cpu.usage",
                "description": "CPU usage percentage",
                "metric_type": MetricType.GAUGE,
                "unit": "percent"
            },
            {
                "name": "system.memory.usage",
                "description": "Memory usage percentage", 
                "metric_type": MetricType.GAUGE,
                "unit": "percent"
            },
            {
                "name": "system.disk.usage",
                "description": "Disk usage percentage",
                "metric_type": MetricType.GAUGE,
                "unit": "percent"
            },
            {
                "name": "application.requests.total",
                "description": "Total application requests",
                "metric_type": MetricType.COUNTER,
                "unit": "count"
            },
            {
                "name": "application.response.time",
                "description": "Application response time",
                "metric_type": MetricType.TIMER,
                "unit": "milliseconds"
            },
            {
                "name": "application.errors.total",
                "description": "Total application errors",
                "metric_type": MetricType.COUNTER,
                "unit": "count"
            }
        ]
        
        for metric_def in system_metrics_definitions:
            metric = Metric(
                name=metric_def["name"],
                description=metric_def["description"],
                metric_type=metric_def["metric_type"],
                unit=metric_def["unit"],
                created_by="system"
            )
            self.metrics[metric.name] = metric
            self.system_metrics["total_metrics"] += 1

    @monitor_performance("create_metric")
    @require_permission(Permission.MANAGE_MONITORING)
    def create_metric(self, request: CreateMetricRequest, created_by: str) -> CreateMetricResponse:
        """Create new metric definition."""
        with log_context(operation="create_metric", user=created_by):
            try:
                # Check if metric already exists
                if request.name in self.metrics:
                    return CreateMetricResponse(
                        success=False,
                        message=f"Metric {request.name} already exists"
                    )
                
                # Create metric
                metric = Metric(
                    name=request.name,
                    description=request.description,
                    metric_type=MetricType(request.metric_type),
                    unit=request.unit,
                    tags=request.tags,
                    retention_days=request.retention_days,
                    resolution_seconds=request.resolution_seconds,
                    aggregation_method=request.aggregation_method,
                    created_by=created_by
                )
                
                # Store metric
                self.metrics[metric.name] = metric
                self.system_metrics["total_metrics"] += 1
                
                logger.info(f"Created metric: {metric.name}")
                
                return CreateMetricResponse(
                    success=True,
                    metric_id=metric.id,
                    message="Metric created successfully",
                    metric=metric.to_dict()
                )
                
            except Exception as e:
                logger.error(f"Failed to create metric: {e}")
                return CreateMetricResponse(
                    success=False,
                    message=f"Failed to create metric: {str(e)}"
                )

    @monitor_performance("record_metric_data")
    def record_metric_data(self, request: MetricDataRequest) -> MetricDataResponse:
        """Record data points for metric."""
        try:
            if request.metric_name not in self.metrics:
                return MetricDataResponse(
                    success=False,
                    message=f"Metric {request.metric_name} not found"
                )
            
            metric = self.metrics[request.metric_name]
            recorded_count = 0
            
            # Handle single value
            if request.value is not None:
                metric.add_data_point(
                    value=request.value,
                    timestamp=request.timestamp,
                    tags=request.tags,
                    metadata=request.metadata
                )
                recorded_count = 1
            
            # Handle batch values
            elif request.data_points:
                for data_point in request.data_points:
                    metric.add_data_point(
                        value=data_point["value"],
                        timestamp=datetime.fromisoformat(data_point["timestamp"]) if "timestamp" in data_point else None,
                        tags=data_point.get("tags", {}),
                        metadata=data_point.get("metadata", {})
                    )
                    recorded_count += 1
            
            self.system_metrics["total_data_points"] += recorded_count
            
            # Trigger alert evaluation if alert engine is available
            if self.alert_engine and recorded_count > 0:
                asyncio.create_task(self._evaluate_metric_alerts(request.metric_name))
            
            return MetricDataResponse(
                success=True,
                points_recorded=recorded_count,
                message=f"Recorded {recorded_count} data points"
            )
            
        except Exception as e:
            logger.error(f"Failed to record metric data: {e}")
            return MetricDataResponse(
                success=False,
                message=f"Failed to record data: {str(e)}"
            )

    @monitor_performance("get_metric_stats")
    @require_permission(Permission.VIEW_MONITORING)
    def get_metric_statistics(self, metric_name: str, start_time: datetime = None,
                            end_time: datetime = None) -> MetricStatsResponse:
        """Get metric statistics."""
        try:
            if metric_name not in self.metrics:
                return MetricStatsResponse(
                    success=False,
                    message=f"Metric {metric_name} not found"
                )
            
            metric = self.metrics[metric_name]
            
            # Get statistics for time range
            stats = metric.get_statistics(start_time, end_time)
            
            # Add current value
            stats["current_value"] = metric.get_current_value()
            
            # Detect anomalies if requested
            if stats.get("count", 0) >= 10:
                anomalies = metric.detect_anomalies()
                stats["anomalies"] = anomalies
                stats["anomaly_count"] = len(anomalies)
            
            return MetricStatsResponse(
                success=True,
                metric_name=metric_name,
                statistics=stats
            )
            
        except Exception as e:
            logger.error(f"Failed to get metric statistics: {e}")
            return MetricStatsResponse(
                success=False,
                message=f"Failed to get statistics: {str(e)}"
            )

    @monitor_performance("create_alert_rule")
    @require_permission(Permission.MANAGE_MONITORING)
    def create_alert_rule(self, request: CreateAlertRuleRequest, created_by: str) -> CreateAlertRuleResponse:
        """Create new alert rule."""
        with log_context(operation="create_alert_rule", user=created_by):
            try:
                # Validate metric exists
                if request.metric_name not in self.metrics:
                    return CreateAlertRuleResponse(
                        success=False,
                        message=f"Metric {request.metric_name} not found"
                    )
                
                # Create alert rule
                alert_rule = AlertRule(
                    name=request.name,
                    description=request.description,
                    metric_name=request.metric_name,
                    condition=request.condition,
                    severity=AlertSeverity(request.severity),
                    enabled=request.enabled,
                    cooldown_minutes=request.cooldown_minutes,
                    max_alerts_per_hour=request.max_alerts_per_hour,
                    notification_channels=request.notification_channels,
                    escalation_policy=request.escalation_policy,
                    suppression_conditions=request.suppression_conditions,
                    created_by=created_by,
                    tags=request.tags
                )
                
                # Store alert rule
                self.alert_rules[alert_rule.id] = alert_rule
                self.system_metrics["total_alert_rules"] += 1
                
                # Register with alert engine
                if self.alert_engine:
                    self.alert_engine.register_alert_rule(alert_rule)
                
                logger.info(f"Created alert rule: {alert_rule.name}")
                
                return CreateAlertRuleResponse(
                    success=True,
                    rule_id=alert_rule.id,
                    message="Alert rule created successfully",
                    rule=alert_rule.to_dict()
                )
                
            except Exception as e:
                logger.error(f"Failed to create alert rule: {e}")
                return CreateAlertRuleResponse(
                    success=False,
                    message=f"Failed to create alert rule: {str(e)}"
                )

    @monitor_performance("list_alerts")
    @require_permission(Permission.VIEW_MONITORING)
    def list_alerts(self, status: Optional[str] = None, severity: Optional[str] = None,
                   start_time: datetime = None, end_time: datetime = None,
                   page: int = 1, page_size: int = 50) -> ListAlertsResponse:
        """List alerts with filtering."""
        try:
            alerts = list(self.active_alerts.values())
            
            # Apply filters
            if status:
                alerts = [a for a in alerts if a.status.value == status]
            
            if severity:
                alerts = [a for a in alerts if a.severity.value == severity]
            
            if start_time:
                alerts = [a for a in alerts if a.triggered_at >= start_time]
            
            if end_time:
                alerts = [a for a in alerts if a.triggered_at <= end_time]
            
            # Sort by triggered time (newest first)
            alerts.sort(key=lambda x: x.triggered_at, reverse=True)
            
            # Pagination
            total_count = len(alerts)
            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_alerts = alerts[start_index:end_index]
            
            # Convert to dict format
            alert_dicts = [alert.to_dict() for alert in paginated_alerts]
            
            return ListAlertsResponse(
                success=True,
                alerts=alert_dicts,
                total_count=total_count,
                page=page,
                page_size=page_size,
                total_pages=(total_count + page_size - 1) // page_size,
                has_next=end_index < total_count,
                has_prev=page > 1
            )
            
        except Exception as e:
            logger.error(f"Failed to list alerts: {e}")
            return ListAlertsResponse(
                success=False,
                message=f"Failed to list alerts: {str(e)}"
            )

    @monitor_performance("acknowledge_alert")
    @require_permission(Permission.MANAGE_MONITORING)
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str, note: str = "") -> AlertResponse:
        """Acknowledge an alert."""
        with log_context(operation="acknowledge_alert", alert_id=alert_id, user=acknowledged_by):
            try:
                if alert_id not in self.active_alerts:
                    return AlertResponse(
                        success=False,
                        message="Alert not found"
                    )
                
                alert = self.active_alerts[alert_id]
                alert.acknowledge(acknowledged_by, note)
                
                # Notify alert engine
                if self.alert_engine:
                    self.alert_engine.update_alert_status(alert_id, AlertStatus.ACKNOWLEDGED)
                
                logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
                
                return AlertResponse(
                    success=True,
                    alert=alert.to_dict(),
                    message="Alert acknowledged successfully"
                )
                
            except Exception as e:
                logger.error(f"Failed to acknowledge alert: {e}")
                return AlertResponse(
                    success=False,
                    message=f"Failed to acknowledge alert: {str(e)}"
                )

    @monitor_performance("resolve_alert")
    @require_permission(Permission.MANAGE_MONITORING)
    def resolve_alert(self, alert_id: str, resolved_by: str, note: str = "") -> AlertResponse:
        """Resolve an alert."""
        with log_context(operation="resolve_alert", alert_id=alert_id, user=resolved_by):
            try:
                if alert_id not in self.active_alerts:
                    return AlertResponse(
                        success=False,
                        message="Alert not found"
                    )
                
                alert = self.active_alerts[alert_id]
                alert.resolve(resolved_by, note)
                
                # Notify alert engine
                if self.alert_engine:
                    self.alert_engine.update_alert_status(alert_id, AlertStatus.RESOLVED)
                
                # Update active alerts count
                self.system_metrics["active_alerts_count"] = len([
                    a for a in self.active_alerts.values() 
                    if a.status == AlertStatus.ACTIVE
                ])
                
                logger.info(f"Alert resolved: {alert_id} by {resolved_by}")
                
                return AlertResponse(
                    success=True,
                    alert=alert.to_dict(),
                    message="Alert resolved successfully"
                )
                
            except Exception as e:
                logger.error(f"Failed to resolve alert: {e}")
                return AlertResponse(
                    success=False,
                    message=f"Failed to resolve alert: {str(e)}"
                )

    @monitor_performance("create_dashboard")
    @require_permission(Permission.MANAGE_MONITORING)
    def create_dashboard(self, request: CreateDashboardRequest, created_by: str) -> CreateDashboardResponse:
        """Create new dashboard."""
        with log_context(operation="create_dashboard", user=created_by):
            try:
                # Create dashboard
                dashboard = Dashboard(
                    name=request.name,
                    description=request.description,
                    dashboard_type=DashboardType(request.dashboard_type),
                    widgets=request.widgets,
                    layout=request.layout,
                    visibility=request.visibility,
                    owner=created_by,
                    shared_with=request.shared_with,
                    refresh_interval_seconds=request.refresh_interval_seconds,
                    auto_refresh=request.auto_refresh,
                    time_range=request.time_range,
                    tags=request.tags
                )
                
                # Store dashboard
                self.dashboards[dashboard.id] = dashboard
                self.system_metrics["total_dashboards"] += 1
                
                logger.info(f"Created dashboard: {dashboard.name}")
                
                return CreateDashboardResponse(
                    success=True,
                    dashboard_id=dashboard.id,
                    message="Dashboard created successfully",
                    dashboard=dashboard.to_dict()
                )
                
            except Exception as e:
                logger.error(f"Failed to create dashboard: {e}")
                return CreateDashboardResponse(
                    success=False,
                    message=f"Failed to create dashboard: {str(e)}"
                )

    @monitor_performance("get_dashboard")
    @require_permission(Permission.VIEW_MONITORING)
    def get_dashboard(self, dashboard_id: str, user_id: str) -> DashboardResponse:
        """Get dashboard by ID."""
        try:
            if dashboard_id not in self.dashboards:
                return DashboardResponse(
                    success=False,
                    message="Dashboard not found"
                )
            
            dashboard = self.dashboards[dashboard_id]
            
            # Check access permissions
            if not self._check_dashboard_access(dashboard, user_id):
                return DashboardResponse(
                    success=False,
                    message="Access denied"
                )
            
            # Record view
            dashboard.record_view()
            
            # Get real-time data for widgets
            dashboard_data = dashboard.to_dict()
            dashboard_data["widget_data"] = self._get_dashboard_widget_data(dashboard)
            
            return DashboardResponse(
                success=True,
                dashboard=dashboard_data
            )
            
        except Exception as e:
            logger.error(f"Failed to get dashboard: {e}")
            return DashboardResponse(
                success=False,
                message=f"Failed to get dashboard: {str(e)}"
            )

    @monitor_performance("get_system_health")
    @require_permission(Permission.VIEW_MONITORING)
    def get_system_health(self) -> SystemHealthResponse:
        """Get comprehensive system health status."""
        try:
            # Calculate system health metrics
            now = datetime.now(timezone.utc)
            uptime_seconds = (now - self.system_metrics["service_started_at"]).total_seconds()
            
            # Active alerts by severity
            active_alerts = [a for a in self.active_alerts.values() if a.status == AlertStatus.ACTIVE]
            alert_breakdown = {
                "critical": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                "high": len([a for a in active_alerts if a.severity == AlertSeverity.HIGH]),
                "medium": len([a for a in active_alerts if a.severity == AlertSeverity.MEDIUM]),
                "low": len([a for a in active_alerts if a.severity == AlertSeverity.LOW])
            }
            
            # System status determination
            if alert_breakdown["critical"] > 0:
                system_status = "critical"
            elif alert_breakdown["high"] > 0:
                system_status = "degraded"
            elif alert_breakdown["medium"] > 5:
                system_status = "warning"
            else:
                system_status = "healthy"
            
            # Component health
            component_health = self._get_component_health()
            
            # Recent metrics activity
            recent_activity = self._get_recent_metrics_activity()
            
            health_data = {
                "system_status": system_status,
                "uptime_seconds": uptime_seconds,
                "timestamp": now.isoformat(),
                "metrics": {
                    "total_metrics": self.system_metrics["total_metrics"],
                    "total_data_points": self.system_metrics["total_data_points"],
                    "total_alert_rules": self.system_metrics["total_alert_rules"],
                    "active_alerts": len(active_alerts),
                    "total_dashboards": self.system_metrics["total_dashboards"]
                },
                "alert_breakdown": alert_breakdown,
                "component_health": component_health,
                "recent_activity": recent_activity,
                "recommendations": self._generate_health_recommendations(system_status, alert_breakdown)
            }
            
            return SystemHealthResponse(
                success=True,
                health_data=health_data
            )
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return SystemHealthResponse(
                success=False,
                message=f"Failed to get system health: {str(e)}"
            )

    async def _evaluate_metric_alerts(self, metric_name: str) -> None:
        """Evaluate alerts for a specific metric."""
        try:
            if not self.alert_engine or metric_name not in self.metrics:
                return
            
            metric = self.metrics[metric_name]
            current_value = metric.get_current_value()
            
            if current_value is None:
                return
            
            # Get relevant alert rules for this metric
            relevant_rules = [
                rule for rule in self.alert_rules.values()
                if rule.metric_name == metric_name and rule.enabled
            ]
            
            for rule in relevant_rules:
                # Get metric statistics for context
                metric_stats = metric.get_statistics()
                
                # Evaluate rule
                evaluation_result = rule.evaluate(current_value, metric_stats)
                
                if evaluation_result["triggered"]:
                    await self._create_alert_from_evaluation(rule, evaluation_result)
        
        except Exception as e:
            logger.error(f"Failed to evaluate alerts for metric {metric_name}: {e}")

    async def _create_alert_from_evaluation(self, rule: AlertRule, evaluation: Dict[str, Any]) -> None:
        """Create alert from rule evaluation."""
        try:
            # Check if similar alert already exists
            existing_alert = self._find_existing_alert(rule.id, evaluation["metric_value"])
            
            if existing_alert:
                logger.debug(f"Similar alert already exists for rule {rule.name}")
                return
            
            # Create new alert
            alert = Alert(
                rule_id=rule.id,
                rule_name=rule.name,
                metric_name=rule.metric_name,
                severity=rule.severity,
                trigger_value=evaluation["metric_value"],
                trigger_condition=evaluation["condition"],
                message=f"Alert triggered: {rule.name} - {evaluation['reason']}",
                context=evaluation
            )
            
            # Store alert
            self.active_alerts[alert.id] = alert
            self.system_metrics["active_alerts_count"] += 1
            
            # Send notifications
            if self.notification_service and rule.notification_channels:
                await self._send_alert_notifications(alert, rule.notification_channels)
            
            logger.info(f"Created alert: {alert.id} for rule {rule.name}")
            
        except Exception as e:
            logger.error(f"Failed to create alert from evaluation: {e}")

    def _find_existing_alert(self, rule_id: str, trigger_value: Union[int, float]) -> Optional[Alert]:
        """Find existing similar alert."""
        # Look for active alerts from the same rule within last 5 minutes
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        
        for alert in self.active_alerts.values():
            if (alert.rule_id == rule_id and 
                alert.status == AlertStatus.ACTIVE and
                alert.triggered_at > cutoff_time):
                return alert
        
        return None

    async def _send_alert_notifications(self, alert: Alert, channels: List[str]) -> None:
        """Send alert notifications to configured channels."""
        if not self.notification_service:
            return
        
        try:
            notification_data = {
                "alert_id": alert.id,
                "severity": alert.severity.value,
                "message": alert.message,
                "metric_name": alert.metric_name,
                "trigger_value": alert.trigger_value,
                "triggered_at": alert.triggered_at.isoformat()
            }
            
            for channel in channels:
                await self.notification_service.send_notification(
                    channel_type=channel,
                    recipient="alert-recipients",
                    subject=f"Alert: {alert.rule_name}",
                    message=alert.message,
                    data=notification_data
                )
                
        except Exception as e:
            logger.error(f"Failed to send alert notifications: {e}")

    def _check_dashboard_access(self, dashboard: Dashboard, user_id: str) -> bool:
        """Check if user has access to dashboard."""
        if dashboard.visibility == "public":
            return True
        
        if dashboard.owner == user_id:
            return True
        
        if user_id in dashboard.shared_with:
            return True
        
        # Additional team/role-based access checks would go here
        return False

    def _get_dashboard_widget_data(self, dashboard: Dashboard) -> Dict[str, Any]:
        """Get real-time data for dashboard widgets."""
        widget_data = {}
        
        for widget in dashboard.widgets:
            widget_id = widget["id"]
            widget_type = widget["type"]
            config = widget.get("config", {})
            
            try:
                if widget_type == "metric_chart":
                    widget_data[widget_id] = self._get_metric_chart_data(config)
                elif widget_type == "alert_summary":
                    widget_data[widget_id] = self._get_alert_summary_data(config)
                elif widget_type == "system_status":
                    widget_data[widget_id] = self._get_system_status_data(config)
                elif widget_type == "metric_value":
                    widget_data[widget_id] = self._get_metric_value_data(config)
                
            except Exception as e:
                logger.error(f"Failed to get data for widget {widget_id}: {e}")
                widget_data[widget_id] = {"error": str(e)}
        
        return widget_data

    def _get_metric_chart_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get data for metric chart widget."""
        metric_name = config.get("metric_name")
        time_range = config.get("time_range", {"last": "1h"})
        
        if not metric_name or metric_name not in self.metrics:
            return {"error": "Metric not found"}
        
        metric = self.metrics[metric_name]
        
        # Calculate time range
        end_time = datetime.now(timezone.utc)
        if "last" in time_range:
            duration_str = time_range["last"]
            if duration_str.endswith("h"):
                hours = int(duration_str[:-1])
                start_time = end_time - timedelta(hours=hours)
            elif duration_str.endswith("m"):
                minutes = int(duration_str[:-1])
                start_time = end_time - timedelta(minutes=minutes)
            else:
                start_time = end_time - timedelta(hours=1)
        else:
            start_time = end_time - timedelta(hours=1)
        
        # Get data points
        data_points = metric.get_data_points(start_time, end_time)
        
        chart_data = {
            "labels": [dp.timestamp.isoformat() for dp in data_points],
            "values": [dp.value for dp in data_points],
            "metric_name": metric_name,
            "unit": metric.unit,
            "data_count": len(data_points)
        }
        
        return chart_data

    def _get_alert_summary_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get data for alert summary widget."""
        active_alerts = [a for a in self.active_alerts.values() if a.status == AlertStatus.ACTIVE]
        
        severity_counts = {
            "critical": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
            "high": len([a for a in active_alerts if a.severity == AlertSeverity.HIGH]),
            "medium": len([a for a in active_alerts if a.severity == AlertSeverity.MEDIUM]),
            "low": len([a for a in active_alerts if a.severity == AlertSeverity.LOW])
        }
        
        # Recent alerts (last 24 hours)
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_alerts = [
            a for a in self.active_alerts.values()
            if a.triggered_at > cutoff_time
        ]
        
        return {
            "active_alerts": len(active_alerts),
            "severity_breakdown": severity_counts,
            "recent_alerts": len(recent_alerts),
            "latest_alerts": [a.to_dict() for a in sorted(recent_alerts, key=lambda x: x.triggered_at, reverse=True)[:5]]
        }

    def _get_system_status_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get data for system status widget."""
        # This would integrate with actual system monitoring
        return {
            "status": "healthy",
            "uptime": (datetime.now(timezone.utc) - self.system_metrics["service_started_at"]).total_seconds(),
            "metrics_count": self.system_metrics["total_metrics"],
            "alerts_count": len([a for a in self.active_alerts.values() if a.status == AlertStatus.ACTIVE])
        }

    def _get_metric_value_data(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get data for single metric value widget."""
        metric_name = config.get("metric_name")
        
        if not metric_name or metric_name not in self.metrics:
            return {"error": "Metric not found"}
        
        metric = self.metrics[metric_name]
        current_value = metric.get_current_value()
        
        # Get trend (comparison with previous value)
        data_points = metric.get_data_points()
        trend = "stable"
        if len(data_points) >= 2:
            current = data_points[-1].value
            previous = data_points[-2].value
            if current > previous * 1.1:
                trend = "up"
            elif current < previous * 0.9:
                trend = "down"
        
        return {
            "value": current_value,
            "unit": metric.unit,
            "trend": trend,
            "last_updated": metric.updated_at.isoformat()
        }

    def _get_component_health(self) -> Dict[str, Any]:
        """Get health status of system components."""
        # This would check actual component health
        components = {
            "monitoring_service": "healthy",
            "alert_engine": "healthy" if self.alert_engine else "unknown",
            "notification_service": "healthy" if self.notification_service else "unknown",
            "metrics_storage": "healthy",
            "dashboard_service": "healthy"
        }
        
        return components

    def _get_recent_metrics_activity(self) -> Dict[str, Any]:
        """Get recent metrics activity summary."""
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)
        
        recent_data_points = 0
        active_metrics = 0
        
        for metric in self.metrics.values():
            recent_points = metric.get_data_points(hour_ago, now)
            recent_data_points += len(recent_points)
            if len(recent_points) > 0:
                active_metrics += 1
        
        return {
            "recent_data_points": recent_data_points,
            "active_metrics": active_metrics,
            "data_rate_per_minute": recent_data_points / 60 if recent_data_points > 0 else 0
        }

    def _generate_health_recommendations(self, system_status: str, 
                                       alert_breakdown: Dict[str, int]) -> List[str]:
        """Generate health recommendations."""
        recommendations = []
        
        if system_status == "critical":
            recommendations.append("Immediate attention required: Critical alerts are active")
        
        if alert_breakdown["high"] > 3:
            recommendations.append("Review and address high-severity alerts")
        
        if alert_breakdown["medium"] > 10:
            recommendations.append("Consider tuning alert thresholds to reduce noise")
        
        active_metrics = len([m for m in self.metrics.values() if m.get_current_value() is not None])
        if active_metrics < self.system_metrics["total_metrics"] * 0.8:
            recommendations.append("Some metrics are not receiving data - check data collection")
        
        if len(self.dashboards) == 0:
            recommendations.append("Create dashboards for better visibility into system health")
        
        return recommendations

    @require_permission(Permission.MANAGE_MONITORING)
    def delete_metric(self, metric_name: str) -> Dict[str, Any]:
        """Delete metric and all its data."""
        try:
            if metric_name not in self.metrics:
                return {"success": False, "message": "Metric not found"}
            
            # Remove metric
            del self.metrics[metric_name]
            self.system_metrics["total_metrics"] -= 1
            
            # Remove associated alert rules
            rules_to_remove = [r.id for r in self.alert_rules.values() if r.metric_name == metric_name]
            for rule_id in rules_to_remove:
                del self.alert_rules[rule_id]
                self.system_metrics["total_alert_rules"] -= 1
            
            logger.info(f"Deleted metric: {metric_name}")
            
            return {"success": True, "message": "Metric deleted successfully"}
            
        except Exception as e:
            logger.error(f"Failed to delete metric: {e}")
            return {"success": False, "message": f"Failed to delete metric: {str(e)}"}

    def get_service_statistics(self) -> Dict[str, Any]:
        """Get monitoring service statistics."""
        return {
            **self.system_metrics,
            "alert_engine_stats": self.alert_engine.get_statistics() if self.alert_engine else {},
            "notification_stats": self.notification_service.get_statistics() if self.notification_service else {}
        }