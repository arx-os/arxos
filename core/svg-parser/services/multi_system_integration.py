"""
Multi-System Integration Framework Service

Provides comprehensive integration framework for CMMS, ERP, SCADA, BMS, and IoT systems
with advanced data transformation, field mapping, and real-time synchronization capabilities.
"""

import json
import time
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import aiohttp
import redis
from sqlalchemy import text
from sqlalchemy.orm import Session
import numpy as np
from cryptography.fernet import Fernet
import jwt

from .base_manager import BaseManager
from models.database import get_db
from utils.auth import get_current_user
from utils.logging_config import get_logger

logger = get_logger(__name__)


class SystemType(Enum):
    """Supported external system types."""
    CMMS = "cmms"
    ERP = "erp"
    SCADA = "scada"
    BMS = "bms"
    IOT = "iot"
    CUSTOM = "custom"


class ConnectionStatus(Enum):
    """Connection status enumeration."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class SyncDirection(Enum):
    """Synchronization direction."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    ARXOS_WINS = "arxos_wins"
    EXTERNAL_WINS = "external_wins"
    MANUAL = "manual"
    MERGE = "merge"
    TIMESTAMP_BASED = "timestamp_based"


@dataclass
class SystemConnection:
    """System connection configuration."""
    system_id: str
    system_type: SystemType
    connection_name: str
    host: str
    port: int
    username: str
    password: str
    database: Optional[str] = None
    api_key: Optional[str] = None
    ssl_enabled: bool = True
    timeout: int = 30
    retry_attempts: int = 3
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    last_sync: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class FieldMapping:
    """Field mapping configuration."""
    mapping_id: str
    system_id: str
    arxos_field: str
    external_field: str
    transformation_rule: Optional[str] = None
    is_required: bool = False
    data_type: str = "string"
    validation_rule: Optional[str] = None
    created_at: datetime = None


@dataclass
class TransformationRule:
    """Data transformation rule."""
    rule_id: str
    rule_name: str
    rule_type: str  # calculation, validation, formatting
    rule_expression: str
    input_fields: List[str]
    output_field: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = None


@dataclass
class SyncResult:
    """Synchronization result."""
    sync_id: str
    system_id: str
    direction: SyncDirection
    records_processed: int
    records_successful: int
    records_failed: int
    conflicts_resolved: int
    sync_duration: float
    status: str
    error_message: Optional[str] = None
    timestamp: datetime = None


class MultiSystemIntegration(BaseManager):
    """
    Multi-System Integration Framework service providing connectors for
    CMMS, ERP, SCADA, BMS, and IoT systems with advanced data transformation.
    """
    
    def __init__(self):
        super().__init__()
        self.connections = {}
        self.transformers = {}
        self.sync_queue = []
        self.connection_pool = {}
        self.redis_client = None
        self._lock = threading.RLock()
        self._sync_lock = threading.RLock()
        
        # Initialize system connectors
        self._initialize_connectors()
        
        # Initialize transformation engine
        self._initialize_transformation_engine()
        
        # Initialize connection monitoring
        self._start_connection_monitoring()
        
        logger.info("Multi-System Integration Framework initialized")
    
    def _initialize_connectors(self):
        """Initialize system connectors for different external systems."""
        self.connectors = {
            SystemType.CMMS: {
                "maximo": self._create_maximo_connector,
                "sap_pm": self._create_sap_pm_connector,
                "infor": self._create_infor_connector,
                "custom": self._create_custom_connector
            },
            SystemType.ERP: {
                "sap": self._create_sap_connector,
                "oracle": self._create_oracle_connector,
                "dynamics": self._create_dynamics_connector,
                "custom": self._create_custom_connector
            },
            SystemType.SCADA: {
                "honeywell": self._create_honeywell_connector,
                "siemens": self._create_siemens_connector,
                "abb": self._create_abb_connector,
                "custom": self._create_custom_connector
            },
            SystemType.BMS: {
                "honeywell_bms": self._create_honeywell_bms_connector,
                "siemens_bms": self._create_siemens_bms_connector,
                "johnson": self._create_johnson_connector,
                "custom": self._create_custom_connector
            },
            SystemType.IOT: {
                "modbus": self._create_modbus_connector,
                "bacnet": self._create_bacnet_connector,
                "mqtt": self._create_mqtt_connector,
                "custom": self._create_custom_connector
            }
        }
        logger.info("System connectors initialized")
    
    def _initialize_transformation_engine(self):
        """Initialize data transformation engine."""
        self.transformation_engine = {
            "calculations": {
                "add": lambda x, y: x + y,
                "subtract": lambda x, y: x - y,
                "multiply": lambda x, y: x * y,
                "divide": lambda x, y: x / y if y != 0 else 0,
                "percentage": lambda x, total: (x / total * 100) if total != 0 else 0,
                "average": lambda values: sum(values) / len(values) if values else 0,
                "sum": lambda values: sum(values) if values else 0,
                "max": lambda values: max(values) if values else 0,
                "min": lambda values: min(values) if values else 0
            },
            "validations": {
                "required": lambda value: value is not None and str(value).strip() != "",
                "email": lambda value: "@" in str(value) if value else False,
                "phone": lambda value: len(str(value).replace("-", "").replace("(", "").replace(")", "")) >= 10 if value else False,
                "numeric": lambda value: str(value).replace(".", "").replace("-", "").isdigit() if value else False,
                "date": lambda value: self._is_valid_date(value) if value else False,
                "range": lambda value, min_val, max_val: min_val <= float(value) <= max_val if value else False
            },
            "formatting": {
                "uppercase": lambda value: str(value).upper() if value else "",
                "lowercase": lambda value: str(value).lower() if value else "",
                "titlecase": lambda value: str(value).title() if value else "",
                "trim": lambda value: str(value).strip() if value else "",
                "date_format": lambda value, format_str: self._format_date(value, format_str) if value else "",
                "number_format": lambda value, precision: round(float(value), precision) if value else 0
            }
        }
        logger.info("Transformation engine initialized")
    
    def create_system_connection(self, connection_config: Dict[str, Any]) -> SystemConnection:
        """
        Create a new system connection.
        
        Args:
            connection_config: Connection configuration dictionary
            
        Returns:
            SystemConnection object
        """
        try:
            with self._lock:
                # Validate connection configuration
                self._validate_connection_config(connection_config)
                
                # Create connection object
                connection = SystemConnection(
                    system_id=connection_config["system_id"],
                    system_type=SystemType(connection_config["system_type"]),
                    connection_name=connection_config["connection_name"],
                    host=connection_config["host"],
                    port=connection_config["port"],
                    username=connection_config["username"],
                    password=connection_config["password"],
                    database=connection_config.get("database"),
                    api_key=connection_config.get("api_key"),
                    ssl_enabled=connection_config.get("ssl_enabled", True),
                    timeout=connection_config.get("timeout", 30),
                    retry_attempts=connection_config.get("retry_attempts", 3),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                # Store connection
                self.connections[connection.system_id] = connection
                
                # Log connection creation
                self._log_integration_event("connection_created", {
                    "system_id": connection.system_id,
                    "system_type": connection.system_type.value,
                    "host": connection.host
                })
                
                logger.info(f"System connection created: {connection.system_id}")
                return connection
                
        except Exception as e:
            logger.error(f"Error creating system connection: {e}")
            raise
    
    def _validate_connection_config(self, config: Dict[str, Any]):
        """Validate connection configuration."""
        required_fields = ["system_id", "system_type", "connection_name", "host", "port", "username", "password"]
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        if not isinstance(config["port"], int) or config["port"] <= 0:
            raise ValueError("Port must be a positive integer")
        
        if config["system_type"] not in [t.value for t in SystemType]:
            raise ValueError(f"Invalid system type: {config['system_type']}")
    
    def test_connection(self, system_id: str) -> Dict[str, Any]:
        """
        Test system connection.
        
        Args:
            system_id: System connection ID
            
        Returns:
            Connection test results
        """
        try:
            with self._lock:
                if system_id not in self.connections:
                    raise ValueError(f"System connection not found: {system_id}")
                
                connection = self.connections[system_id]
                
                # Update status to connecting
                connection.status = ConnectionStatus.CONNECTING
                
                # Test connection based on system type
                test_result = self._test_system_connection(connection)
                
                # Update connection status
                connection.status = ConnectionStatus.CONNECTED if test_result["success"] else ConnectionStatus.ERROR
                connection.updated_at = datetime.now()
                
                # Log test result
                self._log_integration_event("connection_tested", {
                    "system_id": system_id,
                    "success": test_result["success"],
                    "response_time": test_result.get("response_time", 0)
                })
                
                return test_result
                
        except Exception as e:
            logger.error(f"Error testing connection: {e}")
            raise
    
    def _test_system_connection(self, connection: SystemConnection) -> Dict[str, Any]:
        """Test specific system connection."""
        start_time = time.time()
        
        try:
            if connection.system_type == SystemType.CMMS:
                return self._test_cmms_connection(connection)
            elif connection.system_type == SystemType.ERP:
                return self._test_erp_connection(connection)
            elif connection.system_type == SystemType.SCADA:
                return self._test_scada_connection(connection)
            elif connection.system_type == SystemType.BMS:
                return self._test_bms_connection(connection)
            elif connection.system_type == SystemType.IOT:
                return self._test_iot_connection(connection)
            else:
                return {"success": False, "error": f"Unsupported system type: {connection.system_type}"}
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }
    
    def _test_cmms_connection(self, connection: SystemConnection) -> Dict[str, Any]:
        """Test CMMS system connection."""
        # Simulate CMMS connection test
        time.sleep(0.1)  # Simulate network delay
        
        return {
            "success": True,
            "system_type": "CMMS",
            "capabilities": ["work_orders", "equipment", "preventive_maintenance"],
            "response_time": 0.1
        }
    
    def _test_erp_connection(self, connection: SystemConnection) -> Dict[str, Any]:
        """Test ERP system connection."""
        # Simulate ERP connection test
        time.sleep(0.15)  # Simulate network delay
        
        return {
            "success": True,
            "system_type": "ERP",
            "capabilities": ["financial_data", "inventory", "procurement"],
            "response_time": 0.15
        }
    
    def _test_scada_connection(self, connection: SystemConnection) -> Dict[str, Any]:
        """Test SCADA system connection."""
        # Simulate SCADA connection test
        time.sleep(0.2)  # Simulate network delay
        
        return {
            "success": True,
            "system_type": "SCADA",
            "capabilities": ["real_time_data", "alarms", "control_commands"],
            "response_time": 0.2
        }
    
    def _test_bms_connection(self, connection: SystemConnection) -> Dict[str, Any]:
        """Test BMS system connection."""
        # Simulate BMS connection test
        time.sleep(0.12)  # Simulate network delay
        
        return {
            "success": True,
            "system_type": "BMS",
            "capabilities": ["hvac_control", "lighting", "security"],
            "response_time": 0.12
        }
    
    def _test_iot_connection(self, connection: SystemConnection) -> Dict[str, Any]:
        """Test IoT device connection."""
        # Simulate IoT connection test
        time.sleep(0.08)  # Simulate network delay
        
        return {
            "success": True,
            "system_type": "IoT",
            "capabilities": ["sensor_data", "device_control", "status_monitoring"],
            "response_time": 0.08
        }
    
    def create_field_mapping(self, mapping_config: Dict[str, Any]) -> FieldMapping:
        """
        Create field mapping between Arxos and external system.
        
        Args:
            mapping_config: Field mapping configuration
            
        Returns:
            FieldMapping object
        """
        try:
            with self._lock:
                # Validate mapping configuration
                self._validate_mapping_config(mapping_config)
                
                # Create mapping object
                mapping = FieldMapping(
                    mapping_id=mapping_config["mapping_id"],
                    system_id=mapping_config["system_id"],
                    arxos_field=mapping_config["arxos_field"],
                    external_field=mapping_config["external_field"],
                    transformation_rule=mapping_config.get("transformation_rule"),
                    is_required=mapping_config.get("is_required", False),
                    data_type=mapping_config.get("data_type", "string"),
                    validation_rule=mapping_config.get("validation_rule"),
                    created_at=datetime.now()
                )
                
                # Store mapping
                if mapping.system_id not in self.transformers:
                    self.transformers[mapping.system_id] = {}
                
                self.transformers[mapping.system_id][mapping.mapping_id] = mapping
                
                # Log mapping creation
                self._log_integration_event("field_mapping_created", {
                    "mapping_id": mapping.mapping_id,
                    "system_id": mapping.system_id,
                    "arxos_field": mapping.arxos_field,
                    "external_field": mapping.external_field
                })
                
                logger.info(f"Field mapping created: {mapping.mapping_id}")
                return mapping
                
        except Exception as e:
            logger.error(f"Error creating field mapping: {e}")
            raise
    
    def _validate_mapping_config(self, config: Dict[str, Any]):
        """Validate field mapping configuration."""
        required_fields = ["mapping_id", "system_id", "arxos_field", "external_field"]
        
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        if config["system_id"] not in self.connections:
            raise ValueError(f"System connection not found: {config['system_id']}")
    
    def transform_data(self, data: Dict[str, Any], system_id: str, direction: str) -> Dict[str, Any]:
        """
        Transform data between Arxos and external system format.
        
        Args:
            data: Data to transform
            system_id: Target system ID
            direction: Transformation direction ("inbound" or "outbound")
            
        Returns:
            Transformed data
        """
        try:
            with self._lock:
                if system_id not in self.transformers:
                    return data  # No transformations defined
                
                mappings = self.transformers[system_id]
                transformed_data = {}
                
                for mapping_id, mapping in mappings.items():
                    if direction == "outbound":
                        # Transform from Arxos to external system
                        source_field = mapping.arxos_field
                        target_field = mapping.external_field
                    else:
                        # Transform from external system to Arxos
                        source_field = mapping.external_field
                        target_field = mapping.arxos_field
                    
                    if source_field in data:
                        value = data[source_field]
                        
                        # Apply transformation rule if specified
                        if mapping.transformation_rule:
                            value = self._apply_transformation_rule(value, mapping.transformation_rule)
                        
                        # Apply validation if specified
                        if mapping.validation_rule:
                            if not self._apply_validation_rule(value, mapping.validation_rule):
                                logger.warning(f"Validation failed for field {source_field}: {value}")
                                if mapping.is_required:
                                    raise ValueError(f"Required field validation failed: {source_field}")
                        
                        transformed_data[target_field] = value
                
                # Log transformation
                self._log_integration_event("data_transformed", {
                    "system_id": system_id,
                    "direction": direction,
                    "fields_transformed": len(transformed_data)
                })
                
                return transformed_data
                
        except Exception as e:
            logger.error(f"Error transforming data: {e}")
            raise
    
    def _apply_transformation_rule(self, value: Any, rule: str) -> Any:
        """Apply transformation rule to value."""
        try:
            # Parse rule (format: "type:operation:parameters")
            parts = rule.split(":")
            rule_type = parts[0]
            operation = parts[1]
            parameters = parts[2:] if len(parts) > 2 else []
            
            if rule_type == "calculation":
                return self._apply_calculation(value, operation, parameters)
            elif rule_type == "validation":
                return self._apply_validation(value, operation, parameters)
            elif rule_type == "formatting":
                return self._apply_formatting(value, operation, parameters)
            else:
                return value
                
        except Exception as e:
            logger.error(f"Error applying transformation rule: {e}")
            return value
    
    def _apply_calculation(self, value: Any, operation: str, parameters: List[str]) -> Any:
        """Apply calculation transformation."""
        if operation in self.transformation_engine["calculations"]:
            if len(parameters) == 1:
                # Single parameter calculation
                param_value = float(parameters[0])
                return self.transformation_engine["calculations"][operation](float(value), param_value)
            else:
                # Multi-value calculation
                return self.transformation_engine["calculations"][operation]([float(value)] + [float(p) for p in parameters])
        return value
    
    def _apply_validation(self, value: Any, operation: str, parameters: List[str]) -> Any:
        """Apply validation transformation."""
        if operation in self.transformation_engine["validations"]:
            if operation == "range" and len(parameters) >= 2:
                return self.transformation_engine["validations"][operation](value, float(parameters[0]), float(parameters[1]))
            else:
                return self.transformation_engine["validations"][operation](value)
        return value
    
    def _apply_formatting(self, value: Any, operation: str, parameters: List[str]) -> Any:
        """Apply formatting transformation."""
        if operation in self.transformation_engine["formatting"]:
            if operation == "date_format" and parameters:
                return self.transformation_engine["formatting"][operation](value, parameters[0])
            elif operation == "number_format" and parameters:
                return self.transformation_engine["formatting"][operation](value, int(parameters[0]))
            else:
                return self.transformation_engine["formatting"][operation](value)
        return value
    
    def _apply_validation_rule(self, value: Any, rule: str) -> bool:
        """Apply validation rule to value."""
        try:
            # Parse validation rule
            parts = rule.split(":")
            validation_type = parts[0]
            parameters = parts[1:] if len(parts) > 1 else []
            
            if validation_type in self.transformation_engine["validations"]:
                if validation_type == "range" and len(parameters) >= 2:
                    return self.transformation_engine["validations"][validation_type](value, float(parameters[0]), float(parameters[1]))
                else:
                    return self.transformation_engine["validations"][validation_type](value)
            return True
            
        except Exception as e:
            logger.error(f"Error applying validation rule: {e}")
            return False
    
    def sync_data(self, system_id: str, direction: SyncDirection, 
                  data: List[Dict[str, Any]], conflict_resolution: ConflictResolution = ConflictResolution.TIMESTAMP_BASED) -> SyncResult:
        """
        Synchronize data with external system.
        
        Args:
            system_id: Target system ID
            direction: Sync direction
            data: Data to synchronize
            conflict_resolution: Conflict resolution strategy
            
        Returns:
            SyncResult object
        """
        try:
            with self._sync_lock:
                start_time = time.time()
                sync_id = f"sync_{int(time.time())}_{hash(system_id)}"
                
                # Validate system connection
                if system_id not in self.connections:
                    raise ValueError(f"System connection not found: {system_id}")
                
                connection = self.connections[system_id]
                if connection.status != ConnectionStatus.CONNECTED:
                    raise ValueError(f"System not connected: {system_id}")
                
                # Transform data
                transformed_data = []
                for record in data:
                    transformed_record = self.transform_data(record, system_id, direction.value)
                    transformed_data.append(transformed_record)
                
                # Perform synchronization
                sync_result = self._perform_sync(connection, direction, transformed_data, conflict_resolution)
                
                # Update connection last sync time
                connection.last_sync = datetime.now()
                connection.updated_at = datetime.now()
                
                # Create sync result
                result = SyncResult(
                    sync_id=sync_id,
                    system_id=system_id,
                    direction=direction,
                    records_processed=len(data),
                    records_successful=sync_result["successful"],
                    records_failed=sync_result["failed"],
                    conflicts_resolved=sync_result["conflicts"],
                    sync_duration=time.time() - start_time,
                    status="completed" if sync_result["failed"] == 0 else "partial",
                    error_message=sync_result.get("error"),
                    timestamp=datetime.now()
                )
                
                # Log sync result
                self._log_integration_event("data_synced", {
                    "sync_id": sync_id,
                    "system_id": system_id,
                    "direction": direction.value,
                    "records_processed": result.records_processed,
                    "records_successful": result.records_successful,
                    "conflicts_resolved": result.conflicts_resolved,
                    "sync_duration": result.sync_duration
                })
                
                logger.info(f"Data sync completed: {sync_id} - {result.records_successful}/{result.records_processed} successful")
                return result
                
        except Exception as e:
            logger.error(f"Error syncing data: {e}")
            raise
    
    def _perform_sync(self, connection: SystemConnection, direction: SyncDirection, 
                      data: List[Dict[str, Any]], conflict_resolution: ConflictResolution) -> Dict[str, Any]:
        """Perform actual synchronization with external system."""
        successful = 0
        failed = 0
        conflicts = 0
        
        try:
            for record in data:
                try:
                    # Simulate sync operation based on system type
                    if connection.system_type == SystemType.CMMS:
                        result = self._sync_cmms_record(connection, record, direction)
                    elif connection.system_type == SystemType.ERP:
                        result = self._sync_erp_record(connection, record, direction)
                    elif connection.system_type == SystemType.SCADA:
                        result = self._sync_scada_record(connection, record, direction)
                    elif connection.system_type == SystemType.BMS:
                        result = self._sync_bms_record(connection, record, direction)
                    elif connection.system_type == SystemType.IOT:
                        result = self._sync_iot_record(connection, record, direction)
                    else:
                        result = {"success": False, "error": f"Unsupported system type: {connection.system_type}"}
                    
                    if result["success"]:
                        successful += 1
                        if result.get("conflict_resolved"):
                            conflicts += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    failed += 1
                    logger.error(f"Error syncing record: {e}")
            
            return {
                "successful": successful,
                "failed": failed,
                "conflicts": conflicts,
                "error": None if failed == 0 else f"{failed} records failed to sync"
            }
            
        except Exception as e:
            return {
                "successful": successful,
                "failed": failed,
                "conflicts": conflicts,
                "error": str(e)
            }
    
    def _sync_cmms_record(self, connection: SystemConnection, record: Dict[str, Any], direction: SyncDirection) -> Dict[str, Any]:
        """Sync record with CMMS system."""
        # Simulate CMMS sync
        time.sleep(0.05)  # Simulate processing time
        
        # Simulate conflict resolution
        has_conflict = np.random.random() < 0.1  # 10% chance of conflict
        
        return {
            "success": True,
            "conflict_resolved": has_conflict,
            "external_id": f"cmms_{hash(str(record)) % 10000}"
        }
    
    def _sync_erp_record(self, connection: SystemConnection, record: Dict[str, Any], direction: SyncDirection) -> Dict[str, Any]:
        """Sync record with ERP system."""
        # Simulate ERP sync
        time.sleep(0.08)  # Simulate processing time
        
        return {
            "success": True,
            "conflict_resolved": False,
            "external_id": f"erp_{hash(str(record)) % 10000}"
        }
    
    def _sync_scada_record(self, connection: SystemConnection, record: Dict[str, Any], direction: SyncDirection) -> Dict[str, Any]:
        """Sync record with SCADA system."""
        # Simulate SCADA sync
        time.sleep(0.03)  # Simulate processing time
        
        return {
            "success": True,
            "conflict_resolved": False,
            "external_id": f"scada_{hash(str(record)) % 10000}"
        }
    
    def _sync_bms_record(self, connection: SystemConnection, record: Dict[str, Any], direction: SyncDirection) -> Dict[str, Any]:
        """Sync record with BMS system."""
        # Simulate BMS sync
        time.sleep(0.06)  # Simulate processing time
        
        return {
            "success": True,
            "conflict_resolved": False,
            "external_id": f"bms_{hash(str(record)) % 10000}"
        }
    
    def _sync_iot_record(self, connection: SystemConnection, record: Dict[str, Any], direction: SyncDirection) -> Dict[str, Any]:
        """Sync record with IoT system."""
        # Simulate IoT sync
        time.sleep(0.02)  # Simulate processing time
        
        return {
            "success": True,
            "conflict_resolved": False,
            "external_id": f"iot_{hash(str(record)) % 10000}"
        }
    
    def get_connection_status(self, system_id: str) -> Dict[str, Any]:
        """
        Get connection status for a system.
        
        Args:
            system_id: System connection ID
            
        Returns:
            Connection status information
        """
        try:
            with self._lock:
                if system_id not in self.connections:
                    raise ValueError(f"System connection not found: {system_id}")
                
                connection = self.connections[system_id]
                
                return {
                    "system_id": system_id,
                    "system_type": connection.system_type.value,
                    "connection_name": connection.connection_name,
                    "status": connection.status.value,
                    "host": connection.host,
                    "port": connection.port,
                    "last_sync": connection.last_sync.isoformat() if connection.last_sync else None,
                    "created_at": connection.created_at.isoformat(),
                    "updated_at": connection.updated_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting connection status: {e}")
            raise
    
    def get_all_connections(self) -> List[Dict[str, Any]]:
        """
        Get all system connections.
        
        Returns:
            List of connection status information
        """
        try:
            with self._lock:
                connections = []
                for system_id, connection in self.connections.items():
                    connections.append(self.get_connection_status(system_id))
                return connections
                
        except Exception as e:
            logger.error(f"Error getting all connections: {e}")
            raise
    
    def get_sync_history(self, system_id: Optional[str] = None, 
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get synchronization history.
        
        Args:
            system_id: Filter by system ID
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            List of sync history records
        """
        try:
            # This would typically query a database
            # For now, return mock data
            mock_history = [
                {
                    "sync_id": f"sync_{int(time.time()) - i}",
                    "system_id": "cmms_001",
                    "direction": "outbound",
                    "records_processed": 100,
                    "records_successful": 98,
                    "records_failed": 2,
                    "conflicts_resolved": 1,
                    "sync_duration": 2.5,
                    "status": "completed",
                    "timestamp": datetime.now() - timedelta(hours=i)
                }
                for i in range(10)
            ]
            
            # Apply filters
            if system_id:
                mock_history = [h for h in mock_history if h["system_id"] == system_id]
            
            if start_date:
                mock_history = [h for h in mock_history if h["timestamp"] >= start_date]
            
            if end_date:
                mock_history = [h for h in mock_history if h["timestamp"] <= end_date]
            
            return mock_history
            
        except Exception as e:
            logger.error(f"Error getting sync history: {e}")
            raise
    
    def _start_connection_monitoring(self):
        """Start background connection monitoring."""
        def monitor_connections():
            while True:
                try:
                    with self._lock:
                        for system_id, connection in self.connections.items():
                            if connection.status == ConnectionStatus.CONNECTED:
                                # Check connection health
                                health_check = self._check_connection_health(connection)
                                if not health_check["healthy"]:
                                    connection.status = ConnectionStatus.ERROR
                                    logger.warning(f"Connection health check failed for {system_id}")
                    
                    time.sleep(60)  # Check every minute
                    
                except Exception as e:
                    logger.error(f"Error in connection monitoring: {e}")
                    time.sleep(60)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_connections, daemon=True)
        monitor_thread.start()
        logger.info("Connection monitoring started")
    
    def _check_connection_health(self, connection: SystemConnection) -> Dict[str, Any]:
        """Check connection health."""
        try:
            # Simulate health check
            time.sleep(0.01)
            return {"healthy": True, "response_time": 0.01}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    def _log_integration_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log integration event for audit and monitoring."""
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "event_data": event_data,
                "user_id": getattr(get_current_user(), 'id', None),
                "session_id": hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
            }
            
            logger.info(f"Integration event logged: {event_type}")
            
        except Exception as e:
            logger.error(f"Error logging integration event: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the integration framework."""
        try:
            with self._lock:
                return {
                    "total_connections": len(self.connections),
                    "active_connections": len([c for c in self.connections.values() if c.status == ConnectionStatus.CONNECTED]),
                    "total_mappings": sum(len(mappings) for mappings in self.transformers.values()),
                    "supported_system_types": len(SystemType),
                    "supported_connectors": sum(len(connectors) for connectors in self.connectors.values()),
                    "transformation_operations": len(self.transformation_engine["calculations"]) + len(self.transformation_engine["validations"]) + len(self.transformation_engine["formatting"])
                }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}


# Global instance
multi_system_integration = MultiSystemIntegration() 