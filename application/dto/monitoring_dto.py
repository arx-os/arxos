"""
Monitoring Data Transfer Objects.

DTOs for monitoring and alerting operations including metrics management,
alert handling, and dashboard operations.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


@dataclass
class CreateMetricRequest:
    """Create metric request."""
    name: str
    description: str = ""
    metric_type: str = "gauge"  # MetricType value
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    retention_days: int = 30
    resolution_seconds: int = 60
    aggregation_method: str = "avg"  # avg, sum, min, max, count


@dataclass
class CreateMetricResponse:
    """Create metric response."""
    success: bool
    metric_id: Optional[str] = None
    message: str = ""
    metric: Optional[Dict[str, Any]] = None


@dataclass
class MetricDataRequest:
    """Record metric data request."""
    metric_name: str
    value: Optional[Union[int, float]] = None
    timestamp: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    data_points: Optional[List[Dict[str, Any]]] = None  # For batch recording


@dataclass
class MetricDataResponse:
    """Record metric data response."""
    success: bool
    points_recorded: int = 0
    message: str = ""


@dataclass
class MetricStatsResponse:
    """Metric statistics response."""
    success: bool
    metric_name: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class CreateAlertRuleRequest:
    """Create alert rule request."""
    name: str
    description: str = ""
    metric_name: str = ""
    condition: Dict[str, Any] = field(default_factory=dict)
    severity: str = "medium"  # AlertSeverity value
    enabled: bool = True
    cooldown_minutes: int = 5
    max_alerts_per_hour: int = 10
    notification_channels: List[str] = field(default_factory=list)
    escalation_policy: Dict[str, Any] = field(default_factory=dict)
    suppression_conditions: List[Dict[str, Any]] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class CreateAlertRuleResponse:
    """Create alert rule response."""
    success: bool
    rule_id: Optional[str] = None
    message: str = ""
    rule: Optional[Dict[str, Any]] = None


@dataclass
class UpdateAlertRuleRequest:
    """Update alert rule request."""
    name: Optional[str] = None
    description: Optional[str] = None
    condition: Optional[Dict[str, Any]] = None
    severity: Optional[str] = None
    enabled: Optional[bool] = None
    cooldown_minutes: Optional[int] = None
    max_alerts_per_hour: Optional[int] = None
    notification_channels: Optional[List[str]] = None
    escalation_policy: Optional[Dict[str, Any]] = None
    suppression_conditions: Optional[List[Dict[str, Any]]] = None
    tags: Optional[Dict[str, str]] = None


@dataclass
class UpdateAlertRuleResponse:
    """Update alert rule response."""
    success: bool
    message: str = ""
    updated_fields: List[str] = field(default_factory=list)


@dataclass
class AlertResponse:
    """Single alert response."""
    success: bool
    alert: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class ListAlertsResponse:
    """List alerts response."""
    success: bool
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 50
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False
    message: str = ""


@dataclass
class AlertStatsResponse:
    """Alert statistics response."""
    success: bool
    statistics: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class CreateDashboardRequest:
    """Create dashboard request."""
    name: str
    description: str = ""
    dashboard_type: str = "custom"  # DashboardType value
    widgets: List[Dict[str, Any]] = field(default_factory=list)
    layout: Dict[str, Any] = field(default_factory=dict)
    visibility: str = "private"  # private, team, public
    shared_with: List[str] = field(default_factory=list)
    refresh_interval_seconds: int = 300
    auto_refresh: bool = True
    time_range: Dict[str, Any] = field(default_factory=lambda: {"last": "1h"})
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class CreateDashboardResponse:
    """Create dashboard response."""
    success: bool
    dashboard_id: Optional[str] = None
    message: str = ""
    dashboard: Optional[Dict[str, Any]] = None


@dataclass
class UpdateDashboardRequest:
    """Update dashboard request."""
    name: Optional[str] = None
    description: Optional[str] = None
    widgets: Optional[List[Dict[str, Any]]] = None
    layout: Optional[Dict[str, Any]] = None
    visibility: Optional[str] = None
    shared_with: Optional[List[str]] = None
    refresh_interval_seconds: Optional[int] = None
    auto_refresh: Optional[bool] = None
    time_range: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, str]] = None


@dataclass
class UpdateDashboardResponse:
    """Update dashboard response."""
    success: bool
    message: str = ""
    updated_fields: List[str] = field(default_factory=list)


@dataclass
class DashboardResponse:
    """Single dashboard response."""
    success: bool
    dashboard: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class ListDashboardsResponse:
    """List dashboards response."""
    success: bool
    dashboards: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 50
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False
    message: str = ""


@dataclass
class SystemHealthResponse:
    """System health response."""
    success: bool
    health_data: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class MetricQueryRequest:
    """Metric query request."""
    metric_names: List[str]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    aggregation: Optional[str] = None  # avg, sum, min, max, count
    group_by: Optional[List[str]] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    resolution: Optional[str] = None  # 1m, 5m, 15m, 1h, 1d


@dataclass
class MetricQueryResponse:
    """Metric query response."""
    success: bool
    results: List[Dict[str, Any]] = field(default_factory=list)
    query_info: Dict[str, Any] = field(default_factory=dict)
    message: str = ""


@dataclass
class AnomalyDetectionRequest:
    """Anomaly detection request."""
    metric_name: str
    detection_method: str = "statistical"  # AnomalyDetectionMethod value
    sensitivity: float = 0.8  # 0.0 to 1.0
    lookback_points: int = 100
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyDetectionResponse:
    """Anomaly detection response."""
    success: bool
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    detection_info: Dict[str, Any] = field(default_factory=dict)
    message: str = ""


@dataclass
class AlertBulkActionRequest:
    """Bulk alert action request."""
    alert_ids: List[str]
    action: str  # acknowledge, resolve, suppress, delete
    action_by: str
    note: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertBulkActionResponse:
    """Bulk alert action response."""
    success: bool
    processed_count: int = 0
    failed_count: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""


@dataclass
class NotificationChannelRequest:
    """Notification channel configuration request."""
    name: str
    channel_type: str  # NotificationChannel value
    configuration: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    default_for_severity: List[str] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class NotificationChannelResponse:
    """Notification channel response."""
    success: bool
    channel_id: Optional[str] = None
    channel: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class MonitoringAnalyticsRequest:
    """Monitoring analytics request."""
    time_range: Dict[str, Any]
    metrics: Optional[List[str]] = None
    alert_rules: Optional[List[str]] = None
    group_by: Optional[str] = None  # metric, severity, status
    include_trends: bool = True
    include_comparisons: bool = False
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringAnalyticsResponse:
    """Monitoring analytics response."""
    success: bool
    analytics_data: Optional[Dict[str, Any]] = None
    summary_metrics: Optional[Dict[str, Any]] = None
    trends: Optional[Dict[str, Any]] = None
    comparisons: Optional[Dict[str, Any]] = None
    insights: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""


@dataclass
class MetricExportRequest:
    """Metric export request."""
    metric_names: List[str]
    start_time: datetime
    end_time: datetime
    format: str = "csv"  # csv, json, parquet
    include_metadata: bool = True
    compression: str = "none"  # none, gzip, zip


@dataclass
class MetricExportResponse:
    """Metric export response."""
    success: bool
    export_id: Optional[str] = None
    download_url: Optional[str] = None
    file_size: int = 0
    format: str = ""
    expires_at: Optional[datetime] = None
    message: str = ""


@dataclass
class AlertRuleTemplateRequest:
    """Alert rule template request."""
    name: str
    description: str
    category: str
    template_data: Dict[str, Any]
    is_public: bool = False
    tags: List[str] = field(default_factory=list)


@dataclass
class AlertRuleTemplateResponse:
    """Alert rule template response."""
    success: bool
    template_id: Optional[str] = None
    template: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class ListAlertRuleTemplatesResponse:
    """List alert rule templates response."""
    success: bool
    templates: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    categories: List[str] = field(default_factory=list)
    message: str = ""


@dataclass
class AlertCorrelationRequest:
    """Alert correlation analysis request."""
    time_range: Dict[str, Any]
    correlation_methods: List[str] = field(default_factory=lambda: ["temporal", "metric_based"])
    min_correlation_score: float = 0.7
    max_results: int = 50


@dataclass
class AlertCorrelationResponse:
    """Alert correlation analysis response."""
    success: bool
    correlations: List[Dict[str, Any]] = field(default_factory=list)
    correlation_graph: Optional[Dict[str, Any]] = None
    analysis_summary: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class CapacityPlanningRequest:
    """Capacity planning analysis request."""
    metrics: List[str]
    forecast_days: int = 30
    growth_assumptions: Dict[str, float] = field(default_factory=dict)
    confidence_level: float = 0.95
    include_seasonality: bool = True


@dataclass
class CapacityPlanningResponse:
    """Capacity planning analysis response."""
    success: bool
    forecasts: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    risk_assessments: List[Dict[str, Any]] = field(default_factory=list)
    planning_data: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class PerformanceTestRequest:
    """Performance test configuration request."""
    test_name: str
    test_duration_minutes: int = 10
    target_metrics: List[str] = field(default_factory=list)
    load_pattern: Dict[str, Any] = field(default_factory=dict)
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    notification_channels: List[str] = field(default_factory=list)


@dataclass
class PerformanceTestResponse:
    """Performance test response."""
    success: bool
    test_id: Optional[str] = None
    test_results: Optional[Dict[str, Any]] = None
    performance_summary: Optional[Dict[str, Any]] = None
    recommendations: List[str] = field(default_factory=list)
    message: str = ""


@dataclass
class SLODefinitionRequest:
    """Service Level Objective definition request."""
    name: str
    description: str
    service_name: str
    sli_metric: str  # Service Level Indicator metric
    target_value: float
    target_unit: str
    time_window: str  # rolling_30d, monthly, weekly
    alert_threshold: float  # Error budget threshold for alerts
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class SLODefinitionResponse:
    """Service Level Objective definition response."""
    success: bool
    slo_id: Optional[str] = None
    slo: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class SLOStatusResponse:
    """SLO status response."""
    success: bool
    slo_status: Optional[Dict[str, Any]] = None
    error_budget: Optional[Dict[str, Any]] = None
    compliance_history: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""


# Specialized DTOs for different monitoring use cases
@dataclass
class InfrastructureMonitoringRequest(CreateMetricRequest):
    """Infrastructure monitoring request."""
    host_name: str = ""
    component: str = ""  # cpu, memory, disk, network
    collection_interval: int = 60
    alert_thresholds: Dict[str, float] = field(default_factory=dict)


@dataclass
class ApplicationMonitoringRequest(CreateMetricRequest):
    """Application monitoring request."""
    application_name: str = ""
    service_name: str = ""
    endpoint: str = ""
    monitoring_type: str = "performance"  # performance, errors, business
    custom_dimensions: Dict[str, str] = field(default_factory=dict)


@dataclass
class BusinessMetricsRequest(CreateMetricRequest):
    """Business metrics monitoring request."""
    business_unit: str = ""
    kpi_type: str = ""  # revenue, conversion, engagement
    calculation_method: str = ""
    data_source: str = ""
    reporting_schedule: str = "hourly"  # hourly, daily, weekly


@dataclass
class SecurityMonitoringRequest(CreateMetricRequest):
    """Security monitoring request."""
    security_domain: str = ""  # authentication, authorization, threats
    event_source: str = ""
    risk_level: str = "medium"  # low, medium, high, critical
    compliance_requirements: List[str] = field(default_factory=list)


# Response DTOs for specialized monitoring
@dataclass
class InfrastructureMonitoringResponse(CreateMetricResponse):
    """Infrastructure monitoring response."""
    monitoring_config: Optional[Dict[str, Any]] = None
    baseline_established: bool = False


@dataclass
class ApplicationMonitoringResponse(CreateMetricResponse):
    """Application monitoring response."""
    service_map_updated: bool = False
    dependencies: List[str] = field(default_factory=list)


@dataclass
class BusinessMetricsResponse(CreateMetricResponse):
    """Business metrics response."""
    kpi_dashboard_url: Optional[str] = None
    reporting_schedule: Optional[Dict[str, Any]] = None


@dataclass
class SecurityMonitoringResponse(CreateMetricResponse):
    """Security monitoring response."""
    threat_detection_rules: List[Dict[str, Any]] = field(default_factory=list)
    compliance_status: Optional[Dict[str, Any]] = None