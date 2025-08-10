"""
Analytics Data Transfer Objects.

DTOs for analytics and reporting operations including dashboard metrics,
custom queries, trend analysis, and predictive analytics.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


@dataclass
class AnalyticsRequest:
    """Base analytics request."""
    time_range: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    user_context: Dict[str, str] = field(default_factory=dict)


@dataclass
class AnalyticsResponse:
    """Base analytics response."""
    success: bool
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: int = 0
    cache_hit: bool = False


@dataclass
class DashboardMetricsRequest(AnalyticsRequest):
    """Dashboard metrics request."""
    include_predictions: bool = False
    metric_categories: List[str] = field(default_factory=list)
    refresh_cache: bool = False


@dataclass
class DashboardMetricsResponse(AnalyticsResponse):
    """Dashboard metrics response."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DashboardMetricsResponse':
        """Create from dictionary (for caching)."""
        return cls(
            success=data.get("success", True),
            data=data.get("data", {}),
            message=data.get("message", ""),
            execution_time_ms=data.get("execution_time_ms", 0),
            cache_hit=True
        )


@dataclass
class CustomQueryRequest(AnalyticsRequest):
    """Custom analytics query request."""
    metrics: List[str] = field(default_factory=list)
    dimensions: List[str] = field(default_factory=list)
    aggregations: Dict[str, str] = field(default_factory=dict)
    granularity: str = "hour"  # hour, day, week, month
    include_visualizations: bool = False
    limit: int = 1000


@dataclass
class CustomQueryResponse(AnalyticsResponse):
    """Custom analytics query response."""
    query_info: Dict[str, Any] = field(default_factory=dict)
    visualizations: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrendAnalysisRequest(AnalyticsRequest):
    """Trend analysis request."""
    metrics: List[str] = field(default_factory=list)
    entities: Optional[List[str]] = None
    granularity: str = "day"
    include_forecasts: bool = False
    forecast_periods: int = 7
    anomaly_detection: bool = True
    correlation_analysis: bool = True


@dataclass
class TrendAnalysisResponse(AnalyticsResponse):
    """Trend analysis response."""
    trends: Dict[str, Any] = field(default_factory=dict)
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    correlations: Dict[str, Any] = field(default_factory=dict)
    forecasts: Dict[str, Any] = field(default_factory=dict)
    insights: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PredictiveAnalyticsRequest(AnalyticsRequest):
    """Predictive analytics request."""
    prediction_types: List[str] = field(default_factory=list)  # energy_usage, occupancy, maintenance, etc.
    time_horizon: int = 24  # hours
    entities: Optional[List[str]] = None
    confidence_level: float = 0.95
    include_scenarios: bool = False
    model_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictiveAnalyticsResponse(AnalyticsResponse):
    """Predictive analytics response."""
    predictions: Dict[str, Any] = field(default_factory=dict)
    confidence_intervals: Dict[str, Any] = field(default_factory=dict)
    model_performance: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ReportGenerationRequest:
    """Report generation request."""
    report_type: str  # dashboard, energy, occupancy, maintenance, custom
    format: str = "pdf"  # pdf, excel, csv, json
    template_id: Optional[str] = None
    template_options: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    options: Dict[str, Any] = field(default_factory=dict)
    delivery_options: Optional[Dict[str, Any]] = None
    schedule_options: Optional[Dict[str, Any]] = None


@dataclass
class ReportGenerationResponse:
    """Report generation response."""
    success: bool
    report_id: Optional[str] = None
    download_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    scheduled: bool = False


@dataclass
class BuildingMetricsRequest(AnalyticsRequest):
    """Building-specific metrics request."""
    building_ids: Optional[List[str]] = None
    include_floors: bool = True
    include_rooms: bool = True
    include_devices: bool = True
    metric_types: List[str] = field(default_factory=list)


@dataclass
class BuildingMetricsResponse(AnalyticsResponse):
    """Building metrics response."""
    buildings: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    aggregated_metrics: Dict[str, Any] = field(default_factory=dict)
    comparisons: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OccupancyAnalysisRequest(AnalyticsRequest):
    """Occupancy analysis request."""
    granularity: str = "hour"  # minute, hour, day
    include_patterns: bool = True
    include_predictions: bool = False
    space_types: Optional[List[str]] = None
    occupancy_thresholds: Dict[str, float] = field(default_factory=dict)


@dataclass
class OccupancyAnalysisResponse(AnalyticsResponse):
    """Occupancy analysis response."""
    current_occupancy: Dict[str, Any] = field(default_factory=dict)
    historical_patterns: Dict[str, Any] = field(default_factory=dict)
    utilization_metrics: Dict[str, Any] = field(default_factory=dict)
    optimization_opportunities: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class EnergyAnalysisRequest(AnalyticsRequest):
    """Energy analysis request."""
    energy_types: List[str] = field(default_factory=list)  # electricity, gas, steam, etc.
    include_cost_analysis: bool = True
    include_efficiency_metrics: bool = True
    benchmark_comparison: bool = False
    weather_normalization: bool = False


@dataclass
class EnergyAnalysisResponse(AnalyticsResponse):
    """Energy analysis response."""
    consumption_metrics: Dict[str, Any] = field(default_factory=dict)
    cost_analysis: Dict[str, Any] = field(default_factory=dict)
    efficiency_metrics: Dict[str, Any] = field(default_factory=dict)
    savings_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    benchmarks: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeviceAnalyticsRequest(AnalyticsRequest):
    """Device analytics request."""
    device_ids: Optional[List[str]] = None
    device_types: Optional[List[str]] = None
    health_analysis: bool = True
    performance_analysis: bool = True
    maintenance_analysis: bool = True
    include_predictions: bool = False


@dataclass
class DeviceAnalyticsResponse(AnalyticsResponse):
    """Device analytics response."""
    device_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    health_summary: Dict[str, Any] = field(default_factory=dict)
    performance_summary: Dict[str, Any] = field(default_factory=dict)
    maintenance_insights: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SpaceUtilizationRequest(AnalyticsRequest):
    """Space utilization analysis request."""
    space_types: Optional[List[str]] = None
    utilization_metrics: List[str] = field(default_factory=list)
    benchmark_analysis: bool = True
    optimization_analysis: bool = True
    include_financial_impact: bool = False


@dataclass
class SpaceUtilizationResponse(AnalyticsResponse):
    """Space utilization analysis response."""
    utilization_metrics: Dict[str, Any] = field(default_factory=dict)
    space_efficiency: Dict[str, Any] = field(default_factory=dict)
    underutilized_spaces: List[Dict[str, Any]] = field(default_factory=list)
    optimization_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    financial_impact: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnvironmentalAnalysisRequest(AnalyticsRequest):
    """Environmental analysis request."""
    metrics: List[str] = field(default_factory=list)  # temperature, humidity, air_quality, etc.
    comfort_analysis: bool = True
    compliance_check: bool = False
    seasonal_analysis: bool = False
    space_comparison: bool = True


@dataclass
class EnvironmentalAnalysisResponse(AnalyticsResponse):
    """Environmental analysis response."""
    current_conditions: Dict[str, Any] = field(default_factory=dict)
    comfort_metrics: Dict[str, Any] = field(default_factory=dict)
    compliance_status: Dict[str, Any] = field(default_factory=dict)
    trends: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MaintenanceAnalyticsRequest(AnalyticsRequest):
    """Maintenance analytics request."""
    include_scheduled: bool = True
    include_reactive: bool = True
    include_predictive: bool = True
    cost_analysis: bool = True
    efficiency_analysis: bool = True
    failure_analysis: bool = False


@dataclass
class MaintenanceAnalyticsResponse(AnalyticsResponse):
    """Maintenance analytics response."""
    maintenance_summary: Dict[str, Any] = field(default_factory=dict)
    cost_analysis: Dict[str, Any] = field(default_factory=dict)
    efficiency_metrics: Dict[str, Any] = field(default_factory=dict)
    failure_analysis: Dict[str, Any] = field(default_factory=dict)
    optimization_opportunities: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class BenchmarkAnalysisRequest(AnalyticsRequest):
    """Benchmark analysis request."""
    benchmark_type: str  # industry, portfolio, historical, peer
    metrics: List[str] = field(default_factory=list)
    comparison_entities: Optional[List[str]] = None
    normalization_factors: Dict[str, Any] = field(default_factory=dict)
    include_rankings: bool = True


@dataclass
class BenchmarkAnalysisResponse(AnalyticsResponse):
    """Benchmark analysis response."""
    benchmark_results: Dict[str, Any] = field(default_factory=dict)
    performance_rankings: Dict[str, Any] = field(default_factory=dict)
    gap_analysis: Dict[str, Any] = field(default_factory=dict)
    improvement_targets: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AlertAnalyticsRequest(AnalyticsRequest):
    """Alert analytics request."""
    alert_types: Optional[List[str]] = None
    severity_levels: Optional[List[str]] = None
    include_patterns: bool = True
    include_response_analysis: bool = True
    trend_analysis: bool = True


@dataclass
class AlertAnalyticsResponse(AnalyticsResponse):
    """Alert analytics response."""
    alert_summary: Dict[str, Any] = field(default_factory=dict)
    alert_patterns: Dict[str, Any] = field(default_factory=dict)
    response_metrics: Dict[str, Any] = field(default_factory=dict)
    trends: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class PortfolioAnalyticsRequest(AnalyticsRequest):
    """Portfolio-level analytics request."""
    portfolio_id: Optional[str] = None
    building_groups: Optional[List[str]] = None
    comparison_analysis: bool = True
    aggregation_level: str = "building"  # building, floor, room
    performance_metrics: List[str] = field(default_factory=list)


@dataclass
class PortfolioAnalyticsResponse(AnalyticsResponse):
    """Portfolio analytics response."""
    portfolio_summary: Dict[str, Any] = field(default_factory=dict)
    building_comparisons: Dict[str, Any] = field(default_factory=dict)
    performance_rankings: Dict[str, Any] = field(default_factory=dict)
    outlier_analysis: Dict[str, Any] = field(default_factory=dict)
    optimization_opportunities: List[Dict[str, Any]] = field(default_factory=list)


# Query Builder DTOs
@dataclass
class QueryBuilder:
    """Analytics query builder."""
    select: List[str] = field(default_factory=list)
    from_entities: List[str] = field(default_factory=list)
    where_conditions: List[Dict[str, Any]] = field(default_factory=list)
    group_by: List[str] = field(default_factory=list)
    order_by: List[Dict[str, str]] = field(default_factory=list)
    limit: Optional[int] = None
    
    def add_metric(self, metric: str, aggregation: str = "avg") -> 'QueryBuilder':
        """Add metric to query."""
        self.select.append(f"{aggregation}({metric}) as {metric}_{aggregation}")
        return self
    
    def add_dimension(self, dimension: str) -> 'QueryBuilder':
        """Add dimension to query."""
        self.select.append(dimension)
        self.group_by.append(dimension)
        return self
    
    def add_filter(self, field: str, operator: str, value: Any) -> 'QueryBuilder':
        """Add filter condition."""
        self.where_conditions.append({
            "field": field,
            "operator": operator,
            "value": value
        })
        return self
    
    def add_time_range(self, start: datetime, end: datetime) -> 'QueryBuilder':
        """Add time range filter."""
        self.add_filter("timestamp", ">=", start)
        self.add_filter("timestamp", "<=", end)
        return self
    
    def set_limit(self, limit: int) -> 'QueryBuilder':
        """Set result limit."""
        self.limit = limit
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for execution."""
        return {
            "select": self.select,
            "from": self.from_entities,
            "where": self.where_conditions,
            "group_by": self.group_by,
            "order_by": self.order_by,
            "limit": self.limit
        }