"""
Advanced Alert Engine.

Intelligent alerting engine with anomaly detection, correlation analysis,
escalation management, and smart notification routing.
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
import uuid
import statistics

from domain.entities.monitoring_entity import (
    AlertRule, Alert, AlertSeverity, AlertStatus, 
    AnomalyDetectionMethod, NotificationChannel
)
from infrastructure.services.notification_service import NotificationService
from infrastructure.logging.structured_logging import get_logger, log_context
from infrastructure.performance.monitoring import performance_monitor


logger = get_logger(__name__)


class AlertEngine:
    """Advanced intelligent alert engine."""
    
    def __init__(self, notification_service: NotificationService = None,
                 max_workers: int = 10):
        self.notification_service = notification_service
        self.max_workers = max_workers
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Alert rules and active alerts
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        
        # Alert correlation and grouping
        self.correlation_rules: List[Dict[str, Any]] = []
        self.alert_groups: Dict[str, List[str]] = {}  # group_id -> alert_ids
        
        # Notification channels
        self.notification_channels: Dict[str, Dict[str, Any]] = {}
        
        # Escalation policies
        self.escalation_policies: Dict[str, Dict[str, Any]] = {}
        
        # Engine statistics
        self.engine_stats = {
            "total_evaluations": 0,
            "alerts_triggered": 0,
            "alerts_suppressed": 0,
            "notifications_sent": 0,
            "correlation_matches": 0,
            "false_positive_rate": 0.0
        }
        
        # Anomaly detection models
        self.anomaly_models: Dict[str, Dict[str, Any]] = {}
        
        # Alert suppression tracking
        self.suppression_tracker: Dict[str, datetime] = {}
        
        # Background tasks
        self._correlation_task = None
        self._cleanup_task = None
        self._health_check_task = None
        
        # Initialize built-in correlation rules
        self._initialize_correlation_rules()

    def _initialize_correlation_rules(self) -> None:
        """Initialize built-in alert correlation rules."""
        self.correlation_rules = [
            {
                "id": "temporal_correlation",
                "name": "Temporal Correlation",
                "description": "Group alerts that occur within time window",
                "type": "temporal",
                "parameters": {
                    "time_window_minutes": 5,
                    "min_alerts": 2
                }
            },
            {
                "id": "metric_correlation",
                "name": "Metric Correlation",
                "description": "Group alerts from related metrics",
                "type": "metric_based",
                "parameters": {
                    "correlation_threshold": 0.8
                }
            },
            {
                "id": "cascade_correlation",
                "name": "Cascade Correlation", 
                "description": "Group alerts that follow dependency chain",
                "type": "dependency",
                "parameters": {
                    "dependency_depth": 3
                }
            }
        ]

    def register_alert_rule(self, alert_rule: AlertRule) -> None:
        """Register alert rule with the engine."""
        self.alert_rules[alert_rule.id] = alert_rule
        
        # Initialize anomaly detection model if needed
        if alert_rule.condition.get("type") == "anomaly":
            self._initialize_anomaly_model(alert_rule)
        
        logger.info(f"Registered alert rule: {alert_rule.name}")

    def unregister_alert_rule(self, rule_id: str) -> None:
        """Unregister alert rule from the engine."""
        if rule_id in self.alert_rules:
            rule = self.alert_rules.pop(rule_id)
            
            # Clean up anomaly model
            if rule_id in self.anomaly_models:
                del self.anomaly_models[rule_id]
            
            logger.info(f"Unregistered alert rule: {rule.name}")

    def update_alert_rule(self, alert_rule: AlertRule) -> None:
        """Update existing alert rule."""
        if alert_rule.id in self.alert_rules:
            self.alert_rules[alert_rule.id] = alert_rule
            
            # Update anomaly model if needed
            if alert_rule.condition.get("type") == "anomaly":
                self._initialize_anomaly_model(alert_rule)
            
            logger.info(f"Updated alert rule: {alert_rule.name}")

    @performance_monitor("evaluate_alerts")
    async def evaluate_alerts(self, metric_name: str, metric_value: float,
                            metric_stats: Dict[str, Any] = None,
                            context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Evaluate all relevant alert rules for a metric."""
        with log_context(operation="evaluate_alerts", metric_name=metric_name):
            try:
                relevant_rules = [
                    rule for rule in self.alert_rules.values()
                    if rule.metric_name == metric_name and rule.enabled
                ]
                
                if not relevant_rules:
                    return []
                
                evaluation_results = []
                triggered_alerts = []
                
                for rule in relevant_rules:
                    self.engine_stats["total_evaluations"] += 1
                    
                    # Evaluate rule
                    evaluation_result = rule.evaluate(
                        metric_value, metric_stats or {}, context or {}
                    )
                    
                    evaluation_results.append(evaluation_result)
                    
                    if evaluation_result["triggered"]:
                        # Create alert
                        alert = await self._create_alert_from_evaluation(rule, evaluation_result)
                        
                        if alert:
                            triggered_alerts.append(alert)
                            self.engine_stats["alerts_triggered"] += 1
                        else:
                            self.engine_stats["alerts_suppressed"] += 1
                
                # Perform alert correlation
                if triggered_alerts:
                    await self._correlate_alerts(triggered_alerts)
                
                return evaluation_results
                
            except Exception as e:
                logger.error(f"Failed to evaluate alerts: {e}")
                return []

    async def _create_alert_from_evaluation(self, rule: AlertRule, 
                                          evaluation: Dict[str, Any]) -> Optional[Alert]:
        """Create alert from rule evaluation."""
        try:
            # Check for duplicate alerts
            if self._is_duplicate_alert(rule.id, evaluation):
                logger.debug(f"Suppressing duplicate alert for rule: {rule.name}")
                return None
            
            # Check suppression conditions
            if self._is_alert_suppressed(rule, evaluation):
                logger.debug(f"Alert suppressed for rule: {rule.name}")
                return None
            
            # Create alert
            alert = Alert(
                rule_id=rule.id,
                rule_name=rule.name,
                metric_name=rule.metric_name,
                severity=rule.severity,
                trigger_value=evaluation["metric_value"],
                trigger_condition=evaluation["condition"],
                message=self._generate_alert_message(rule, evaluation),
                context=evaluation
            )
            
            # Add to active alerts
            self.active_alerts[alert.id] = alert
            
            # Add to history
            self.alert_history.append({
                "alert_id": alert.id,
                "rule_id": rule.id,
                "metric_name": rule.metric_name,
                "severity": rule.severity.value,
                "triggered_at": alert.triggered_at.isoformat(),
                "trigger_value": alert.trigger_value
            })
            
            # Send notifications
            await self._send_alert_notifications(alert, rule)
            
            logger.info(f"Created alert: {alert.id} for rule: {rule.name}")
            
            return alert
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return None

    def _is_duplicate_alert(self, rule_id: str, evaluation: Dict[str, Any]) -> bool:
        """Check if alert is a duplicate."""
        # Look for active alerts from same rule in last 5 minutes
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        
        for alert in self.active_alerts.values():
            if (alert.rule_id == rule_id and 
                alert.status == AlertStatus.ACTIVE and
                alert.triggered_at > cutoff_time):
                return True
        
        return False

    def _is_alert_suppressed(self, rule: AlertRule, evaluation: Dict[str, Any]) -> bool:
        """Check if alert should be suppressed."""
        # Check maintenance windows
        if self._is_in_maintenance_window():
            return True
        
        # Check rule-specific suppression
        for suppression in rule.suppression_conditions:
            if self._evaluate_suppression_condition(suppression, evaluation):
                return True
        
        # Check global suppression rules
        return self._check_global_suppression(rule, evaluation)

    def _is_in_maintenance_window(self) -> bool:
        """Check if system is in maintenance window."""
        # This would check configured maintenance windows
        # For now, return False (no maintenance)
        return False

    def _evaluate_suppression_condition(self, suppression: Dict[str, Any], 
                                      evaluation: Dict[str, Any]) -> bool:
        """Evaluate suppression condition."""
        condition_type = suppression.get("type", "value")
        
        if condition_type == "value":
            field = suppression.get("field", "metric_value")
            operator = suppression.get("operator", "lt")
            threshold = suppression.get("value", 0)
            
            field_value = evaluation.get(field, 0)
            
            if operator == "lt" and field_value < threshold:
                return True
            elif operator == "gt" and field_value > threshold:
                return True
            elif operator == "eq" and field_value == threshold:
                return True
        
        elif condition_type == "time":
            # Time-based suppression
            start_time = suppression.get("start_time")
            end_time = suppression.get("end_time")
            
            if start_time and end_time:
                now = datetime.now(timezone.utc).time()
                start = datetime.strptime(start_time, "%H:%M").time()
                end = datetime.strptime(end_time, "%H:%M").time()
                
                if start <= now <= end:
                    return True
        
        return False

    def _check_global_suppression(self, rule: AlertRule, evaluation: Dict[str, Any]) -> bool:
        """Check global suppression rules."""
        # Global suppression based on alert volume
        recent_alerts = self._get_recent_alerts(minutes=10)
        
        # Suppress if too many alerts in short time
        if len(recent_alerts) > 50:
            return True
        
        # Suppress low-severity alerts if system is under stress
        if (rule.severity in [AlertSeverity.LOW, AlertSeverity.MEDIUM] and 
            len(recent_alerts) > 20):
            return True
        
        return False

    def _generate_alert_message(self, rule: AlertRule, evaluation: Dict[str, Any]) -> str:
        """Generate alert message."""
        template = rule.condition.get("message_template", 
                                    "{rule_name}: {metric_name} is {trigger_value}")
        
        message = template.format(
            rule_name=rule.name,
            metric_name=rule.metric_name,
            trigger_value=evaluation["metric_value"],
            condition=evaluation["condition"],
            reason=evaluation.get("reason", "")
        )
        
        return message

    async def _send_alert_notifications(self, alert: Alert, rule: AlertRule) -> None:
        """Send alert notifications through configured channels."""
        if not rule.notification_channels or not self.notification_service:
            return
        
        try:
            notification_data = {
                "alert_id": alert.id,
                "rule_id": rule.id,
                "rule_name": rule.name,
                "metric_name": alert.metric_name,
                "severity": alert.severity.value,
                "trigger_value": alert.trigger_value,
                "condition": alert.trigger_condition,
                "message": alert.message,
                "triggered_at": alert.triggered_at.isoformat(),
                "dashboard_url": self._generate_dashboard_url(alert)
            }
            
            # Send to each configured channel
            for channel in rule.notification_channels:
                if channel in self.notification_channels:
                    channel_config = self.notification_channels[channel]
                    
                    await self.notification_service.send_notification(
                        channel_type=channel_config["type"],
                        recipient=channel_config["recipient"],
                        subject=f"[{alert.severity.value.upper()}] {alert.rule_name}",
                        message=alert.message,
                        data=notification_data
                    )
                    
                    self.engine_stats["notifications_sent"] += 1
            
            # Handle escalation if configured
            if rule.escalation_policy:
                await self._handle_escalation(alert, rule.escalation_policy)
                
        except Exception as e:
            logger.error(f"Failed to send alert notifications: {e}")

    def _generate_dashboard_url(self, alert: Alert) -> str:
        """Generate dashboard URL for alert context."""
        # This would generate a URL to a dashboard showing the alert context
        return f"/dashboards/alert/{alert.id}"

    async def _handle_escalation(self, alert: Alert, escalation_policy: Dict[str, Any]) -> None:
        """Handle alert escalation."""
        try:
            escalation_levels = escalation_policy.get("levels", [])
            
            for level in escalation_levels:
                wait_minutes = level.get("wait_minutes", 15)
                channels = level.get("channels", [])
                
                # Schedule escalation
                asyncio.create_task(
                    self._schedule_escalation(alert.id, wait_minutes, channels)
                )
                
        except Exception as e:
            logger.error(f"Failed to handle escalation: {e}")

    async def _schedule_escalation(self, alert_id: str, wait_minutes: int, 
                                 channels: List[str]) -> None:
        """Schedule alert escalation."""
        await asyncio.sleep(wait_minutes * 60)
        
        # Check if alert is still active and unacknowledged
        if (alert_id in self.active_alerts and 
            self.active_alerts[alert_id].status == AlertStatus.ACTIVE):
            
            alert = self.active_alerts[alert_id]
            
            # Send escalation notifications
            if self.notification_service:
                escalation_message = f"ESCALATION: {alert.message} (Unresolved for {wait_minutes} minutes)"
                
                for channel in channels:
                    if channel in self.notification_channels:
                        channel_config = self.notification_channels[channel]
                        
                        await self.notification_service.send_notification(
                            channel_type=channel_config["type"],
                            recipient=channel_config["recipient"],
                            subject=f"[ESCALATION] {alert.rule_name}",
                            message=escalation_message,
                            data={"alert_id": alert_id, "escalation": True}
                        )

    async def _correlate_alerts(self, alerts: List[Alert]) -> None:
        """Perform alert correlation analysis."""
        try:
            if len(alerts) < 2:
                return
            
            for correlation_rule in self.correlation_rules:
                correlation_type = correlation_rule["type"]
                
                if correlation_type == "temporal":
                    await self._temporal_correlation(alerts, correlation_rule)
                elif correlation_type == "metric_based":
                    await self._metric_correlation(alerts, correlation_rule)
                elif correlation_type == "dependency":
                    await self._dependency_correlation(alerts, correlation_rule)
                    
        except Exception as e:
            logger.error(f"Failed to correlate alerts: {e}")

    async def _temporal_correlation(self, alerts: List[Alert], rule: Dict[str, Any]) -> None:
        """Perform temporal alert correlation."""
        time_window = rule["parameters"]["time_window_minutes"]
        min_alerts = rule["parameters"]["min_alerts"]
        
        # Group alerts by time window
        time_groups = defaultdict(list)
        base_time = datetime.now(timezone.utc)
        
        for alert in alerts:
            # Calculate time bucket
            minutes_ago = int((base_time - alert.triggered_at).total_seconds() / 60)
            bucket = minutes_ago // time_window
            time_groups[bucket].append(alert)
        
        # Create correlation groups for buckets with enough alerts
        for bucket, bucket_alerts in time_groups.items():
            if len(bucket_alerts) >= min_alerts:
                group_id = f"temporal_{bucket}_{int(time.time())}"
                self.alert_groups[group_id] = [a.id for a in bucket_alerts]
                self.engine_stats["correlation_matches"] += 1
                
                logger.info(f"Created temporal correlation group: {group_id} with {len(bucket_alerts)} alerts")

    async def _metric_correlation(self, alerts: List[Alert], rule: Dict[str, Any]) -> None:
        """Perform metric-based alert correlation."""
        correlation_threshold = rule["parameters"]["correlation_threshold"]
        
        # Group alerts by metric patterns
        metric_groups = defaultdict(list)
        
        for alert in alerts:
            # Simple metric name similarity
            metric_base = alert.metric_name.split('.')[0]  # e.g., "system" from "system.cpu.usage"
            metric_groups[metric_base].append(alert)
        
        # Create correlation groups
        for metric_base, metric_alerts in metric_groups.items():
            if len(metric_alerts) >= 2:
                group_id = f"metric_{metric_base}_{int(time.time())}"
                self.alert_groups[group_id] = [a.id for a in metric_alerts]
                self.engine_stats["correlation_matches"] += 1
                
                logger.info(f"Created metric correlation group: {group_id} with {len(metric_alerts)} alerts")

    async def _dependency_correlation(self, alerts: List[Alert], rule: Dict[str, Any]) -> None:
        """Perform dependency-based alert correlation."""
        # This would use service dependency mapping
        # For now, implement simple service-based grouping
        
        service_groups = defaultdict(list)
        
        for alert in alerts:
            # Extract service from metric name or context
            service_name = alert.context.get("service", "unknown")
            if service_name == "unknown":
                # Try to extract from metric name
                parts = alert.metric_name.split('.')
                if len(parts) > 1:
                    service_name = parts[1]  # e.g., "api" from "application.api.response_time"
            
            service_groups[service_name].append(alert)
        
        # Create dependency groups
        for service, service_alerts in service_groups.items():
            if len(service_alerts) >= 2:
                group_id = f"dependency_{service}_{int(time.time())}"
                self.alert_groups[group_id] = [a.id for a in service_alerts]
                self.engine_stats["correlation_matches"] += 1
                
                logger.info(f"Created dependency correlation group: {group_id} with {len(service_alerts)} alerts")

    def _initialize_anomaly_model(self, alert_rule: AlertRule) -> None:
        """Initialize anomaly detection model for alert rule."""
        model_config = {
            "rule_id": alert_rule.id,
            "method": alert_rule.condition.get("detection_method", "statistical"),
            "sensitivity": alert_rule.condition.get("sensitivity", 0.8),
            "lookback_points": alert_rule.condition.get("lookback_points", 100),
            "baseline_data": deque(maxlen=1000),
            "model_parameters": {}
        }
        
        self.anomaly_models[alert_rule.id] = model_config
        logger.info(f"Initialized anomaly model for rule: {alert_rule.name}")

    def update_alert_status(self, alert_id: str, new_status: AlertStatus) -> bool:
        """Update alert status."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = new_status
            
            if new_status in [AlertStatus.RESOLVED, AlertStatus.SUPPRESSED]:
                # Move to history and remove from active
                self.alert_history.append({
                    "alert_id": alert.id,
                    "rule_id": alert.rule_id,
                    "resolved_at": datetime.now(timezone.utc).isoformat(),
                    "status": new_status.value
                })
            
            return True
        
        return False

    def register_notification_channel(self, channel_id: str, config: Dict[str, Any]) -> None:
        """Register notification channel."""
        self.notification_channels[channel_id] = config
        logger.info(f"Registered notification channel: {channel_id}")

    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active alerts with optional severity filter."""
        alerts = [a for a in self.active_alerts.values() if a.status == AlertStatus.ACTIVE]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return sorted(alerts, key=lambda x: x.triggered_at, reverse=True)

    def get_alert_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics for time period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Filter recent alerts from history
        recent_alerts = [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert["triggered_at"]) > cutoff_time
        ]
        
        # Calculate statistics
        total_alerts = len(recent_alerts)
        severity_breakdown = defaultdict(int)
        metric_breakdown = defaultdict(int)
        
        for alert in recent_alerts:
            severity_breakdown[alert["severity"]] += 1
            metric_breakdown[alert["metric_name"]] += 1
        
        # Calculate rates
        active_alerts = len([a for a in self.active_alerts.values() if a.status == AlertStatus.ACTIVE])
        resolved_alerts = len([a for a in recent_alerts if "resolved_at" in a])
        
        mttr = 0  # Mean Time To Resolution
        if resolved_alerts > 0:
            resolution_times = []
            for alert in recent_alerts:
                if "resolved_at" in alert:
                    triggered = datetime.fromisoformat(alert["triggered_at"])
                    resolved = datetime.fromisoformat(alert["resolved_at"])
                    resolution_times.append((resolved - triggered).total_seconds())
            
            if resolution_times:
                mttr = statistics.mean(resolution_times) / 60  # Convert to minutes
        
        return {
            "time_period_hours": hours,
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "resolved_alerts": resolved_alerts,
            "severity_breakdown": dict(severity_breakdown),
            "top_metrics": dict(sorted(metric_breakdown.items(), key=lambda x: x[1], reverse=True)[:10]),
            "mean_time_to_resolution_minutes": round(mttr, 2),
            "alert_rate_per_hour": total_alerts / hours if hours > 0 else 0,
            "correlation_groups": len(self.alert_groups),
            "false_positive_rate": self.engine_stats["false_positive_rate"]
        }

    def _get_recent_alerts(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get alerts from recent time period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        
        recent = []
        for alert in self.alert_history:
            if datetime.fromisoformat(alert["triggered_at"]) > cutoff_time:
                recent.append(alert)
        
        return recent

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive engine statistics."""
        return {
            **self.engine_stats,
            "registered_rules": len(self.alert_rules),
            "active_alerts": len([a for a in self.active_alerts.values() if a.status == AlertStatus.ACTIVE]),
            "notification_channels": len(self.notification_channels),
            "correlation_groups": len(self.alert_groups),
            "anomaly_models": len(self.anomaly_models),
            "alert_history_size": len(self.alert_history)
        }

    def cleanup_old_data(self, days: int = 7) -> int:
        """Clean up old alert data."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        cleanup_count = 0
        
        # Clean up resolved/expired alerts
        alerts_to_remove = []
        for alert_id, alert in self.active_alerts.items():
            if (alert.status in [AlertStatus.RESOLVED, AlertStatus.EXPIRED] and
                alert.triggered_at < cutoff_time):
                alerts_to_remove.append(alert_id)
        
        for alert_id in alerts_to_remove:
            del self.active_alerts[alert_id]
            cleanup_count += 1
        
        # Clean up old correlation groups
        groups_to_remove = []
        for group_id in self.alert_groups:
            # Remove groups with no active alerts
            active_alerts_in_group = [
                aid for aid in self.alert_groups[group_id]
                if aid in self.active_alerts
            ]
            if not active_alerts_in_group:
                groups_to_remove.append(group_id)
        
        for group_id in groups_to_remove:
            del self.alert_groups[group_id]
        
        logger.info(f"Cleaned up {cleanup_count} old alerts and {len(groups_to_remove)} correlation groups")
        return cleanup_count

    async def shutdown(self) -> None:
        """Shutdown alert engine gracefully."""
        logger.info("Shutting down alert engine...")
        
        # Cancel background tasks
        if self._correlation_task:
            self._correlation_task.cancel()
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        if self._health_check_task:
            self._health_check_task.cancel()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("Alert engine shutdown complete")