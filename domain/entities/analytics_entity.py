"""
Analytics Domain Entities.

Domain entities for analytics, reporting, and business intelligence operations
including queries, templates, metrics, and dashboard configurations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, Union
from enum import Enum
import json

from domain.value_objects import AnalyticsId, ReportId, UserId
from domain.events import DomainEvent
from domain.exceptions import InvalidAnalyticsError, BusinessRuleViolationError


class MetricType(Enum):
    """Types of metrics available for analytics."""
    # Operational Metrics
    OCCUPANCY = "occupancy"
    UTILIZATION = "utilization"
    AVAILABILITY = "availability"
    
    # Energy Metrics
    ENERGY_CONSUMPTION = "energy_consumption"
    POWER_DEMAND = "power_demand"
    ENERGY_COST = "energy_cost"
    ENERGY_EFFICIENCY = "energy_efficiency"
    
    # Environmental Metrics
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    AIR_QUALITY = "air_quality"
    CO2_LEVEL = "co2_level"
    LIGHT_LEVEL = "light_level"
    NOISE_LEVEL = "noise_level"
    
    # Device Metrics
    DEVICE_HEALTH = "device_health"
    DEVICE_UPTIME = "device_uptime"
    DEVICE_PERFORMANCE = "device_performance"
    FAILURE_RATE = "failure_rate"
    
    # Space Metrics
    SPACE_EFFICIENCY = "space_efficiency"
    DENSITY = "density"
    CIRCULATION = "circulation"
    
    # Financial Metrics
    OPERATIONAL_COST = "operational_cost"
    MAINTENANCE_COST = "maintenance_cost"
    ENERGY_COST_PER_SQFT = "energy_cost_per_sqft"
    ROI = "roi"
    
    # Performance Metrics
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    
    # Custom Metrics
    CUSTOM = "custom"


class AggregationType(Enum):
    """Types of aggregations for metrics."""
    SUM = "sum"
    AVERAGE = "avg"
    MINIMUM = "min"
    MAXIMUM = "max"
    COUNT = "count"
    MEDIAN = "median"
    PERCENTILE_95 = "p95"
    PERCENTILE_99 = "p99"
    STANDARD_DEVIATION = "stddev"
    VARIANCE = "variance"
    FIRST = "first"
    LAST = "last"


class TimeGranularity(Enum):
    """Time granularity for analytics queries."""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class ReportFormat(Enum):
    """Report output formats."""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"
    PNG = "png"
    SVG = "svg"


class ReportStatus(Enum):
    """Report generation status."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class MetricDefinition:
    """Definition of an analytics metric."""
    name: str
    type: MetricType
    unit: str
    description: str
    calculation_method: str
    aggregation_types: Set[AggregationType] = field(default_factory=set)
    dimensions: List[str] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Validate metric definition."""
        return bool(self.name and self.type and self.unit and self.calculation_method)


@dataclass
class QueryFilter:
    """Filter for analytics queries."""
    field: str
    operator: str  # eq, ne, gt, gte, lt, lte, in, not_in, contains, between
    value: Union[str, int, float, List[Any], Dict[str, Any]]
    logic_operator: str = "AND"  # AND, OR
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
            "logic_operator": self.logic_operator
        }


@dataclass
class QueryAggregation:
    """Aggregation definition for queries."""
    field: str
    type: AggregationType
    alias: Optional[str] = None
    
    def get_alias(self) -> str:
        """Get aggregation alias."""
        return self.alias or f"{self.field}_{self.type.value}"


# Domain Events
@dataclass
class QueryExecuted(DomainEvent):
    """Query executed event."""
    query_id: str
    user_id: str
    execution_time_ms: int
    result_count: int
    cache_hit: bool


@dataclass
class ReportGenerated(DomainEvent):
    """Report generated event."""
    report_id: str
    report_type: str
    format: str
    generated_by: str
    file_size: int
    generation_time_ms: int


@dataclass
class DashboardViewed(DomainEvent):
    """Dashboard viewed event."""
    dashboard_id: str
    user_id: str
    view_duration_seconds: int
    widgets_loaded: List[str]


@dataclass
class MetricThresholdExceeded(DomainEvent):
    """Metric threshold exceeded event."""
    metric_name: str
    current_value: float
    threshold_value: float
    severity: str
    entity_id: str
    entity_type: str


class AnalyticsQuery:
    """Analytics query entity with comprehensive querying capabilities."""
    
    def __init__(self, query_id: AnalyticsId, created_by: UserId):
        # Core Identity
        self.id = query_id
        self.created_by = created_by
        
        # Query Definition
        self.metrics: List[str] = []
        self.dimensions: List[str] = []
        self.filters: List[QueryFilter] = []
        self.aggregations: List[QueryAggregation] = []
        self.time_range: Dict[str, Any] = {}
        self.granularity: Optional[TimeGranularity] = None
        
        # Query Configuration
        self.limit: Optional[int] = None
        self.order_by: List[Dict[str, str]] = []
        self.group_by: List[str] = []
        
        # Execution Context
        self.execution_context: Dict[str, Any] = {}
        self.cache_enabled: bool = True
        self.cache_ttl: int = 3600  # 1 hour default
        
        # Metadata
        self.name: Optional[str] = None
        self.description: Optional[str] = None
        self.tags: Set[str] = set()
        self.is_saved: bool = False
        self.is_public: bool = False
        
        # Lifecycle Information
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.last_executed_at: Optional[datetime] = None
        self.execution_count: int = 0
        
        # Performance Tracking
        self.average_execution_time_ms: float = 0
        self.last_execution_time_ms: int = 0
        self.result_count_history: List[int] = []
        
        # Domain Events
        self._domain_events: List[DomainEvent] = []
    
    def add_metric(self, metric: str, aggregation: AggregationType = AggregationType.AVERAGE) -> None:
        """Add metric to query."""
        if metric not in self.metrics:
            self.metrics.append(metric)
            
        # Add corresponding aggregation
        agg = QueryAggregation(field=metric, type=aggregation)
        if agg not in self.aggregations:
            self.aggregations.append(agg)
        
        self.updated_at = datetime.now(timezone.utc)
    
    def add_dimension(self, dimension: str) -> None:
        """Add dimension to query."""
        if dimension not in self.dimensions:
            self.dimensions.append(dimension)
            
        # Add to group by if not already present
        if dimension not in self.group_by:
            self.group_by.append(dimension)
        
        self.updated_at = datetime.now(timezone.utc)
    
    def add_filter(self, field: str, operator: str, value: Any, logic_operator: str = "AND") -> None:
        """Add filter to query."""
        filter_obj = QueryFilter(
            field=field,
            operator=operator,
            value=value,
            logic_operator=logic_operator
        )
        self.filters.append(filter_obj)
        self.updated_at = datetime.now(timezone.utc)
    
    def set_time_range(self, start: datetime, end: datetime) -> None:
        """Set query time range."""
        if start >= end:
            raise InvalidAnalyticsError("Start time must be before end time")
        
        self.time_range = {
            "start": start,
            "end": end,
            "duration_hours": (end - start).total_seconds() / 3600
        }
        self.updated_at = datetime.now(timezone.utc)
    
    def set_granularity(self, granularity: TimeGranularity) -> None:
        """Set time granularity."""
        self.granularity = granularity
        self.updated_at = datetime.now(timezone.utc)
    
    def set_limit(self, limit: int) -> None:
        """Set result limit."""
        if limit <= 0:
            raise InvalidAnalyticsError("Limit must be positive")
        
        if limit > 10000:
            raise BusinessRuleViolationError("Query limit cannot exceed 10,000 rows")
        
        self.limit = limit
        self.updated_at = datetime.now(timezone.utc)
    
    def add_order_by(self, field: str, direction: str = "DESC") -> None:
        """Add order by clause."""
        if direction.upper() not in ["ASC", "DESC"]:
            raise InvalidAnalyticsError("Order direction must be ASC or DESC")
        
        self.order_by.append({"field": field, "direction": direction.upper()})
        self.updated_at = datetime.now(timezone.utc)
    
    def save_query(self, name: str, description: str = "", is_public: bool = False) -> None:
        """Save query for reuse."""
        if not name.strip():
            raise InvalidAnalyticsError("Query name cannot be empty")
        
        self.name = name.strip()
        self.description = description.strip()
        self.is_public = is_public
        self.is_saved = True
        self.updated_at = datetime.now(timezone.utc)
    
    def record_execution(self, execution_time_ms: int, result_count: int, cache_hit: bool = False) -> None:
        """Record query execution metrics."""
        self.last_executed_at = datetime.now(timezone.utc)
        self.last_execution_time_ms = execution_time_ms
        self.execution_count += 1
        
        # Update average execution time
        total_time = (self.average_execution_time_ms * (self.execution_count - 1)) + execution_time_ms
        self.average_execution_time_ms = total_time / self.execution_count
        
        # Track result count history (keep last 10)
        self.result_count_history.append(result_count)
        if len(self.result_count_history) > 10:
            self.result_count_history = self.result_count_history[-10:]
        
        # Add domain event
        self._add_domain_event(QueryExecuted(
            query_id=str(self.id),
            user_id=str(self.created_by),
            execution_time_ms=execution_time_ms,
            result_count=result_count,
            cache_hit=cache_hit
        ))
    
    def get_average_result_count(self) -> float:
        """Get average result count."""
        if not self.result_count_history:
            return 0
        return sum(self.result_count_history) / len(self.result_count_history)
    
    def is_complex_query(self) -> bool:
        """Determine if query is complex based on various factors."""
        complexity_score = 0
        
        # Number of metrics
        complexity_score += len(self.metrics) * 1
        
        # Number of dimensions
        complexity_score += len(self.dimensions) * 2
        
        # Number of filters
        complexity_score += len(self.filters) * 1
        
        # Time range duration (hours)
        if self.time_range:
            duration_hours = self.time_range.get("duration_hours", 0)
            if duration_hours > 720:  # 30 days
                complexity_score += 5
            elif duration_hours > 168:  # 7 days
                complexity_score += 3
            elif duration_hours > 24:  # 1 day
                complexity_score += 1
        
        # Granularity
        if self.granularity:
            granularity_weights = {
                TimeGranularity.MINUTE: 5,
                TimeGranularity.HOUR: 3,
                TimeGranularity.DAY: 1,
                TimeGranularity.WEEK: 0,
                TimeGranularity.MONTH: 0,
                TimeGranularity.QUARTER: 0,
                TimeGranularity.YEAR: 0
            }
            complexity_score += granularity_weights.get(self.granularity, 0)
        
        return complexity_score > 10
    
    def to_sql_dict(self) -> Dict[str, Any]:
        """Convert query to SQL-like dictionary for execution."""
        return {
            "select": [agg.get_alias() for agg in self.aggregations],
            "from": "analytics_data",
            "where": [f.to_dict() for f in self.filters],
            "group_by": self.group_by,
            "order_by": self.order_by,
            "limit": self.limit,
            "time_range": self.time_range,
            "granularity": self.granularity.value if self.granularity else None
        }
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Get domain events."""
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """Clear domain events."""
        self._domain_events.clear()
    
    def _add_domain_event(self, event: DomainEvent) -> None:
        """Add domain event."""
        self._domain_events.append(event)


class ReportTemplate:
    """Report template entity for standardized reporting."""
    
    def __init__(self, template_id: ReportId, name: str, report_type: str, created_by: UserId):
        # Core Identity
        self.id = template_id
        self.name = self._validate_name(name)
        self.type = report_type
        self.created_by = created_by
        
        # Template Configuration
        self.sections: List[Dict[str, Any]] = []
        self.layout: Dict[str, Any] = {}
        self.styling: Dict[str, Any] = {}
        self.options: Dict[str, Any] = {}
        
        # Data Sources
        self.data_sources: List[Dict[str, Any]] = []
        self.default_parameters: Dict[str, Any] = {}
        
        # Template Metadata
        self.description: str = ""
        self.tags: Set[str] = set()
        self.category: str = ""
        self.version: str = "1.0"
        
        # Access Control
        self.is_public: bool = False
        self.allowed_users: Set[str] = set()
        self.allowed_roles: Set[str] = set()
        
        # Usage Statistics
        self.usage_count: int = 0
        self.last_used_at: Optional[datetime] = None
        
        # Lifecycle
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.is_active: bool = True
        
        # Domain Events
        self._domain_events: List[DomainEvent] = []
    
    def _validate_name(self, name: str) -> str:
        """Validate template name."""
        if not name or not name.strip():
            raise InvalidAnalyticsError("Template name cannot be empty")
        
        name = name.strip()
        if len(name) > 100:
            raise InvalidAnalyticsError("Template name cannot exceed 100 characters")
        
        return name
    
    def add_section(self, section_type: str, title: str, config: Dict[str, Any], required: bool = True) -> None:
        """Add section to template."""
        section = {
            "type": section_type,
            "title": title,
            "config": config,
            "required": required,
            "order": len(self.sections)
        }
        self.sections.append(section)
        self.updated_at = datetime.now(timezone.utc)
    
    def remove_section(self, section_index: int) -> None:
        """Remove section from template."""
        if 0 <= section_index < len(self.sections):
            self.sections.pop(section_index)
            # Reorder remaining sections
            for i, section in enumerate(self.sections):
                section["order"] = i
            self.updated_at = datetime.now(timezone.utc)
    
    def set_layout(self, layout_config: Dict[str, Any]) -> None:
        """Set template layout configuration."""
        self.layout = layout_config
        self.updated_at = datetime.now(timezone.utc)
    
    def set_styling(self, styling_config: Dict[str, Any]) -> None:
        """Set template styling configuration."""
        self.styling = styling_config
        self.updated_at = datetime.now(timezone.utc)
    
    def add_data_source(self, source_name: str, source_config: Dict[str, Any]) -> None:
        """Add data source to template."""
        data_source = {
            "name": source_name,
            "config": source_config,
            "added_at": datetime.now(timezone.utc).isoformat()
        }
        self.data_sources.append(data_source)
        self.updated_at = datetime.now(timezone.utc)
    
    def set_default_parameter(self, param_name: str, param_value: Any) -> None:
        """Set default parameter value."""
        self.default_parameters[param_name] = param_value
        self.updated_at = datetime.now(timezone.utc)
    
    def grant_access(self, user_id: str = None, role: str = None) -> None:
        """Grant access to user or role."""
        if user_id:
            self.allowed_users.add(user_id)
        if role:
            self.allowed_roles.add(role)
        self.updated_at = datetime.now(timezone.utc)
    
    def revoke_access(self, user_id: str = None, role: str = None) -> None:
        """Revoke access from user or role."""
        if user_id and user_id in self.allowed_users:
            self.allowed_users.remove(user_id)
        if role and role in self.allowed_roles:
            self.allowed_roles.remove(role)
        self.updated_at = datetime.now(timezone.utc)
    
    def can_access(self, user_id: str, user_roles: Set[str]) -> bool:
        """Check if user can access template."""
        if self.is_public:
            return True
        
        if user_id == str(self.created_by):
            return True
        
        if user_id in self.allowed_users:
            return True
        
        if any(role in self.allowed_roles for role in user_roles):
            return True
        
        return False
    
    def record_usage(self, user_id: str) -> None:
        """Record template usage."""
        self.usage_count += 1
        self.last_used_at = datetime.now(timezone.utc)
    
    def clone(self, new_name: str, new_created_by: UserId) -> 'ReportTemplate':
        """Clone template with new name and owner."""
        cloned_template = ReportTemplate(
            template_id=ReportId(),
            name=new_name,
            report_type=self.type,
            created_by=new_created_by
        )
        
        # Copy configuration
        cloned_template.sections = [section.copy() for section in self.sections]
        cloned_template.layout = self.layout.copy()
        cloned_template.styling = self.styling.copy()
        cloned_template.options = self.options.copy()
        cloned_template.data_sources = [ds.copy() for ds in self.data_sources]
        cloned_template.default_parameters = self.default_parameters.copy()
        
        # Copy metadata (but not access control)
        cloned_template.description = f"Copy of {self.description}"
        cloned_template.tags = self.tags.copy()
        cloned_template.category = self.category
        
        return cloned_template
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Get domain events."""
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """Clear domain events."""
        self._domain_events.clear()
    
    def _add_domain_event(self, event: DomainEvent) -> None:
        """Add domain event."""
        self._domain_events.append(event)


class DashboardMetric:
    """Dashboard metric configuration entity."""
    
    def __init__(self, metric_id: str, name: str, metric_type: MetricType):
        # Core Identity
        self.id = metric_id
        self.name = name
        self.type = metric_type
        
        # Metric Configuration
        self.aggregation: AggregationType = AggregationType.AVERAGE
        self.unit: str = ""
        self.format_string: str = "{value}"
        
        # Display Configuration
        self.display_name: str = name
        self.description: str = ""
        self.icon: str = ""
        self.color: str = "#007bff"
        
        # Thresholds and Alerts
        self.warning_threshold: Optional[float] = None
        self.critical_threshold: Optional[float] = None
        self.target_value: Optional[float] = None
        self.threshold_direction: str = "above"  # above, below, between
        
        # Data Source
        self.data_source: str = ""
        self.query_config: Dict[str, Any] = {}
        self.refresh_interval: int = 300  # 5 minutes
        
        # Visualization
        self.chart_type: str = "gauge"  # gauge, line, bar, pie, number
        self.chart_config: Dict[str, Any] = {}
        
        # Position and Layout
        self.dashboard_position: Dict[str, int] = {"x": 0, "y": 0, "width": 1, "height": 1}
        
        # Metadata
        self.tags: Set[str] = set()
        self.is_active: bool = True
        
        # Lifecycle
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        
        # Performance Tracking
        self.last_value: Optional[float] = None
        self.last_updated_at: Optional[datetime] = None
        self.update_count: int = 0
    
    def set_thresholds(self, warning: float = None, critical: float = None, 
                      target: float = None, direction: str = "above") -> None:
        """Set metric thresholds."""
        if direction not in ["above", "below", "between"]:
            raise InvalidAnalyticsError("Threshold direction must be 'above', 'below', or 'between'")
        
        self.warning_threshold = warning
        self.critical_threshold = critical
        self.target_value = target
        self.threshold_direction = direction
        self.updated_at = datetime.now(timezone.utc)
    
    def update_value(self, value: float) -> None:
        """Update metric value and check thresholds."""
        old_value = self.last_value
        self.last_value = value
        self.last_updated_at = datetime.now(timezone.utc)
        self.update_count += 1
        
        # Check thresholds and generate events if exceeded
        self._check_thresholds(old_value, value)
    
    def _check_thresholds(self, old_value: Optional[float], new_value: float) -> None:
        """Check if thresholds are exceeded and generate events."""
        if not self.warning_threshold and not self.critical_threshold:
            return
        
        # Check critical threshold
        if self.critical_threshold is not None:
            if self._exceeds_threshold(new_value, self.critical_threshold, "critical"):
                if old_value is None or not self._exceeds_threshold(old_value, self.critical_threshold, "critical"):
                    # Threshold just exceeded
                    self._trigger_threshold_event("critical", new_value, self.critical_threshold)
        
        # Check warning threshold
        if self.warning_threshold is not None:
            if self._exceeds_threshold(new_value, self.warning_threshold, "warning"):
                if old_value is None or not self._exceeds_threshold(old_value, self.warning_threshold, "warning"):
                    # Threshold just exceeded
                    self._trigger_threshold_event("warning", new_value, self.warning_threshold)
    
    def _exceeds_threshold(self, value: float, threshold: float, severity: str) -> bool:
        """Check if value exceeds threshold based on direction."""
        if self.threshold_direction == "above":
            return value > threshold
        elif self.threshold_direction == "below":
            return value < threshold
        else:  # between - not implemented for simplicity
            return False
    
    def _trigger_threshold_event(self, severity: str, current_value: float, threshold_value: float) -> None:
        """Trigger threshold exceeded event."""
        # This would typically integrate with an event system
        pass
    
    def get_status(self) -> str:
        """Get current status based on thresholds."""
        if self.last_value is None:
            return "unknown"
        
        if self.critical_threshold is not None:
            if self._exceeds_threshold(self.last_value, self.critical_threshold, "critical"):
                return "critical"
        
        if self.warning_threshold is not None:
            if self._exceeds_threshold(self.last_value, self.warning_threshold, "warning"):
                return "warning"
        
        return "normal"
    
    def format_value(self, value: float = None) -> str:
        """Format metric value for display."""
        display_value = value if value is not None else self.last_value
        if display_value is None:
            return "N/A"
        
        return self.format_string.format(value=display_value, unit=self.unit)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "display_name": self.display_name,
            "description": self.description,
            "unit": self.unit,
            "last_value": self.last_value,
            "formatted_value": self.format_value(),
            "status": self.get_status(),
            "thresholds": {
                "warning": self.warning_threshold,
                "critical": self.critical_threshold,
                "target": self.target_value,
                "direction": self.threshold_direction
            },
            "chart_config": {
                "type": self.chart_type,
                "config": self.chart_config
            },
            "position": self.dashboard_position,
            "last_updated_at": self.last_updated_at.isoformat() if self.last_updated_at else None,
            "is_active": self.is_active
        }