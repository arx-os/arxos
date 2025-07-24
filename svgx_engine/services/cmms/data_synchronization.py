"""
CMMS Data Synchronization Service for Arxos SVG-BIM Integration

This service provides comprehensive CMMS data synchronization including
work orders, maintenance schedules, asset tracking, and real-time monitoring
with enterprise-grade features.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import json
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib
import hmac

logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Synchronization status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class SyncType(Enum):
    """Synchronization types."""
    WORK_ORDERS = "work_orders"
    MAINTENANCE_SCHEDULES = "maintenance_schedules"
    ASSETS = "assets"
    EQUIPMENT_SPECS = "equipment_specs"
    INVENTORY = "inventory"
    PERSONNEL = "personnel"


class WorkOrderStatus(Enum):
    """Work order status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class MaintenanceType(Enum):
    """Maintenance types."""
    PREVENTIVE = "preventive"
    PREDICTIVE = "predictive"
    CORRECTIVE = "corrective"
    EMERGENCY = "emergency"


class AssetStatus(Enum):
    """Asset status."""
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"
    RETIRED = "retired"


@dataclass
class CMMSConnection:
    """CMMS connection configuration."""
    connection_id: str
    name: str
    system_type: str  # upkeep, fiix, maximo, sap_pm, custom
    base_url: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    auth_type: str = "api_key"  # api_key, basic_auth, oauth2
    sync_interval: int = 3600  # seconds
    last_sync: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class FieldMapping:
    """Field mapping configuration."""
    mapping_id: str
    connection_id: str
    cmms_field: str
    arxos_field: str
    data_type: str  # string, number, date, boolean
    is_required: bool = False
    default_value: Optional[str] = None
    transform_rule: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkOrder:
    """Work order data model."""
    work_order_id: str
    cmms_work_order_id: str
    connection_id: str
    title: str
    description: Optional[str] = None
    status: WorkOrderStatus
    priority: str = "medium"
    maintenance_type: MaintenanceType
    assigned_to: Optional[str] = None
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    cost: float = 0.0
    parts_used: Optional[List[Dict[str, Any]]] = None
    scheduled_date: Optional[datetime] = None
    started_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    asset_id: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class MaintenanceSchedule:
    """Maintenance schedule data model."""
    schedule_id: str
    cmms_schedule_id: str
    connection_id: str
    asset_id: str
    title: str
    description: Optional[str] = None
    maintenance_type: MaintenanceType
    frequency: str  # daily, weekly, monthly, yearly
    interval: int = 1
    priority: str = "medium"
    estimated_hours: float = 0.0
    instructions: Optional[str] = None
    is_active: bool = True
    next_due_date: datetime
    last_completed: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Asset:
    """Asset data model."""
    asset_id: str
    cmms_asset_id: str
    connection_id: str
    name: str
    type: str
    location: Optional[str] = None
    status: AssetStatus
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    installation_date: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    maintenance_history: Optional[List[Dict[str, Any]]] = None
    specifications: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SyncResult:
    """Synchronization result."""
    sync_id: str
    connection_id: str
    sync_type: SyncType
    status: SyncStatus
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_failed: int = 0
    error_details: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class CMMSDataSynchronizationService:
    """
    CMMS Data Synchronization Service with enterprise-grade features.
    
    Provides:
    - Real-time data synchronization with CMMS systems
    - Work order processing and management
    - Automated maintenance scheduling
    - Asset tracking and monitoring
    - Field mapping and data transformation
    - Error handling and retry logic
    - Performance monitoring and reporting
    """
    
    def __init__(self):
        """Initialize the CMMS data synchronization service."""
        self.connections: Dict[str, CMMSConnection] = {}
        self.field_mappings: Dict[str, List[FieldMapping]] = {}
        self.work_orders: Dict[str, WorkOrder] = {}
        self.maintenance_schedules: Dict[str, MaintenanceSchedule] = {}
        self.assets: Dict[str, Asset] = {}
        self.sync_results: Dict[str, SyncResult] = {}
        self.statistics = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "total_records_processed": 0,
            "total_records_created": 0,
            "total_records_updated": 0,
            "total_records_failed": 0,
            "average_sync_time": 0.0
        }
        
        logger.info("CMMS Data Synchronization Service initialized")
    
    def add_connection(self, connection: CMMSConnection) -> None:
        """Add a CMMS connection."""
        self.connections[connection.connection_id] = connection
        logger.info(f"Added CMMS connection: {connection.name} ({connection.system_type})")
    
    def add_field_mapping(self, mapping: FieldMapping) -> None:
        """Add a field mapping."""
        if mapping.connection_id not in self.field_mappings:
            self.field_mappings[mapping.connection_id] = []
        self.field_mappings[mapping.connection_id].append(mapping)
        logger.info(f"Added field mapping: {mapping.cmms_field} -> {mapping.arxos_field}")
    
    async def sync_work_orders(self, connection_id: str) -> SyncResult:
        """
        Synchronize work orders from CMMS.
        
        Args:
            connection_id: CMMS connection ID
            
        Returns:
            Sync result
        """
        sync_id = str(uuid.uuid4())
        result = SyncResult(
            sync_id=sync_id,
            connection_id=connection_id,
            sync_type=SyncType.WORK_ORDERS,
            status=SyncStatus.IN_PROGRESS
        )
        
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                raise ValueError(f"Connection not found: {connection_id}")
            
            # Fetch work orders from CMMS API
            work_orders_data = await self._fetch_work_orders_from_cmms(connection)
            
            # Process each work order
            for work_order_data in work_orders_data:
                result.records_processed += 1
                
                try:
                    # Transform data using field mappings
                    transformed_data = self._transform_work_order_data(
                        work_order_data, 
                        self.field_mappings.get(connection_id, [])
                    )
                    
                    # Create or update work order
                    work_order = self._create_work_order_from_data(transformed_data, connection_id)
                    
                    if work_order.work_order_id in self.work_orders:
                        # Update existing work order
                        self._update_work_order(work_order)
                        result.records_updated += 1
                    else:
                        # Create new work order
                        self.work_orders[work_order.work_order_id] = work_order
                        result.records_created += 1
                    
                except Exception as e:
                    result.records_failed += 1
                    logger.error(f"Failed to process work order: {e}")
            
            result.status = SyncStatus.COMPLETED
            result.completed_at = datetime.now()
            
        except Exception as e:
            result.status = SyncStatus.FAILED
            result.error_details = str(e)
            result.completed_at = datetime.now()
            logger.error(f"Work order sync failed: {e}")
        
        # Update statistics
        self._update_sync_statistics(result)
        self.sync_results[sync_id] = result
        
        return result
    
    async def sync_maintenance_schedules(self, connection_id: str) -> SyncResult:
        """
        Synchronize maintenance schedules from CMMS.
        
        Args:
            connection_id: CMMS connection ID
            
        Returns:
            Sync result
        """
        sync_id = str(uuid.uuid4())
        result = SyncResult(
            sync_id=sync_id,
            connection_id=connection_id,
            sync_type=SyncType.MAINTENANCE_SCHEDULES,
            status=SyncStatus.IN_PROGRESS
        )
        
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                raise ValueError(f"Connection not found: {connection_id}")
            
            # Fetch maintenance schedules from CMMS API
            schedules_data = await self._fetch_maintenance_schedules_from_cmms(connection)
            
            # Process each maintenance schedule
            for schedule_data in schedules_data:
                result.records_processed += 1
                
                try:
                    # Transform data using field mappings
                    transformed_data = self._transform_schedule_data(
                        schedule_data, 
                        self.field_mappings.get(connection_id, [])
                    )
                    
                    # Create or update maintenance schedule
                    schedule = self._create_maintenance_schedule_from_data(transformed_data, connection_id)
                    
                    if schedule.schedule_id in self.maintenance_schedules:
                        # Update existing schedule
                        self._update_maintenance_schedule(schedule)
                        result.records_updated += 1
                    else:
                        # Create new schedule
                        self.maintenance_schedules[schedule.schedule_id] = schedule
                        result.records_created += 1
                    
                except Exception as e:
                    result.records_failed += 1
                    logger.error(f"Failed to process maintenance schedule: {e}")
            
            result.status = SyncStatus.COMPLETED
            result.completed_at = datetime.now()
            
        except Exception as e:
            result.status = SyncStatus.FAILED
            result.error_details = str(e)
            result.completed_at = datetime.now()
            logger.error(f"Maintenance schedule sync failed: {e}")
        
        # Update statistics
        self._update_sync_statistics(result)
        self.sync_results[sync_id] = result
        
        return result
    
    async def sync_assets(self, connection_id: str) -> SyncResult:
        """
        Synchronize assets from CMMS.
        
        Args:
            connection_id: CMMS connection ID
            
        Returns:
            Sync result
        """
        sync_id = str(uuid.uuid4())
        result = SyncResult(
            sync_id=sync_id,
            connection_id=connection_id,
            sync_type=SyncType.ASSETS,
            status=SyncStatus.IN_PROGRESS
        )
        
        try:
            connection = self.connections.get(connection_id)
            if not connection:
                raise ValueError(f"Connection not found: {connection_id}")
            
            # Fetch assets from CMMS API
            assets_data = await self._fetch_assets_from_cmms(connection)
            
            # Process each asset
            for asset_data in assets_data:
                result.records_processed += 1
                
                try:
                    # Transform data using field mappings
                    transformed_data = self._transform_asset_data(
                        asset_data, 
                        self.field_mappings.get(connection_id, [])
                    )
                    
                    # Create or update asset
                    asset = self._create_asset_from_data(transformed_data, connection_id)
                    
                    if asset.asset_id in self.assets:
                        # Update existing asset
                        self._update_asset(asset)
                        result.records_updated += 1
                    else:
                        # Create new asset
                        self.assets[asset.asset_id] = asset
                        result.records_created += 1
                    
                except Exception as e:
                    result.records_failed += 1
                    logger.error(f"Failed to process asset: {e}")
            
            result.status = SyncStatus.COMPLETED
            result.completed_at = datetime.now()
            
        except Exception as e:
            result.status = SyncStatus.FAILED
            result.error_details = str(e)
            result.completed_at = datetime.now()
            logger.error(f"Asset sync failed: {e}")
        
        # Update statistics
        self._update_sync_statistics(result)
        self.sync_results[sync_id] = result
        
        return result
    
    async def sync_all(self, connection_id: str) -> List[SyncResult]:
        """
        Synchronize all data types from CMMS.
        
        Args:
            connection_id: CMMS connection ID
            
        Returns:
            List of sync results
        """
        results = []
        
        # Sync work orders
        work_order_result = await self.sync_work_orders(connection_id)
        results.append(work_order_result)
        
        # Sync maintenance schedules
        schedule_result = await self.sync_maintenance_schedules(connection_id)
        results.append(schedule_result)
        
        # Sync assets
        asset_result = await self.sync_assets(connection_id)
        results.append(asset_result)
        
        return results
    
    async def _fetch_work_orders_from_cmms(self, connection: CMMSConnection) -> List[Dict[str, Any]]:
        """Fetch work orders from CMMS API."""
        async with aiohttp.ClientSession() as session:
            # Determine API endpoint based on system type
            if connection.system_type == "upkeep":
                endpoint = f"{connection.base_url}/api/v1/work-orders"
            elif connection.system_type == "fiix":
                endpoint = f"{connection.base_url}/api/v2/work-orders"
            elif connection.system_type == "maximo":
                endpoint = f"{connection.base_url}/api/workorders"
            else:
                endpoint = f"{connection.base_url}/api/work-orders"
            
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            if connection.auth_type == "api_key" and connection.api_key:
                headers["Authorization"] = f"Bearer {connection.api_key}"
            
            # Make API request
            async with session.get(endpoint, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("work_orders", []) if isinstance(data, dict) else data
                else:
                    raise Exception(f"CMMS API returned status {response.status}")
    
    async def _fetch_maintenance_schedules_from_cmms(self, connection: CMMSConnection) -> List[Dict[str, Any]]:
        """Fetch maintenance schedules from CMMS API."""
        async with aiohttp.ClientSession() as session:
            # Determine API endpoint based on system type
            if connection.system_type == "upkeep":
                endpoint = f"{connection.base_url}/api/v1/schedules"
            elif connection.system_type == "fiix":
                endpoint = f"{connection.base_url}/api/v2/schedules"
            elif connection.system_type == "maximo":
                endpoint = f"{connection.base_url}/api/pm"
            else:
                endpoint = f"{connection.base_url}/api/schedules"
            
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            if connection.auth_type == "api_key" and connection.api_key:
                headers["Authorization"] = f"Bearer {connection.api_key}"
            
            # Make API request
            async with session.get(endpoint, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("schedules", []) if isinstance(data, dict) else data
                else:
                    raise Exception(f"CMMS API returned status {response.status}")
    
    async def _fetch_assets_from_cmms(self, connection: CMMSConnection) -> List[Dict[str, Any]]:
        """Fetch assets from CMMS API."""
        async with aiohttp.ClientSession() as session:
            # Determine API endpoint based on system type
            if connection.system_type == "upkeep":
                endpoint = f"{connection.base_url}/api/v1/assets"
            elif connection.system_type == "fiix":
                endpoint = f"{connection.base_url}/api/v2/assets"
            elif connection.system_type == "maximo":
                endpoint = f"{connection.base_url}/api/assets"
            else:
                endpoint = f"{connection.base_url}/api/assets"
            
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            if connection.auth_type == "api_key" and connection.api_key:
                headers["Authorization"] = f"Bearer {connection.api_key}"
            
            # Make API request
            async with session.get(endpoint, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("assets", []) if isinstance(data, dict) else data
                else:
                    raise Exception(f"CMMS API returned status {response.status}")
    
    def _transform_work_order_data(self, data: Dict[str, Any], mappings: List[FieldMapping]) -> Dict[str, Any]:
        """Transform work order data using field mappings."""
        transformed = {}
        
        for mapping in mappings:
            if mapping.cmms_field in data:
                value = data[mapping.cmms_field]
                
                # Apply transformation rules
                if mapping.transform_rule:
                    value = self._apply_transform_rule(value, mapping.transform_rule)
                
                transformed[mapping.arxos_field] = value
            elif mapping.is_required and mapping.default_value:
                transformed[mapping.arxos_field] = mapping.default_value
        
        return transformed
    
    def _transform_schedule_data(self, data: Dict[str, Any], mappings: List[FieldMapping]) -> Dict[str, Any]:
        """Transform maintenance schedule data using field mappings."""
        transformed = {}
        
        for mapping in mappings:
            if mapping.cmms_field in data:
                value = data[mapping.cmms_field]
                
                # Apply transformation rules
                if mapping.transform_rule:
                    value = self._apply_transform_rule(value, mapping.transform_rule)
                
                transformed[mapping.arxos_field] = value
            elif mapping.is_required and mapping.default_value:
                transformed[mapping.arxos_field] = mapping.default_value
        
        return transformed
    
    def _transform_asset_data(self, data: Dict[str, Any], mappings: List[FieldMapping]) -> Dict[str, Any]:
        """Transform asset data using field mappings."""
        transformed = {}
        
        for mapping in mappings:
            if mapping.cmms_field in data:
                value = data[mapping.cmms_field]
                
                # Apply transformation rules
                if mapping.transform_rule:
                    value = self._apply_transform_rule(value, mapping.transform_rule)
                
                transformed[mapping.arxos_field] = value
            elif mapping.is_required and mapping.default_value:
                transformed[mapping.arxos_field] = mapping.default_value
        
        return transformed
    
    def _apply_transform_rule(self, value: Any, rule: str) -> Any:
        """Apply transformation rule to value."""
        try:
            rule_data = json.loads(rule)
            rule_type = rule_data.get("type")
            
            if rule_type == "type_conversion":
                return self._apply_type_conversion(value, rule_data)
            elif rule_type == "date_format":
                return self._apply_date_format(value, rule_data)
            elif rule_type == "string_manipulation":
                return self._apply_string_manipulation(value, rule_data)
            elif rule_type == "conditional":
                return self._apply_conditional_logic(value, rule_data)
            else:
                return value
        except Exception as e:
            logger.error(f"Transform rule application failed: {e}")
            return value
    
    def _apply_type_conversion(self, value: Any, rule: Dict[str, Any]) -> Any:
        """Apply type conversion transformation."""
        target_type = rule.get("target_type")
        
        if target_type == "string":
            return str(value)
        elif target_type == "int":
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return 0
        elif target_type == "float":
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0
        elif target_type == "bool":
            if isinstance(value, str):
                return value.lower() in ["true", "1", "yes", "on"]
            return bool(value)
        
        return value
    
    def _apply_date_format(self, value: Any, rule: Dict[str, Any]) -> Any:
        """Apply date format transformation."""
        input_format = rule.get("input_format", "%Y-%m-%dT%H:%M:%SZ")
        output_format = rule.get("output_format", "%Y-%m-%dT%H:%M:%SZ")
        
        try:
            if isinstance(value, str):
                parsed_date = datetime.strptime(value, input_format)
                return parsed_date.strftime(output_format)
            elif isinstance(value, datetime):
                return value.strftime(output_format)
        except Exception as e:
            logger.error(f"Date format transformation failed: {e}")
        
        return value
    
    def _apply_string_manipulation(self, value: Any, rule: Dict[str, Any]) -> Any:
        """Apply string manipulation transformation."""
        operation = rule.get("operation")
        str_value = str(value)
        
        if operation == "uppercase":
            return str_value.upper()
        elif operation == "lowercase":
            return str_value.lower()
        elif operation == "trim":
            return str_value.strip()
        elif operation == "replace":
            old_str = rule.get("old", "")
            new_str = rule.get("new", "")
            return str_value.replace(old_str, new_str)
        
        return str_value
    
    def _apply_conditional_logic(self, value: Any, rule: Dict[str, Any]) -> Any:
        """Apply conditional logic transformation."""
        condition = rule.get("condition", {})
        operator = condition.get("operator")
        expected_value = condition.get("value")
        
        if operator == "equals":
            if str(value) == str(expected_value):
                return rule.get("true_value", value)
        elif operator == "not_equals":
            if str(value) != str(expected_value):
                return rule.get("true_value", value)
        elif operator == "contains":
            if str(expected_value) in str(value):
                return rule.get("true_value", value)
        
        return rule.get("false_value", value)
    
    def _create_work_order_from_data(self, data: Dict[str, Any], connection_id: str) -> WorkOrder:
        """Create work order from transformed data."""
        return WorkOrder(
            work_order_id=str(uuid.uuid4()),
            cmms_work_order_id=data.get("cmms_work_order_id", ""),
            connection_id=connection_id,
            title=data.get("title", ""),
            description=data.get("description"),
            status=WorkOrderStatus(data.get("status", "open")),
            priority=data.get("priority", "medium"),
            maintenance_type=MaintenanceType(data.get("maintenance_type", "corrective")),
            assigned_to=data.get("assigned_to"),
            estimated_hours=float(data.get("estimated_hours", 0)),
            actual_hours=float(data.get("actual_hours", 0)),
            cost=float(data.get("cost", 0)),
            parts_used=data.get("parts_used"),
            scheduled_date=self._parse_datetime(data.get("scheduled_date")),
            started_date=self._parse_datetime(data.get("started_date")),
            completed_date=self._parse_datetime(data.get("completed_date")),
            asset_id=data.get("asset_id"),
            location=data.get("location")
        )
    
    def _create_maintenance_schedule_from_data(self, data: Dict[str, Any], connection_id: str) -> MaintenanceSchedule:
        """Create maintenance schedule from transformed data."""
        return MaintenanceSchedule(
            schedule_id=str(uuid.uuid4()),
            cmms_schedule_id=data.get("cmms_schedule_id", ""),
            connection_id=connection_id,
            asset_id=data.get("asset_id", ""),
            title=data.get("title", ""),
            description=data.get("description"),
            maintenance_type=MaintenanceType(data.get("maintenance_type", "preventive")),
            frequency=data.get("frequency", "monthly"),
            interval=int(data.get("interval", 1)),
            priority=data.get("priority", "medium"),
            estimated_hours=float(data.get("estimated_hours", 0)),
            instructions=data.get("instructions"),
            is_active=bool(data.get("is_active", True)),
            next_due_date=self._parse_datetime(data.get("next_due_date")) or datetime.now(),
            last_completed=self._parse_datetime(data.get("last_completed"))
        )
    
    def _create_asset_from_data(self, data: Dict[str, Any], connection_id: str) -> Asset:
        """Create asset from transformed data."""
        return Asset(
            asset_id=str(uuid.uuid4()),
            cmms_asset_id=data.get("cmms_asset_id", ""),
            connection_id=connection_id,
            name=data.get("name", ""),
            type=data.get("type", ""),
            location=data.get("location"),
            status=AssetStatus(data.get("status", "operational")),
            manufacturer=data.get("manufacturer"),
            model=data.get("model"),
            serial_number=data.get("serial_number"),
            installation_date=self._parse_datetime(data.get("installation_date")),
            last_maintenance=self._parse_datetime(data.get("last_maintenance")),
            next_maintenance=self._parse_datetime(data.get("next_maintenance")),
            maintenance_history=data.get("maintenance_history"),
            specifications=data.get("specifications")
        )
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime value."""
        if not value:
            return None
        
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            try:
                # Try common datetime formats
                formats = [
                    "%Y-%m-%dT%H:%M:%SZ",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d"
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
            except Exception:
                pass
        
        return None
    
    def _update_work_order(self, work_order: WorkOrder) -> None:
        """Update existing work order."""
        if work_order.work_order_id in self.work_orders:
            existing = self.work_orders[work_order.work_order_id]
            existing.title = work_order.title
            existing.description = work_order.description
            existing.status = work_order.status
            existing.priority = work_order.priority
            existing.maintenance_type = work_order.maintenance_type
            existing.assigned_to = work_order.assigned_to
            existing.estimated_hours = work_order.estimated_hours
            existing.actual_hours = work_order.actual_hours
            existing.cost = work_order.cost
            existing.parts_used = work_order.parts_used
            existing.scheduled_date = work_order.scheduled_date
            existing.started_date = work_order.started_date
            existing.completed_date = work_order.completed_date
            existing.asset_id = work_order.asset_id
            existing.location = work_order.location
            existing.updated_at = datetime.now()
    
    def _update_maintenance_schedule(self, schedule: MaintenanceSchedule) -> None:
        """Update existing maintenance schedule."""
        if schedule.schedule_id in self.maintenance_schedules:
            existing = self.maintenance_schedules[schedule.schedule_id]
            existing.title = schedule.title
            existing.description = schedule.description
            existing.maintenance_type = schedule.maintenance_type
            existing.frequency = schedule.frequency
            existing.interval = schedule.interval
            existing.priority = schedule.priority
            existing.estimated_hours = schedule.estimated_hours
            existing.instructions = schedule.instructions
            existing.is_active = schedule.is_active
            existing.next_due_date = schedule.next_due_date
            existing.last_completed = schedule.last_completed
            existing.updated_at = datetime.now()
    
    def _update_asset(self, asset: Asset) -> None:
        """Update existing asset."""
        if asset.asset_id in self.assets:
            existing = self.assets[asset.asset_id]
            existing.name = asset.name
            existing.type = asset.type
            existing.location = asset.location
            existing.status = asset.status
            existing.manufacturer = asset.manufacturer
            existing.model = asset.model
            existing.serial_number = asset.serial_number
            existing.installation_date = asset.installation_date
            existing.last_maintenance = asset.last_maintenance
            existing.next_maintenance = asset.next_maintenance
            existing.maintenance_history = asset.maintenance_history
            existing.specifications = asset.specifications
            existing.updated_at = datetime.now()
    
    def _update_sync_statistics(self, result: SyncResult) -> None:
        """Update sync statistics."""
        self.statistics["total_syncs"] += 1
        
        if result.status == SyncStatus.COMPLETED:
            self.statistics["successful_syncs"] += 1
        elif result.status == SyncStatus.FAILED:
            self.statistics["failed_syncs"] += 1
        
        self.statistics["total_records_processed"] += result.records_processed
        self.statistics["total_records_created"] += result.records_created
        self.statistics["total_records_updated"] += result.records_updated
        self.statistics["total_records_failed"] += result.records_failed
        
        # Update average sync time
        if result.completed_at:
            sync_time = (result.completed_at - result.started_at).total_seconds()
            total_syncs = self.statistics["successful_syncs"] + self.statistics["failed_syncs"]
            if total_syncs > 0:
                self.statistics["average_sync_time"] = (
                    (self.statistics["average_sync_time"] * (total_syncs - 1) + sync_time) / total_syncs
                )
    
    def get_work_orders(self, connection_id: Optional[str] = None, status: Optional[WorkOrderStatus] = None) -> List[WorkOrder]:
        """Get work orders with optional filtering."""
        work_orders = list(self.work_orders.values())
        
        if connection_id:
            work_orders = [wo for wo in work_orders if wo.connection_id == connection_id]
        
        if status:
            work_orders = [wo for wo in work_orders if wo.status == status]
        
        return work_orders
    
    def get_maintenance_schedules(self, connection_id: Optional[str] = None, asset_id: Optional[str] = None) -> List[MaintenanceSchedule]:
        """Get maintenance schedules with optional filtering."""
        schedules = list(self.maintenance_schedules.values())
        
        if connection_id:
            schedules = [s for s in schedules if s.connection_id == connection_id]
        
        if asset_id:
            schedules = [s for s in schedules if s.asset_id == asset_id]
        
        return schedules
    
    def get_assets(self, connection_id: Optional[str] = None, status: Optional[AssetStatus] = None) -> List[Asset]:
        """Get assets with optional filtering."""
        assets = list(self.assets.values())
        
        if connection_id:
            assets = [a for a in assets if a.connection_id == connection_id]
        
        if status:
            assets = [a for a in assets if a.status == status]
        
        return assets
    
    def get_sync_results(self, connection_id: Optional[str] = None) -> List[SyncResult]:
        """Get sync results with optional filtering."""
        results = list(self.sync_results.values())
        
        if connection_id:
            results = [r for r in results if r.connection_id == connection_id]
        
        return results
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """Get sync statistics."""
        return self.statistics.copy()


# Factory function
def create_cmms_data_synchronization_service() -> CMMSDataSynchronizationService:
    """Create a CMMS data synchronization service instance."""
    return CMMSDataSynchronizationService() 