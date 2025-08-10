"""
Integration Data Transfer Objects.

DTOs for enterprise integration operations including connector management,
flow execution, and integration monitoring.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime


@dataclass
class CreateConnectorRequest:
    """Create integration connector request."""
    name: str
    description: str = ""
    connector_type: str  # IntegrationType value
    direction: str  # IntegrationDirection value
    input_format: str = "json"  # DataFormat value
    output_format: str = "json"  # DataFormat value
    source_endpoint: Optional[Dict[str, Any]] = None
    target_endpoint: Optional[Dict[str, Any]] = None
    transformations: List[Dict[str, Any]] = field(default_factory=list)
    error_handling: Dict[str, Any] = field(default_factory=dict)
    dead_letter_queue: Optional[str] = None
    health_check_config: Dict[str, Any] = field(default_factory=dict)
    monitoring_enabled: bool = True
    tags: List[str] = field(default_factory=list)
    auto_activate: bool = False


@dataclass
class CreateConnectorResponse:
    """Create integration connector response."""
    success: bool
    connector_id: Optional[str] = None
    message: str = ""
    connector: Optional[Dict[str, Any]] = None


@dataclass
class UpdateConnectorRequest:
    """Update integration connector request."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # ConnectorStatus value
    transformations: Optional[List[Dict[str, Any]]] = None
    error_handling: Optional[Dict[str, Any]] = None
    monitoring_enabled: Optional[bool] = None
    tags: Optional[List[str]] = None


@dataclass
class UpdateConnectorResponse:
    """Update integration connector response."""
    success: bool
    message: str = ""
    updated_fields: List[str] = field(default_factory=list)


@dataclass
class ConnectorResponse:
    """Single connector response."""
    success: bool
    connector: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class ListConnectorsResponse:
    """List connectors response."""
    success: bool
    connectors: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 50
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False
    message: str = ""


@dataclass
class ExecuteConnectorRequest:
    """Execute connector request."""
    connector_id: str
    input_data: Dict[str, Any]
    execution_context: Dict[str, Any] = field(default_factory=dict)
    timeout_override: Optional[int] = None


@dataclass
class ExecuteConnectorResponse:
    """Execute connector response."""
    success: bool
    execution_id: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[int] = None
    message: str = ""
    error_details: Optional[Dict[str, Any]] = None


@dataclass
class TestConnectorRequest:
    """Test connector request."""
    connector_id: str
    test_data: Optional[Dict[str, Any]] = None
    test_options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestConnectorResponse:
    """Test connector response."""
    success: bool
    test_result: str = ""  # passed, failed, warning
    validation_results: Dict[str, Any] = field(default_factory=dict)
    connectivity_test: Dict[str, Any] = field(default_factory=dict)
    transformation_test: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    message: str = ""


@dataclass
class CreateFlowRequest:
    """Create integration flow request."""
    name: str
    description: str = ""
    connector_ids: List[str] = field(default_factory=list)
    trigger_config: Dict[str, Any] = field(default_factory=dict)
    error_handling: Dict[str, Any] = field(default_factory=dict)
    parallel_execution: bool = False
    timeout_seconds: int = 300
    retry_config: Dict[str, Any] = field(default_factory=dict)
    auto_activate: bool = False


@dataclass
class CreateFlowResponse:
    """Create integration flow response."""
    success: bool
    flow_id: Optional[str] = None
    message: str = ""


@dataclass
class FlowExecutionResponse:
    """Flow execution response."""
    success: bool
    execution_id: Optional[str] = None
    flow_results: List[Dict[str, Any]] = field(default_factory=list)
    execution_time_ms: Optional[int] = None
    message: str = ""


@dataclass
class ConnectorStatsRequest:
    """Connector statistics request."""
    connector_id: str
    days: int = 30
    include_trends: bool = True
    include_error_analysis: bool = True


@dataclass
class ConnectorStatsResponse:
    """Connector statistics response."""
    success: bool
    statistics: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class IntegrationHealthResponse:
    """Integration health response."""
    success: bool
    overall_health: str = ""  # healthy, warning, unhealthy, no_connectors
    system_metrics: Dict[str, Any] = field(default_factory=dict)
    connector_health: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    message: str = ""


@dataclass
class ConnectorSearchRequest:
    """Connector search request."""
    query: str
    connector_type: Optional[str] = None
    status: Optional[str] = None
    direction: Optional[str] = None
    tags: Optional[List[str]] = None
    created_by: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    page: int = 1
    page_size: int = 50
    sort_by: str = "updated_at"  # name, created_at, updated_at, execution_count
    sort_order: str = "desc"  # asc, desc


@dataclass
class ConnectorSearchResponse:
    """Connector search response."""
    success: bool
    connectors: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    page_size: int = 50
    query: str = ""
    facets: Dict[str, Dict[str, int]] = field(default_factory=dict)
    message: str = ""


@dataclass
class BulkConnectorActionRequest:
    """Bulk connector action request."""
    connector_ids: List[str]
    action: str  # activate, deactivate, delete, test
    action_params: Dict[str, Any] = field(default_factory=dict)
    confirm: bool = False


@dataclass
class BulkConnectorActionResponse:
    """Bulk connector action response."""
    success: bool
    processed_count: int = 0
    failed_count: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""


@dataclass
class ConnectorTemplateRequest:
    """Connector template request."""
    name: str
    description: str
    connector_type: str
    template_data: Dict[str, Any]
    is_public: bool = False
    tags: List[str] = field(default_factory=list)


@dataclass
class ConnectorTemplateResponse:
    """Connector template response."""
    success: bool
    template_id: Optional[str] = None
    template: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class ListConnectorTemplatesResponse:
    """List connector templates response."""
    success: bool
    templates: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    categories: List[str] = field(default_factory=list)
    message: str = ""


@dataclass
class ConnectorValidationRequest:
    """Connector validation request."""
    connector_data: Dict[str, Any]
    strict_validation: bool = True
    check_connectivity: bool = False


@dataclass
class ConnectorValidationResponse:
    """Connector validation response."""
    success: bool
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    connectivity_status: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class ConnectorExportRequest:
    """Connector export request."""
    connector_ids: List[str]
    format: str = "json"  # json, yaml, xml
    include_statistics: bool = False
    include_templates: bool = False
    compression: str = "none"  # none, zip, gzip


@dataclass
class ConnectorExportResponse:
    """Connector export response."""
    success: bool
    export_id: Optional[str] = None
    download_url: Optional[str] = None
    file_size: int = 0
    format: str = ""
    expires_at: Optional[datetime] = None
    message: str = ""


@dataclass
class ConnectorImportRequest:
    """Connector import request."""
    import_data: Union[str, Dict[str, Any]]
    format: str = "json"  # json, yaml, xml
    conflict_resolution: str = "skip"  # skip, overwrite, rename
    validate_before_import: bool = True
    auto_activate: bool = False


@dataclass
class ConnectorImportResponse:
    """Connector import response."""
    success: bool
    imported_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    imported_connectors: List[Dict[str, Any]] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    message: str = ""


@dataclass
class ConnectorScheduleRequest:
    """Connector schedule request."""
    connector_id: str
    schedule_type: str  # cron, interval, once
    schedule_config: Dict[str, Any]
    timezone: str = "UTC"
    enabled: bool = True
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class ConnectorScheduleResponse:
    """Connector schedule response."""
    success: bool
    schedule_id: Optional[str] = None
    next_execution: Optional[datetime] = None
    schedule_info: Optional[Dict[str, Any]] = None
    message: str = ""


@dataclass
class IntegrationMonitoringRequest:
    """Integration monitoring request."""
    connector_ids: Optional[List[str]] = None
    flow_ids: Optional[List[str]] = None
    time_range: Optional[Dict[str, Any]] = None
    include_performance_metrics: bool = True
    include_error_details: bool = True
    include_data_flow: bool = False


@dataclass
class IntegrationMonitoringResponse:
    """Integration monitoring response."""
    success: bool
    monitoring_data: Optional[Dict[str, Any]] = None
    active_executions: List[Dict[str, Any]] = field(default_factory=list)
    performance_summary: Optional[Dict[str, Any]] = None
    error_summary: Optional[Dict[str, Any]] = None
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""


@dataclass
class IntegrationAnalyticsRequest:
    """Integration analytics request."""
    time_range: Dict[str, Any]
    connector_ids: Optional[List[str]] = None
    flow_ids: Optional[List[str]] = None
    metrics: List[str] = field(default_factory=list)
    group_by: Optional[str] = None  # connector_type, status, direction
    include_trends: bool = True
    include_comparisons: bool = False


@dataclass
class IntegrationAnalyticsResponse:
    """Integration analytics response."""
    success: bool
    analytics_data: Optional[Dict[str, Any]] = None
    summary_metrics: Optional[Dict[str, Any]] = None
    trends: Optional[Dict[str, Any]] = None
    comparisons: Optional[Dict[str, Any]] = None
    insights: List[Dict[str, Any]] = field(default_factory=list)
    message: str = ""


@dataclass
class DataMappingRequest:
    """Data mapping configuration request."""
    source_schema: Dict[str, Any]
    target_schema: Dict[str, Any]
    mapping_rules: List[Dict[str, Any]] = field(default_factory=list)
    auto_generate: bool = False
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DataMappingResponse:
    """Data mapping configuration response."""
    success: bool
    mapping_id: Optional[str] = None
    generated_mappings: List[Dict[str, Any]] = field(default_factory=list)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    compatibility_score: Optional[float] = None
    suggestions: List[str] = field(default_factory=list)
    message: str = ""


@dataclass
class TransformationTestRequest:
    """Transformation test request."""
    transformations: List[Dict[str, Any]]
    test_data: List[Dict[str, Any]]
    expected_results: Optional[List[Dict[str, Any]]] = None


@dataclass
class TransformationTestResponse:
    """Transformation test response."""
    success: bool
    test_results: List[Dict[str, Any]] = field(default_factory=list)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    message: str = ""


# Specialized DTOs for different integration types
@dataclass
class DatabaseConnectorRequest(CreateConnectorRequest):
    """Database connector request."""
    connection_string: str = ""
    database_type: str = ""  # mysql, postgresql, mssql, oracle
    query_config: Dict[str, Any] = field(default_factory=dict)
    connection_pool_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APIConnectorRequest(CreateConnectorRequest):
    """API connector request."""
    api_version: str = ""
    authentication_method: str = ""  # basic, oauth2, api_key, jwt
    rate_limiting: Dict[str, Any] = field(default_factory=dict)
    pagination_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MessageQueueConnectorRequest(CreateConnectorRequest):
    """Message queue connector request."""
    queue_type: str = ""  # rabbitmq, kafka, sqs, azure_service_bus
    topic_config: Dict[str, Any] = field(default_factory=dict)
    consumer_config: Dict[str, Any] = field(default_factory=dict)
    producer_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileSystemConnectorRequest(CreateConnectorRequest):
    """File system connector request."""
    file_path: str = ""
    file_pattern: str = ""
    processing_mode: str = "batch"  # batch, streaming
    archive_config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FTPConnectorRequest(CreateConnectorRequest):
    """FTP/SFTP connector request."""
    host: str = ""
    port: int = 21
    protocol: str = "ftp"  # ftp, sftp, ftps
    directory_config: Dict[str, Any] = field(default_factory=dict)
    transfer_mode: str = "binary"  # binary, ascii


# Response DTOs for specialized connectors
@dataclass
class DatabaseConnectorResponse(CreateConnectorResponse):
    """Database connector response."""
    connection_test: Optional[Dict[str, Any]] = None
    schema_info: Optional[Dict[str, Any]] = None


@dataclass
class APIConnectorResponse(CreateConnectorResponse):
    """API connector response."""
    api_discovery: Optional[Dict[str, Any]] = None
    endpoint_validation: Optional[Dict[str, Any]] = None


@dataclass
class MessageQueueConnectorResponse(CreateConnectorResponse):
    """Message queue connector response."""
    queue_info: Optional[Dict[str, Any]] = None
    subscription_details: Optional[Dict[str, Any]] = None


@dataclass
class FileSystemConnectorResponse(CreateConnectorResponse):
    """File system connector response."""
    directory_info: Optional[Dict[str, Any]] = None
    file_permissions: Optional[Dict[str, Any]] = None


@dataclass
class FTPConnectorResponse(CreateConnectorResponse):
    """FTP connector response."""
    server_info: Optional[Dict[str, Any]] = None
    directory_listing: Optional[List[Dict[str, Any]]] = None