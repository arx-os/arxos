"""
Workflow Data Transfer Objects.

DTOs for workflow automation operations including workflow creation,
execution, management, and monitoring.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


@dataclass
class WorkflowTriggerRequest:
    """Workflow trigger configuration request."""
    type: str  # TriggerType value
    name: str
    configuration: Dict[str, Any] = field(default_factory=dict)
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True


@dataclass
class WorkflowActionRequest:
    """Workflow action configuration request."""
    type: str  # ActionType value
    name: str
    configuration: Dict[str, Any] = field(default_factory=dict)
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    retry_count: int = 3
    timeout_seconds: int = 300
    enabled: bool = True


@dataclass
class WorkflowVariableRequest:
    """Workflow variable definition request."""
    name: str
    type: str  # string, number, boolean, object, array
    default_value: Any = None
    description: str = ""
    required: bool = False


@dataclass
class CreateWorkflowRequest:
    """Create workflow request."""
    name: str
    description: str = ""
    category: str = ""
    tags: List[str] = field(default_factory=list)
    priority: int = 5  # 1-10 scale
    timeout_seconds: int = 3600
    max_concurrent_executions: int = 1
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    variables: List[Dict[str, Any]] = field(default_factory=list)
    auto_activate: bool = False


@dataclass
class CreateWorkflowResponse:
    """Create workflow response."""
    success: bool
    workflow_id: Optional[str] = None
    message: str = ""
    workflow: Optional[Dict[str, Any]] = None


@dataclass
class UpdateWorkflowRequest:
    """Update workflow request."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[int] = None
    timeout_seconds: Optional[int] = None
    max_concurrent_executions: Optional[int] = None
    triggers: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    variables: Optional[List[Dict[str, Any]]] = None


@dataclass
class UpdateWorkflowResponse:
    """Update workflow response."""
    success: bool
    message: str = ""
    updated_fields: List[str] = field(default_factory=list)


@dataclass
class WorkflowResponse:
    """Single workflow response."""
    success: bool
    workflow: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class ListWorkflowsResponse:
    """List workflows response."""
    success: bool
    workflows: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 50
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False
    message: str = ""


@dataclass
class ExecuteWorkflowRequest:
    """Execute workflow request."""
    workflow_id: str
    variables: Optional[Dict[str, Any]] = None
    timeout_override: Optional[int] = None
    priority_override: Optional[int] = None


@dataclass
class ExecuteWorkflowResponse:
    """Execute workflow response."""
    success: bool
    execution_id: Optional[str] = None
    status: Optional[str] = None
    message: str = ""
    execution_details: Optional[Dict[str, Any]] = None


@dataclass
class TriggerWorkflowRequest:
    """Trigger workflow from event request."""
    event_type: str
    event_data: Dict[str, Any]
    source: str = "system"
    timestamp: Optional[datetime] = None


@dataclass
class WorkflowExecutionResponse:
    """Workflow execution details response."""
    success: bool
    execution: Optional[Dict[str, Any]] = None
    workflow_info: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class CloneWorkflowRequest:
    """Clone workflow request."""
    source_workflow_id: str
    new_name: str
    copy_executions: bool = False
    modifications: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowStatsRequest:
    """Workflow statistics request."""
    workflow_id: str
    days: int = 30
    include_trends: bool = True
    include_performance: bool = True
    include_failure_analysis: bool = True


@dataclass
class WorkflowStatsResponse:
    """Workflow statistics response."""
    success: bool
    statistics: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class WorkflowSearchRequest:
    """Workflow search request."""
    query: str
    status: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    created_by: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    execution_count_min: Optional[int] = None
    execution_count_max: Optional[int] = None
    success_rate_min: Optional[float] = None
    page: int = 1
    page_size: int = 50
    sort_by: str = "updated_at"  # name, created_at, updated_at, execution_count, success_rate
    sort_order: str = "desc"  # asc, desc


@dataclass
class WorkflowSearchResponse:
    """Workflow search response."""
    success: bool
    workflows: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 50
    query: str = ""
    facets: Dict[str, Dict[str, int]] = field(default_factory=dict)  # Categories, tags, status counts
    message: str = ""


@dataclass
class BulkWorkflowActionRequest:
    """Bulk workflow action request."""
    workflow_ids: List[str]
    action: str  # activate, deactivate, disable, delete, archive
    confirm: bool = False
    reason: str = ""


@dataclass
class BulkWorkflowActionResponse:
    """Bulk workflow action response."""
    success: bool
    processed_count: int = 0
    failed_count: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""


@dataclass
class WorkflowTemplateRequest:
    """Workflow template request."""
    name: str
    description: str
    category: str
    template_data: Dict[str, Any]
    is_public: bool = False
    tags: List[str] = field(default_factory=list)


@dataclass
class WorkflowTemplateResponse:
    """Workflow template response."""
    success: bool
    template_id: Optional[str] = None
    template: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class ListWorkflowTemplatesResponse:
    """List workflow templates response."""
    success: bool
    templates: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    categories: List[str] = field(default_factory=list)
    message: str = ""


@dataclass
class WorkflowValidationRequest:
    """Workflow validation request."""
    workflow_data: Dict[str, Any]
    strict_validation: bool = True
    check_dependencies: bool = True


@dataclass
class WorkflowValidationResponse:
    """Workflow validation response."""
    success: bool
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    message: str = ""


@dataclass
class WorkflowExportRequest:
    """Workflow export request."""
    workflow_ids: List[str]
    format: str = "json"  # json, yaml, xml
    include_executions: bool = False
    include_statistics: bool = False
    compression: str = "none"  # none, zip, gzip


@dataclass
class WorkflowExportResponse:
    """Workflow export response."""
    success: bool
    export_id: Optional[str] = None
    download_url: Optional[str] = None
    file_size: int = 0
    format: str = ""
    expires_at: Optional[datetime] = None
    message: str = ""


@dataclass
class WorkflowImportRequest:
    """Workflow import request."""
    import_data: Union[str, Dict[str, Any]]
    format: str = "json"  # json, yaml, xml
    conflict_resolution: str = "skip"  # skip, overwrite, rename
    validate_before_import: bool = True
    auto_activate: bool = False


@dataclass
class WorkflowImportResponse:
    """Workflow import response."""
    success: bool
    imported_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    imported_workflows: List[Dict[str, Any]] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    message: str = ""


@dataclass
class WorkflowScheduleRequest:
    """Workflow schedule request."""
    workflow_id: str
    schedule_type: str  # cron, interval, once
    schedule_config: Dict[str, Any]
    timezone: str = "UTC"
    enabled: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class WorkflowScheduleResponse:
    """Workflow schedule response."""
    success: bool
    schedule_id: Optional[str] = None
    next_execution: Optional[datetime] = None
    schedule_info: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class WorkflowMonitoringRequest:
    """Workflow monitoring request."""
    workflow_ids: Optional[List[str]] = None
    status_filter: Optional[List[str]] = None
    time_range: Optional[Dict[str, Any]] = None
    include_active_executions: bool = True
    include_performance_metrics: bool = True
    include_alerts: bool = True


@dataclass
class WorkflowMonitoringResponse:
    """Workflow monitoring response."""
    success: bool
    monitoring_data: Optional[Dict[str, Any]] = None
    active_executions: List[Dict[str, Any]] = field(default_factory=list)
    performance_summary: Optional[Dict[str, Any]] = None
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    system_health: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class WorkflowDebugRequest:
    """Workflow debug request."""
    workflow_id: str
    execution_id: Optional[str] = None
    include_context: bool = True
    include_action_details: bool = True
    include_variable_states: bool = True
    include_error_traces: bool = True


@dataclass
class WorkflowDebugResponse:
    """Workflow debug response."""
    success: bool
    debug_info: Optional[Dict[str, Any]] = None
    execution_trace: List[Dict[str, Any]] = field(default_factory=list)
    error_details: Optional[Dict[str, Any]] = None
    suggestions: List[str] = field(default_factory=list)
    message: str = ""


@dataclass
class WorkflowAnalyticsRequest:
    """Workflow analytics request."""
    time_range: Dict[str, Any]
    workflow_ids: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    metrics: List[str] = field(default_factory=list)
    group_by: Optional[str] = None  # category, status, created_by, etc.
    include_trends: bool = True
    include_comparisons: bool = False


@dataclass
class WorkflowAnalyticsResponse:
    """Workflow analytics response."""
    success: bool
    analytics_data: Optional[Dict[str, Any]] = None
    summary_metrics: Optional[Dict[str, Any]] = None
    trends: Optional[Dict[str, Any]] = None
    comparisons: Optional[Dict[str, Any]] = None
    insights: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""


# Specialized DTOs for different workflow types
@dataclass
class DeviceAutomationWorkflowRequest(CreateWorkflowRequest):
    """Device automation workflow request."""
    device_ids: List[str] = field(default_factory=list)
    device_types: List[str] = field(default_factory=list)
    automation_rules: List[Dict[str, Any]] = field(default_factory=list)
    safety_constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnergyOptimizationWorkflowRequest(CreateWorkflowRequest):
    """Energy optimization workflow request."""
    optimization_targets: List[str] = field(default_factory=list)  # reduce_consumption, shift_load, etc.
    energy_sources: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    savings_goals: Dict[str, float] = field(default_factory=dict)


@dataclass
class MaintenanceWorkflowRequest(CreateWorkflowRequest):
    """Maintenance workflow request."""
    maintenance_type: str  # preventive, reactive, predictive
    asset_ids: List[str] = field(default_factory=list)
    maintenance_schedule: Dict[str, Any] = field(default_factory=dict)
    escalation_rules: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SecurityWorkflowRequest(CreateWorkflowRequest):
    """Security workflow request."""
    security_level: str  # low, medium, high, critical
    monitored_areas: List[str] = field(default_factory=list)
    response_procedures: List[Dict[str, Any]] = field(default_factory=list)
    notification_contacts: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class EnvironmentalWorkflowRequest(CreateWorkflowRequest):
    """Environmental control workflow request."""
    environmental_zones: List[str] = field(default_factory=list)
    comfort_parameters: Dict[str, Dict[str, float]] = field(default_factory=dict)  # temp, humidity ranges
    energy_efficiency_priority: int = 5  # 1-10 scale
    occupancy_awareness: bool = True


# Response DTOs for specialized workflows
@dataclass
class DeviceAutomationWorkflowResponse(CreateWorkflowResponse):
    """Device automation workflow response."""
    controlled_devices: List[Dict[str, Any]] = field(default_factory=list)
    automation_summary: Optional[Dict[str, Any]] = None


@dataclass
class EnergyOptimizationWorkflowResponse(CreateWorkflowResponse):
    """Energy optimization workflow response."""
    optimization_potential: Optional[Dict[str, Any]] = None
    estimated_savings: Optional[Dict[str, float]] = None


@dataclass
class MaintenanceWorkflowResponse(CreateWorkflowResponse):
    """Maintenance workflow response."""
    maintenance_schedule: Optional[Dict[str, Any]] = None
    covered_assets: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class SecurityWorkflowResponse(CreateWorkflowResponse):
    """Security workflow response."""
    security_coverage: Optional[Dict[str, Any]] = None
    response_time_estimate: Optional[int] = None  # seconds


@dataclass
class EnvironmentalWorkflowResponse(CreateWorkflowResponse):
    """Environmental workflow response."""
    controlled_zones: List[Dict[str, Any]] = field(default_factory=list)
    comfort_score: Optional[float] = None