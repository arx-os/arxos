"""
Monitoring and Alerting Domain Entities.

Domain models for comprehensive monitoring, alerting, and observability
including metrics, alerts, dashboards, and system health tracking.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timezone, timedelta
from enum import Enum
import json
import statistics

from infrastructure.logging.structured_logging import get_logger


logger = get_logger(__name__)


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"
    PERCENTAGE = "percentage"


class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(Enum):
    """Alert status values."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    EXPIRED = "expired"


class NotificationChannel(Enum):
    """Notification channel types."""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    WEBHOOK = "webhook"
    PAGERDUTY = "pagerduty"
    TEAMS = "teams"
    DISCORD = "discord"


class DashboardType(Enum):
    """Dashboard types."""
    SYSTEM_HEALTH = "system_health"
    PERFORMANCE = "performance"
    BUSINESS_METRICS = "business_metrics"
    SECURITY = "security"
    CUSTOM = "custom"


class AnomalyDetectionMethod(Enum):
    """Anomaly detection methods."""
    STATISTICAL = "statistical"
    MACHINE_LEARNING = "machine_learning"
    THRESHOLD = "threshold"
    SEASONAL = "seasonal"
    TREND = "trend"


@dataclass
class MetricDataPoint:
    """Individual metric data point."""
    timestamp: datetime
    value: Union[int, float]
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "tags": self.tags,
            "metadata": self.metadata
        }


@dataclass
class Metric:
    """Metric definition and data storage."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    metric_type: MetricType = MetricType.GAUGE
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    # Data retention
    retention_days: int = 30
    resolution_seconds: int = 60
    
    # Aggregation settings
    aggregation_method: str = "avg"  # avg, sum, min, max, count
    
    # Data points storage
    data_points: List[MetricDataPoint] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = ""
    
    # Statistics cache
    _stats_cache: Dict[str, Any] = field(default_factory=dict, init=False)
    _cache_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc), init=False)

    def add_data_point(self, value: Union[int, float], 
                      timestamp: datetime = None,
                      tags: Dict[str, str] = None,
                      metadata: Dict[str, Any] = None) -> None:
        """Add new data point."""
        data_point = MetricDataPoint(
            timestamp=timestamp or datetime.now(timezone.utc),
            value=value,
            tags=tags or {},
            metadata=metadata or {}
        )
        
        self.data_points.append(data_point)
        self.updated_at = datetime.now(timezone.utc)
        
        # Clear cache when new data is added
        self._stats_cache.clear()
        
        # Clean old data points based on retention policy
        self._cleanup_old_data()

    def get_data_points(self, start_time: datetime = None,
                       end_time: datetime = None,
                       tags_filter: Dict[str, str] = None) -> List[MetricDataPoint]:
        """Get data points with optional filtering."""
        filtered_points = self.data_points
        
        # Filter by time range
        if start_time:
            filtered_points = [p for p in filtered_points if p.timestamp >= start_time]
        
        if end_time:
            filtered_points = [p for p in filtered_points if p.timestamp <= end_time]
        
        # Filter by tags
        if tags_filter:
            def matches_tags(point):
                return all(point.tags.get(k) == v for k, v in tags_filter.items())
            filtered_points = [p for p in filtered_points if matches_tags(p)]
        
        return sorted(filtered_points, key=lambda x: x.timestamp)

    def get_current_value(self) -> Optional[Union[int, float]]:
        """Get current metric value."""
        if not self.data_points:
            return None
        
        # Sort by timestamp and return latest
        sorted_points = sorted(self.data_points, key=lambda x: x.timestamp, reverse=True)
        return sorted_points[0].value

    def get_statistics(self, start_time: datetime = None,
                      end_time: datetime = None) -> Dict[str, Any]:
        """Get metric statistics for time range."""
        cache_key = f"{start_time}_{end_time}"
        
        # Check cache
        if (cache_key in self._stats_cache and 
            (datetime.now(timezone.utc) - self._cache_timestamp).total_seconds() < 300):
            return self._stats_cache[cache_key]
        
        data_points = self.get_data_points(start_time, end_time)
        
        if not data_points:
            return {"count": 0, "message": "No data points in range"}
        
        values = [p.value for p in data_points]
        
        stats = {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "current": data_points[-1].value if data_points else None,
            "first_timestamp": data_points[0].timestamp.isoformat(),
            "last_timestamp": data_points[-1].timestamp.isoformat()
        }
        
        # Add additional statistics for sufficient data
        if len(values) > 1:
            stats["std_dev"] = statistics.stdev(values)
            stats["variance"] = statistics.variance(values)
        
        if len(values) >= 3:
            stats["median"] = statistics.median(values)
            stats["mode"] = statistics.mode(values) if len(set(values)) < len(values) else None
        
        # Cache results
        self._stats_cache[cache_key] = stats
        self._cache_timestamp = datetime.now(timezone.utc)
        
        return stats

    def detect_anomalies(self, method: AnomalyDetectionMethod = AnomalyDetectionMethod.STATISTICAL,
                        lookback_points: int = 100) -> List[Dict[str, Any]]:
        """Detect anomalies in metric data."""
        if len(self.data_points) < 10:
            return []  # Need minimum data for anomaly detection
        
        recent_points = sorted(self.data_points, key=lambda x: x.timestamp)[-lookback_points:]
        anomalies = []
        
        if method == AnomalyDetectionMethod.STATISTICAL:
            anomalies = self._detect_statistical_anomalies(recent_points)
        elif method == AnomalyDetectionMethod.THRESHOLD:
            anomalies = self._detect_threshold_anomalies(recent_points)
        elif method == AnomalyDetectionMethod.TREND:
            anomalies = self._detect_trend_anomalies(recent_points)
        
        return anomalies

    def _detect_statistical_anomalies(self, data_points: List[MetricDataPoint]) -> List[Dict[str, Any]]:
        """Detect statistical anomalies using z-score."""
        if len(data_points) < 5:
            return []
        
        values = [p.value for p in data_points]
        mean_val = statistics.mean(values)
        
        try:
            std_dev = statistics.stdev(values)
        except statistics.StatisticsError:
            return []  # All values are the same
        
        anomalies = []
        threshold = 2.5  # Z-score threshold
        
        for point in data_points[-10:]:  # Check last 10 points
            if std_dev > 0:
                z_score = abs(point.value - mean_val) / std_dev
                if z_score > threshold:
                    anomalies.append({
                        "timestamp": point.timestamp.isoformat(),
                        "value": point.value,
                        "z_score": z_score,
                        "mean": mean_val,
                        "std_dev": std_dev,
                        "type": "statistical",
                        "severity": "high" if z_score > 3 else "medium"
                    })
        
        return anomalies

    def _detect_threshold_anomalies(self, data_points: List[MetricDataPoint]) -> List[Dict[str, Any]]:
        """Detect threshold-based anomalies."""
        # This would be configured based on metric-specific thresholds
        # For now, using dynamic thresholds based on historical data
        
        if len(data_points) < 10:
            return []
        
        values = [p.value for p in data_points[:-5]]  # Historical values
        recent_values = [p.value for p in data_points[-5:]]  # Recent values
        
        if not values:
            return []
        
        # Dynamic thresholds based on percentiles
        lower_threshold = statistics.quantiles(values, n=100)[4]  # 5th percentile
        upper_threshold = statistics.quantiles(values, n=100)[94]  # 95th percentile
        
        anomalies = []
        for point in data_points[-5:]:
            if point.value < lower_threshold or point.value > upper_threshold:
                anomalies.append({
                    "timestamp": point.timestamp.isoformat(),
                    "value": point.value,
                    "lower_threshold": lower_threshold,
                    "upper_threshold": upper_threshold,
                    "type": "threshold",
                    "severity": "medium"
                })
        
        return anomalies

    def _detect_trend_anomalies(self, data_points: List[MetricDataPoint]) -> List[Dict[str, Any]]:
        """Detect trend-based anomalies."""
        if len(data_points) < 10:
            return []
        
        values = [p.value for p in data_points]
        
        # Calculate trend using linear regression
        n = len(values)
        x_vals = list(range(n))
        
        x_mean = sum(x_vals) / n
        y_mean = sum(values) / n
        
        numerator = sum((x_vals[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)
        
        if denominator == 0:
            return []
        
        slope = numerator / denominator
        
        # Check for sudden trend changes
        recent_slope = self._calculate_recent_slope(data_points[-5:])
        
        anomalies = []
        if abs(recent_slope - slope) > abs(slope * 2):  # Significant trend change
            anomalies.append({
                "timestamp": data_points[-1].timestamp.isoformat(),
                "overall_slope": slope,
                "recent_slope": recent_slope,
                "trend_change": abs(recent_slope - slope),
                "type": "trend",
                "severity": "medium"
            })
        
        return anomalies

    def _calculate_recent_slope(self, data_points: List[MetricDataPoint]) -> float:
        """Calculate slope for recent data points."""
        if len(data_points) < 2:
            return 0
        
        values = [p.value for p in data_points]
        n = len(values)
        x_vals = list(range(n))
        
        x_mean = sum(x_vals) / n
        y_mean = sum(values) / n
        
        numerator = sum((x_vals[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)
        
        return numerator / denominator if denominator != 0 else 0

    def _cleanup_old_data(self) -> None:
        """Remove data points older than retention period."""
        if self.retention_days <= 0:
            return
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        self.data_points = [p for p in self.data_points if p.timestamp >= cutoff_time]

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "metric_type": self.metric_type.value,
            "unit": self.unit,
            "tags": self.tags,
            "retention_days": self.retention_days,
            "resolution_seconds": self.resolution_seconds,
            "aggregation_method": self.aggregation_method,
            "data_points_count": len(self.data_points),
            "current_value": self.get_current_value(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by
        }


@dataclass
class AlertRule:
    """Alert rule definition."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    metric_name: str = ""
    condition: Dict[str, Any] = field(default_factory=dict)
    severity: AlertSeverity = AlertSeverity.MEDIUM
    
    # Alert settings
    enabled: bool = True
    cooldown_minutes: int = 5
    max_alerts_per_hour: int = 10
    
    # Notification settings
    notification_channels: List[str] = field(default_factory=list)
    escalation_policy: Dict[str, Any] = field(default_factory=dict)
    
    # Suppression settings
    suppression_conditions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    # Runtime tracking
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = 0
    last_evaluation_at: Optional[datetime] = None

    def evaluate(self, metric_value: Union[int, float], 
                metric_stats: Dict[str, Any] = None,
                context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate alert rule against metric value."""
        now = datetime.now(timezone.utc)
        self.last_evaluation_at = now
        
        if not self.enabled:
            return {"triggered": False, "reason": "Rule disabled"}
        
        # Check cooldown period
        if self.last_triggered_at and self.cooldown_minutes > 0:
            cooldown_end = self.last_triggered_at + timedelta(minutes=self.cooldown_minutes)
            if now < cooldown_end:
                return {"triggered": False, "reason": "In cooldown period"}
        
        # Check rate limiting
        if self._is_rate_limited():
            return {"triggered": False, "reason": "Rate limited"}
        
        # Check suppression conditions
        if self._is_suppressed(context or {}):
            return {"triggered": False, "reason": "Suppressed"}
        
        # Evaluate condition
        condition_result = self._evaluate_condition(metric_value, metric_stats or {})
        
        evaluation_result = {
            "triggered": condition_result["triggered"],
            "rule_id": self.id,
            "rule_name": self.name,
            "metric_name": self.metric_name,
            "metric_value": metric_value,
            "condition": condition_result["condition"],
            "severity": self.severity.value,
            "evaluated_at": now.isoformat(),
            "reason": condition_result.get("reason", "")
        }
        
        if condition_result["triggered"]:
            self.last_triggered_at = now
            self.trigger_count += 1
            evaluation_result["trigger_count"] = self.trigger_count
        
        return evaluation_result

    def _evaluate_condition(self, value: Union[int, float], 
                          stats: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate the alert condition."""
        condition_type = self.condition.get("type", "threshold")
        
        if condition_type == "threshold":
            return self._evaluate_threshold_condition(value)
        elif condition_type == "anomaly":
            return self._evaluate_anomaly_condition(value, stats)
        elif condition_type == "rate":
            return self._evaluate_rate_condition(value, stats)
        elif condition_type == "missing_data":
            return self._evaluate_missing_data_condition(stats)
        else:
            return {"triggered": False, "reason": f"Unknown condition type: {condition_type}"}

    def _evaluate_threshold_condition(self, value: Union[int, float]) -> Dict[str, Any]:
        """Evaluate threshold-based condition."""
        operator = self.condition.get("operator", "gt")
        threshold = self.condition.get("threshold", 0)
        
        triggered = False
        if operator == "gt" and value > threshold:
            triggered = True
        elif operator == "gte" and value >= threshold:
            triggered = True
        elif operator == "lt" and value < threshold:
            triggered = True
        elif operator == "lte" and value <= threshold:
            triggered = True
        elif operator == "eq" and value == threshold:
            triggered = True
        elif operator == "ne" and value != threshold:
            triggered = True
        
        return {
            "triggered": triggered,
            "condition": f"value {operator} {threshold}",
            "reason": f"Value {value} {operator} {threshold}" if triggered else ""
        }

    def _evaluate_anomaly_condition(self, value: Union[int, float], 
                                  stats: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate anomaly-based condition."""
        if "std_dev" not in stats or "mean" not in stats:
            return {"triggered": False, "reason": "Insufficient statistics for anomaly detection"}
        
        mean_val = stats["mean"]
        std_dev = stats["std_dev"]
        threshold = self.condition.get("z_score_threshold", 2.5)
        
        if std_dev == 0:
            return {"triggered": False, "reason": "No variance in data"}
        
        z_score = abs(value - mean_val) / std_dev
        triggered = z_score > threshold
        
        return {
            "triggered": triggered,
            "condition": f"z_score > {threshold}",
            "reason": f"Z-score {z_score:.2f} exceeds threshold {threshold}" if triggered else "",
            "z_score": z_score
        }

    def _evaluate_rate_condition(self, value: Union[int, float], 
                               stats: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate rate-based condition."""
        # Rate conditions would compare current value to previous values
        # This is a simplified implementation
        
        previous_value = self.condition.get("previous_value", 0)
        rate_threshold = self.condition.get("rate_threshold", 0)
        
        if previous_value == 0:
            return {"triggered": False, "reason": "No previous value for rate calculation"}
        
        rate = (value - previous_value) / previous_value * 100  # Percentage change
        
        operator = self.condition.get("operator", "gt")
        triggered = False
        
        if operator == "gt" and rate > rate_threshold:
            triggered = True
        elif operator == "lt" and rate < rate_threshold:
            triggered = True
        
        return {
            "triggered": triggered,
            "condition": f"rate {operator} {rate_threshold}%",
            "reason": f"Rate {rate:.2f}% {operator} {rate_threshold}%" if triggered else "",
            "rate": rate
        }

    def _evaluate_missing_data_condition(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate missing data condition."""
        max_age_minutes = self.condition.get("max_age_minutes", 10)
        
        if "last_timestamp" not in stats:
            return {"triggered": True, "reason": "No data available"}
        
        last_timestamp = datetime.fromisoformat(stats["last_timestamp"])
        age_minutes = (datetime.now(timezone.utc) - last_timestamp).total_seconds() / 60
        
        triggered = age_minutes > max_age_minutes
        
        return {
            "triggered": triggered,
            "condition": f"data_age > {max_age_minutes} minutes",
            "reason": f"Data is {age_minutes:.1f} minutes old" if triggered else "",
            "data_age_minutes": age_minutes
        }

    def _is_rate_limited(self) -> bool:
        """Check if alert is rate limited."""
        if self.max_alerts_per_hour <= 0:
            return False
        
        # This would typically check a time-windowed counter
        # For now, using simplified logic based on trigger count and time
        
        if not self.last_triggered_at:
            return False
        
        hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        
        # Simplified: if triggered recently and count is high, rate limit
        if (self.last_triggered_at > hour_ago and 
            self.trigger_count >= self.max_alerts_per_hour):
            return True
        
        return False

    def _is_suppressed(self, context: Dict[str, Any]) -> bool:
        """Check if alert should be suppressed."""
        for suppression in self.suppression_conditions:
            if self._evaluate_suppression_condition(suppression, context):
                return True
        return False

    def _evaluate_suppression_condition(self, suppression: Dict[str, Any], 
                                      context: Dict[str, Any]) -> bool:
        """Evaluate individual suppression condition."""
        condition_type = suppression.get("type", "context")
        
        if condition_type == "context":
            field = suppression.get("field")
            operator = suppression.get("operator", "eq")
            value = suppression.get("value")
            
            context_value = context.get(field)
            
            if operator == "eq" and context_value == value:
                return True
            elif operator == "ne" and context_value != value:
                return True
            elif operator == "contains" and value in str(context_value):
                return True
        
        elif condition_type == "time":
            # Time-based suppression (e.g., during maintenance windows)
            start_time = suppression.get("start_time")
            end_time = suppression.get("end_time")
            
            if start_time and end_time:
                now = datetime.now(timezone.utc).time()
                start = datetime.strptime(start_time, "%H:%M").time()
                end = datetime.strptime(end_time, "%H:%M").time()
                
                if start <= now <= end:
                    return True
        
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert rule to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "metric_name": self.metric_name,
            "condition": self.condition,
            "severity": self.severity.value,
            "enabled": self.enabled,
            "cooldown_minutes": self.cooldown_minutes,
            "max_alerts_per_hour": self.max_alerts_per_hour,
            "notification_channels": self.notification_channels,
            "escalation_policy": self.escalation_policy,
            "suppression_conditions": self.suppression_conditions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "tags": self.tags,
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            "trigger_count": self.trigger_count,
            "last_evaluation_at": self.last_evaluation_at.isoformat() if self.last_evaluation_at else None
        }


@dataclass
class Alert:
    """Active alert instance."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    rule_name: str = ""
    metric_name: str = ""
    severity: AlertSeverity = AlertSeverity.MEDIUM
    status: AlertStatus = AlertStatus.ACTIVE
    
    # Alert data
    trigger_value: Union[int, float] = 0
    trigger_condition: str = ""
    message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Assignment and acknowledgment
    assigned_to: Optional[str] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    
    # Metadata
    tags: Dict[str, str] = field(default_factory=dict)
    annotations: List[Dict[str, Any]] = field(default_factory=list)

    def acknowledge(self, acknowledged_by: str, note: str = "") -> None:
        """Acknowledge the alert."""
        if self.status == AlertStatus.ACTIVE:
            self.status = AlertStatus.ACKNOWLEDGED
            self.acknowledged_at = datetime.now(timezone.utc)
            self.acknowledged_by = acknowledged_by
            
            if note:
                self.add_annotation("acknowledgment", note, acknowledged_by)

    def resolve(self, resolved_by: str, note: str = "") -> None:
        """Resolve the alert."""
        if self.status in [AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]:
            self.status = AlertStatus.RESOLVED
            self.resolved_at = datetime.now(timezone.utc)
            self.resolved_by = resolved_by
            
            if note:
                self.add_annotation("resolution", note, resolved_by)

    def suppress(self, reason: str = "") -> None:
        """Suppress the alert."""
        if self.status == AlertStatus.ACTIVE:
            self.status = AlertStatus.SUPPRESSED
            
            if reason:
                self.add_annotation("suppression", reason, "system")

    def add_annotation(self, annotation_type: str, content: str, created_by: str) -> None:
        """Add annotation to alert."""
        annotation = {
            "id": str(uuid.uuid4()),
            "type": annotation_type,
            "content": content,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self.annotations.append(annotation)

    def get_duration(self) -> timedelta:
        """Get alert duration."""
        end_time = self.resolved_at or datetime.now(timezone.utc)
        return end_time - self.triggered_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "metric_name": self.metric_name,
            "severity": self.severity.value,
            "status": self.status.value,
            "trigger_value": self.trigger_value,
            "trigger_condition": self.trigger_condition,
            "message": self.message,
            "context": self.context,
            "triggered_at": self.triggered_at.isoformat(),
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "assigned_to": self.assigned_to,
            "acknowledged_by": self.acknowledged_by,
            "resolved_by": self.resolved_by,
            "duration_seconds": self.get_duration().total_seconds(),
            "tags": self.tags,
            "annotations": self.annotations
        }


@dataclass
class Dashboard:
    """Monitoring dashboard definition."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    dashboard_type: DashboardType = DashboardType.CUSTOM
    
    # Layout and widgets
    widgets: List[Dict[str, Any]] = field(default_factory=list)
    layout: Dict[str, Any] = field(default_factory=dict)
    
    # Access control
    visibility: str = "private"  # private, team, public
    owner: str = ""
    shared_with: List[str] = field(default_factory=list)
    
    # Settings
    refresh_interval_seconds: int = 300
    auto_refresh: bool = True
    time_range: Dict[str, Any] = field(default_factory=lambda: {"last": "1h"})
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)
    
    # Usage tracking
    view_count: int = 0
    last_viewed_at: Optional[datetime] = None

    def add_widget(self, widget_type: str, title: str, config: Dict[str, Any]) -> str:
        """Add widget to dashboard."""
        widget_id = str(uuid.uuid4())
        
        widget = {
            "id": widget_id,
            "type": widget_type,
            "title": title,
            "config": config,
            "position": {"x": 0, "y": 0, "width": 4, "height": 3},
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.widgets.append(widget)
        self.updated_at = datetime.now(timezone.utc)
        
        return widget_id

    def remove_widget(self, widget_id: str) -> bool:
        """Remove widget from dashboard."""
        initial_count = len(self.widgets)
        self.widgets = [w for w in self.widgets if w["id"] != widget_id]
        
        if len(self.widgets) < initial_count:
            self.updated_at = datetime.now(timezone.utc)
            return True
        
        return False

    def update_widget(self, widget_id: str, updates: Dict[str, Any]) -> bool:
        """Update widget configuration."""
        for widget in self.widgets:
            if widget["id"] == widget_id:
                widget.update(updates)
                widget["updated_at"] = datetime.now(timezone.utc).isoformat()
                self.updated_at = datetime.now(timezone.utc)
                return True
        
        return False

    def record_view(self) -> None:
        """Record dashboard view."""
        self.view_count += 1
        self.last_viewed_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert dashboard to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "dashboard_type": self.dashboard_type.value,
            "widgets": self.widgets,
            "layout": self.layout,
            "visibility": self.visibility,
            "owner": self.owner,
            "shared_with": self.shared_with,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "auto_refresh": self.auto_refresh,
            "time_range": self.time_range,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "view_count": self.view_count,
            "last_viewed_at": self.last_viewed_at.isoformat() if self.last_viewed_at else None
        }