"""
Enterprise Integration Domain Entities.

Domain models for enterprise integration capabilities including connectors,
data mapping, transformation rules, and integration workflows.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timezone, timedelta
from enum import Enum
import json

from infrastructure.logging.structured_logging import get_logger


logger = get_logger(__name__)


class IntegrationType(Enum):
    """Types of enterprise integrations."""
    REST_API = "rest_api"
    SOAP_WEB_SERVICE = "soap_web_service"
    DATABASE = "database"
    MESSAGE_QUEUE = "message_queue"
    FILE_SYSTEM = "file_system"
    FTP_SFTP = "ftp_sftp"
    EMAIL = "email"
    WEBHOOK = "webhook"
    GRAPHQL = "graphql"
    ENTERPRISE_BUS = "enterprise_bus"
    CUSTOM = "custom"


class ConnectorStatus(Enum):
    """Connector status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"


class DataFormat(Enum):
    """Data format types."""
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    YAML = "yaml"
    AVRO = "avro"
    PROTOBUF = "protobuf"
    PLAIN_TEXT = "plain_text"
    BINARY = "binary"


class TransformationType(Enum):
    """Data transformation types."""
    FIELD_MAPPING = "field_mapping"
    VALUE_CONVERSION = "value_conversion"
    AGGREGATION = "aggregation"
    FILTERING = "filtering"
    ENRICHMENT = "enrichment"
    VALIDATION = "validation"
    CUSTOM_SCRIPT = "custom_script"


class IntegrationDirection(Enum):
    """Integration data flow direction."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class IntegrationEndpoint:
    """Integration endpoint configuration."""
    id: str
    name: str
    url: str
    integration_type: IntegrationType
    data_format: DataFormat
    authentication: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 30
    retry_config: Dict[str, Any] = field(default_factory=dict)
    rate_limit: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def validate_configuration(self) -> List[str]:
        """Validate endpoint configuration."""
        errors = []
        
        if not self.name.strip():
            errors.append("Endpoint name is required")
        
        if not self.url.strip():
            errors.append("Endpoint URL is required")
        
        if self.timeout_seconds <= 0:
            errors.append("Timeout seconds must be positive")
        
        # Validate authentication
        auth_type = self.authentication.get("type", "none")
        if auth_type == "basic" and not (
            self.authentication.get("username") and self.authentication.get("password")
        ):
            errors.append("Basic auth requires username and password")
        elif auth_type == "oauth2" and not self.authentication.get("token"):
            errors.append("OAuth2 auth requires token")
        elif auth_type == "api_key" and not (
            self.authentication.get("key") and self.authentication.get("value")
        ):
            errors.append("API key auth requires key and value")
        
        return errors


@dataclass
class DataTransformation:
    """Data transformation rule."""
    id: str
    name: str
    transformation_type: TransformationType
    source_field: Optional[str] = None
    target_field: Optional[str] = None
    transformation_logic: Dict[str, Any] = field(default_factory=dict)
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    order: int = 0

    def should_apply(self, data: Dict[str, Any]) -> bool:
        """Check if transformation should be applied."""
        if not self.enabled:
            return False
        
        if not self.conditions:
            return True
        
        for condition in self.conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")
            
            field_value = self._get_field_value(data, field)
            
            if not self._evaluate_condition(field_value, operator, value):
                return False
        
        return True
    
    def apply_transformation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply transformation to data."""
        try:
            result = data.copy()
            
            if self.transformation_type == TransformationType.FIELD_MAPPING:
                return self._apply_field_mapping(result)
            elif self.transformation_type == TransformationType.VALUE_CONVERSION:
                return self._apply_value_conversion(result)
            elif self.transformation_type == TransformationType.FILTERING:
                return self._apply_filtering(result)
            elif self.transformation_type == TransformationType.ENRICHMENT:
                return self._apply_enrichment(result)
            elif self.transformation_type == TransformationType.VALIDATION:
                return self._apply_validation(result)
            else:
                logger.warning(f"Unsupported transformation type: {self.transformation_type}")
                return result
                
        except Exception as e:
            logger.error(f"Transformation failed: {e}")
            return data
    
    def _apply_field_mapping(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply field mapping transformation."""
        mapping = self.transformation_logic.get("mapping", {})
        
        for source_field, target_field in mapping.items():
            value = self._get_field_value(data, source_field)
            if value is not None:
                self._set_field_value(data, target_field, value)
                
                # Remove source field if different from target
                if source_field != target_field and "." not in source_field:
                    data.pop(source_field, None)
        
        return data
    
    def _apply_value_conversion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply value conversion transformation."""
        field = self.source_field or self.target_field
        if not field:
            return data
        
        value = self._get_field_value(data, field)
        if value is None:
            return data
        
        conversion_type = self.transformation_logic.get("conversion_type")
        
        if conversion_type == "string":
            converted_value = str(value)
        elif conversion_type == "number":
            converted_value = float(value) if "." in str(value) else int(value)
        elif conversion_type == "boolean":
            converted_value = bool(value) if not isinstance(value, str) else value.lower() in ["true", "1", "yes", "on"]
        elif conversion_type == "date":
            from datetime import datetime
            if isinstance(value, str):
                converted_value = datetime.fromisoformat(value).isoformat()
            else:
                converted_value = value
        else:
            converted_value = value
        
        self._set_field_value(data, self.target_field or field, converted_value)
        return data
    
    def _apply_filtering(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply filtering transformation."""
        include_fields = self.transformation_logic.get("include_fields", [])
        exclude_fields = self.transformation_logic.get("exclude_fields", [])
        
        if include_fields:
            # Only keep specified fields
            filtered_data = {}
            for field in include_fields:
                value = self._get_field_value(data, field)
                if value is not None:
                    self._set_field_value(filtered_data, field, value)
            return filtered_data
        
        if exclude_fields:
            # Remove specified fields
            result = data.copy()
            for field in exclude_fields:
                self._remove_field(result, field)
            return result
        
        return data
    
    def _apply_enrichment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply data enrichment transformation."""
        enrichments = self.transformation_logic.get("enrichments", {})
        
        for field, enrichment_config in enrichments.items():
            if enrichment_config.get("type") == "static_value":
                self._set_field_value(data, field, enrichment_config.get("value"))
            elif enrichment_config.get("type") == "calculated":
                # Simple calculation support
                expression = enrichment_config.get("expression", "")
                if expression:
                    try:
                        # Basic expression evaluation (production would use safer evaluation)
                        calculated_value = eval(expression, {"data": data})
                        self._set_field_value(data, field, calculated_value)
                    except Exception as e:
                        logger.warning(f"Calculation failed for field {field}: {e}")
        
        return data
    
    def _apply_validation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply validation transformation."""
        validations = self.transformation_logic.get("validations", {})
        
        for field, validation_config in validations.items():
            value = self._get_field_value(data, field)
            
            if validation_config.get("required", False) and value is None:
                raise ValueError(f"Required field {field} is missing")
            
            if value is not None:
                min_length = validation_config.get("min_length")
                max_length = validation_config.get("max_length")
                
                if min_length and len(str(value)) < min_length:
                    raise ValueError(f"Field {field} is too short (minimum {min_length})")
                
                if max_length and len(str(value)) > max_length:
                    raise ValueError(f"Field {field} is too long (maximum {max_length})")
                
                pattern = validation_config.get("pattern")
                if pattern:
                    import re
                    if not re.match(pattern, str(value)):
                        raise ValueError(f"Field {field} does not match required pattern")
        
        return data
    
    def _get_field_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get field value using dot notation."""
        if not field_path:
            return None
        
        keys = field_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _set_field_value(self, data: Dict[str, Any], field_path: str, value: Any) -> None:
        """Set field value using dot notation."""
        if not field_path:
            return
        
        keys = field_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _remove_field(self, data: Dict[str, Any], field_path: str) -> None:
        """Remove field using dot notation."""
        if not field_path:
            return
        
        keys = field_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return
        
        if isinstance(current, dict):
            current.pop(keys[-1], None)
    
    def _evaluate_condition(self, field_value: Any, operator: str, expected_value: Any) -> bool:
        """Evaluate condition."""
        try:
            if operator == "equals":
                return field_value == expected_value
            elif operator == "not_equals":
                return field_value != expected_value
            elif operator == "greater_than":
                return float(field_value) > float(expected_value)
            elif operator == "less_than":
                return float(field_value) < float(expected_value)
            elif operator == "contains":
                return expected_value in str(field_value)
            elif operator == "exists":
                return field_value is not None
            else:
                return True
        except (ValueError, TypeError):
            return False


@dataclass
class IntegrationConnector:
    """Enterprise integration connector."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    connector_type: IntegrationType = IntegrationType.REST_API
    direction: IntegrationDirection = IntegrationDirection.BIDIRECTIONAL
    status: ConnectorStatus = ConnectorStatus.INACTIVE
    
    # Endpoint configurations
    source_endpoint: Optional[IntegrationEndpoint] = None
    target_endpoint: Optional[IntegrationEndpoint] = None
    
    # Data processing
    input_format: DataFormat = DataFormat.JSON
    output_format: DataFormat = DataFormat.JSON
    transformations: List[DataTransformation] = field(default_factory=list)
    
    # Error handling
    error_handling: Dict[str, Any] = field(default_factory=dict)
    dead_letter_queue: Optional[str] = None
    
    # Monitoring and metrics
    health_check_config: Dict[str, Any] = field(default_factory=dict)
    monitoring_enabled: bool = True
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = ""
    tags: List[str] = field(default_factory=list)
    
    # Runtime statistics
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    last_executed_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    average_execution_time_ms: float = 0.0

    def validate(self) -> List[str]:
        """Validate connector configuration."""
        errors = []
        
        if not self.name.strip():
            errors.append("Connector name is required")
        
        if self.direction in [IntegrationDirection.INBOUND, IntegrationDirection.BIDIRECTIONAL]:
            if not self.source_endpoint:
                errors.append("Source endpoint is required for inbound/bidirectional connectors")
            else:
                errors.extend(self.source_endpoint.validate_configuration())
        
        if self.direction in [IntegrationDirection.OUTBOUND, IntegrationDirection.BIDIRECTIONAL]:
            if not self.target_endpoint:
                errors.append("Target endpoint is required for outbound/bidirectional connectors")
            else:
                errors.extend(self.target_endpoint.validate_configuration())
        
        # Validate transformations
        for transformation in self.transformations:
            if not transformation.enabled:
                continue
            
            if not transformation.name.strip():
                errors.append(f"Transformation {transformation.id} name is required")
        
        return errors
    
    def can_execute(self) -> bool:
        """Check if connector can be executed."""
        return (
            self.status == ConnectorStatus.ACTIVE and
            len(self.validate()) == 0
        )
    
    def apply_transformations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply all transformations to data."""
        result = data.copy()
        
        # Sort transformations by order
        sorted_transformations = sorted(
            [t for t in self.transformations if t.enabled],
            key=lambda x: x.order
        )
        
        for transformation in sorted_transformations:
            if transformation.should_apply(result):
                try:
                    result = transformation.apply_transformation(result)
                    logger.debug(f"Applied transformation: {transformation.name}")
                except Exception as e:
                    logger.error(f"Transformation {transformation.name} failed: {e}")
                    if self.error_handling.get("stop_on_transformation_error", False):
                        raise
        
        return result
    
    def record_execution(self, success: bool, execution_time_ms: int = 0) -> None:
        """Record execution statistics."""
        now = datetime.now(timezone.utc)
        
        self.execution_count += 1
        self.last_executed_at = now
        
        if success:
            self.success_count += 1
            self.last_success_at = now
        else:
            self.failure_count += 1
            self.last_failure_at = now
        
        # Update average execution time
        if execution_time_ms > 0:
            total_time = self.average_execution_time_ms * (self.execution_count - 1)
            self.average_execution_time_ms = (total_time + execution_time_ms) / self.execution_count
    
    def get_success_rate(self) -> float:
        """Get success rate percentage."""
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get connector health status."""
        now = datetime.now(timezone.utc)
        
        # Check if recently executed successfully
        recently_successful = False
        if self.last_success_at:
            time_since_success = (now - self.last_success_at).total_seconds() / 3600  # hours
            recently_successful = time_since_success < 24
        
        # Check success rate
        success_rate = self.get_success_rate()
        
        # Determine health status
        if self.status != ConnectorStatus.ACTIVE:
            health = "inactive"
        elif success_rate >= 95 and recently_successful:
            health = "healthy"
        elif success_rate >= 80:
            health = "warning"
        else:
            health = "unhealthy"
        
        return {
            "health": health,
            "success_rate": success_rate,
            "execution_count": self.execution_count,
            "last_executed": self.last_executed_at.isoformat() if self.last_executed_at else None,
            "last_success": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_failure": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "average_execution_time_ms": self.average_execution_time_ms
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert connector to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "connector_type": self.connector_type.value,
            "direction": self.direction.value,
            "status": self.status.value,
            "input_format": self.input_format.value,
            "output_format": self.output_format.value,
            "transformations_count": len(self.transformations),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "tags": self.tags,
            "statistics": {
                "execution_count": self.execution_count,
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "success_rate": self.get_success_rate(),
                "average_execution_time_ms": self.average_execution_time_ms
            },
            "health": self.get_health_status()
        }


@dataclass
class IntegrationFlow:
    """Integration flow definition."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    connectors: List[str] = field(default_factory=list)  # Connector IDs in execution order
    trigger_config: Dict[str, Any] = field(default_factory=dict)
    error_handling: Dict[str, Any] = field(default_factory=dict)
    parallel_execution: bool = False
    timeout_seconds: int = 300
    retry_config: Dict[str, Any] = field(default_factory=dict)
    
    enabled: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = ""
    
    def validate(self) -> List[str]:
        """Validate integration flow."""
        errors = []
        
        if not self.name.strip():
            errors.append("Flow name is required")
        
        if not self.connectors:
            errors.append("At least one connector is required")
        
        if self.timeout_seconds <= 0:
            errors.append("Timeout must be positive")
        
        return errors