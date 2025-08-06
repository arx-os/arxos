"""
CMMS Integration Service for SVGX Engine

Floor-specific maintenance management with integration to SVGX precision system.
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid

# SVGX Engine imports
from svgx_engine.core.precision_coordinate import PrecisionCoordinate
from svgx_engine.core.precision_math import PrecisionMath
from svgx_engine.core.precision_errors import ValidationError
from svgx_engine.logging.logging_config import get_logger
from svgx_engine.infrastructure.database import DatabaseManager

logger = get_logger(__name__)


class WorkOrderStatus(Enum):
    """Work order status enumeration"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class MaintenanceType(Enum):
    """Maintenance type enumeration"""

    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    EMERGENCY = "emergency"
    INSPECTION = "inspection"
    CALIBRATION = "calibration"


class PriorityLevel(Enum):
    """Priority level enumeration"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FloorAsset:
    """Floor-specific asset information with precision coordinates"""

    asset_id: str
    floor_id: str
    building_id: str
    asset_name: str
    asset_type: str
    location_x: float
    location_y: float
    location_z: float = 0.0
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    installation_date: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    status: str = "active"
    condition: str = "good"
    maintenance_interval_days: int = 365
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def precision_location(self) -> PrecisionCoordinate:
        """Get precision coordinate for asset location"""
        return PrecisionCoordinate(self.location_x, self.location_y, self.location_z)


@dataclass
class MaintenanceSchedule:
    """Floor-specific maintenance schedule"""

    schedule_id: str
    floor_id: str
    building_id: str
    asset_id: Optional[str] = None
    maintenance_type: MaintenanceType = MaintenanceType.PREVENTIVE
    frequency_days: int = 30
    description: str = ""
    assigned_technician: Optional[str] = None
    estimated_duration_hours: float = 2.0
    parts_required: List[str] = field(default_factory=list)
    instructions: str = ""
    is_active: bool = True
    last_executed: Optional[datetime] = None
    next_scheduled: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkOrder:
    """Floor-specific work order"""

    work_order_id: str
    floor_id: str
    building_id: str
    asset_id: Optional[str] = None
    schedule_id: Optional[str] = None
    title: str
    description: str
    maintenance_type: MaintenanceType = MaintenanceType.CORRECTIVE
    priority: PriorityLevel = PriorityLevel.MEDIUM
    status: WorkOrderStatus = WorkOrderStatus.PENDING
    assigned_technician: Optional[str] = None
    requested_by: Optional[str] = None
    estimated_duration_hours: Optional[float] = None
    actual_duration_hours: Optional[float] = None
    scheduled_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    completion_date: Optional[datetime] = None
    parts_used: List[str] = field(default_factory=list)
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    total_cost: Optional[float] = None
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MaintenanceHistory:
    """Maintenance history record"""

    history_id: str
    floor_id: str
    building_id: str
    asset_id: Optional[str] = None
    work_order_id: Optional[str] = None
    maintenance_type: MaintenanceType
    performed_by: str
    performed_date: datetime
    description: str
    parts_replaced: List[str] = field(default_factory=list)
    labor_hours: float = 0.0
    cost: Optional[float] = None
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


class FloorAssetManager:
    """Manages floor-specific assets with precision coordinate support"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.precision_math = PrecisionMath()

    async def add_floor_asset(self, asset: FloorAsset) -> bool:
        """Add a floor asset with precision validation"""
        try:
            # Validate precision coordinates
            precision_location = asset.precision_location

            # Check for duplicate assets at same location
            existing_assets = await self.get_floor_assets(
                asset.floor_id, asset.building_id
            )
            for existing_asset in existing_assets:
                existing_precision = existing_asset.precision_location
                distance = self.precision_math.distance(
                    precision_location, existing_precision
                )
                if distance < 0.1:  # Minimum clearance
                    logger.warning(
                        f"Asset too close to existing asset at distance {distance}"
                    )
                    return False

            # Store asset in database
            asset_data = {
                "asset_id": asset.asset_id,
                "floor_id": asset.floor_id,
                "building_id": asset.building_id,
                "asset_name": asset.asset_name,
                "asset_type": asset.asset_type,
                "location_x": asset.location_x,
                "location_y": asset.location_y,
                "location_z": asset.location_z,
                "manufacturer": asset.manufacturer,
                "model": asset.model,
                "serial_number": asset.serial_number,
                "installation_date": (
                    asset.installation_date.isoformat()
                    if asset.installation_date
                    else None
                ),
                "last_maintenance": (
                    asset.last_maintenance.isoformat()
                    if asset.last_maintenance
                    else None
                ),
                "next_maintenance": (
                    asset.next_maintenance.isoformat()
                    if asset.next_maintenance
                    else None
                ),
                "status": asset.status,
                "condition": asset.condition,
                "maintenance_interval_days": asset.maintenance_interval_days,
                "created_at": asset.created_at.isoformat(),
                "updated_at": asset.updated_at.isoformat(),
                "metadata": json.dumps(asset.metadata),
            }

            await self.db_manager.execute(
                """
                INSERT INTO floor_assets (
                    asset_id, floor_id, building_id, asset_name, asset_type,
                    location_x, location_y, location_z, manufacturer, model,
                    serial_number, installation_date, last_maintenance, next_maintenance,
                    status, condition, maintenance_interval_days, created_at, updated_at, metadata
                ) VALUES (
                    :asset_id, :floor_id, :building_id, :asset_name, :asset_type,
                    :location_x, :location_y, :location_z, :manufacturer, :model,
                    :serial_number, :installation_date, :last_maintenance, :next_maintenance,
                    :status, :condition, :maintenance_interval_days, :created_at, :updated_at, :metadata
                )
                """,
                asset_data,
            )

            logger.info(
                f"Added floor asset {asset.asset_id} at precision location {precision_location}"
            )
            return True

        except Exception as e:
            logger.error(f"Error adding floor asset: {e}")
            return False

    async def get_floor_assets(
        self, floor_id: str, building_id: str
    ) -> List[FloorAsset]:
        """Get all assets for a specific floor with precision coordinates"""
        try:
            result = await self.db_manager.fetch_all(
                """
                SELECT * FROM floor_assets 
                WHERE floor_id = :floor_id AND building_id = :building_id
                ORDER BY asset_name
                """,
                {"floor_id": floor_id, "building_id": building_id},
            )

            assets = []
            for row in result:
                asset = FloorAsset(
                    asset_id=row["asset_id"],
                    floor_id=row["floor_id"],
                    building_id=row["building_id"],
                    asset_name=row["asset_name"],
                    asset_type=row["asset_type"],
                    location_x=row["location_x"],
                    location_y=row["location_y"],
                    location_z=row["location_z"],
                    manufacturer=row["manufacturer"],
                    model=row["model"],
                    serial_number=row["serial_number"],
                    installation_date=(
                        datetime.fromisoformat(row["installation_date"])
                        if row["installation_date"]
                        else None
                    ),
                    last_maintenance=(
                        datetime.fromisoformat(row["last_maintenance"])
                        if row["last_maintenance"]
                        else None
                    ),
                    next_maintenance=(
                        datetime.fromisoformat(row["next_maintenance"])
                        if row["next_maintenance"]
                        else None
                    ),
                    status=row["status"],
                    condition=row["condition"],
                    maintenance_interval_days=row["maintenance_interval_days"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                assets.append(asset)

            return assets

        except Exception as e:
            logger.error(f"Error getting floor assets: {e}")
            return []


class MaintenanceScheduler:
    """Manages maintenance schedules with precision timing"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def add_maintenance_schedule(self, schedule: MaintenanceSchedule) -> bool:
        """Add a maintenance schedule"""
        try:
            schedule_data = {
                "schedule_id": schedule.schedule_id,
                "floor_id": schedule.floor_id,
                "building_id": schedule.building_id,
                "asset_id": schedule.asset_id,
                "maintenance_type": schedule.maintenance_type.value,
                "frequency_days": schedule.frequency_days,
                "description": schedule.description,
                "assigned_technician": schedule.assigned_technician,
                "estimated_duration_hours": schedule.estimated_duration_hours,
                "parts_required": json.dumps(schedule.parts_required),
                "instructions": schedule.instructions,
                "is_active": schedule.is_active,
                "last_executed": (
                    schedule.last_executed.isoformat()
                    if schedule.last_executed
                    else None
                ),
                "next_scheduled": (
                    schedule.next_scheduled.isoformat()
                    if schedule.next_scheduled
                    else None
                ),
                "created_at": schedule.created_at.isoformat(),
                "updated_at": schedule.updated_at.isoformat(),
                "metadata": json.dumps(schedule.metadata),
            }

            await self.db_manager.execute(
                """
                INSERT INTO maintenance_schedules (
                    schedule_id, floor_id, building_id, asset_id, maintenance_type,
                    frequency_days, description, assigned_technician, estimated_duration_hours,
                    parts_required, instructions, is_active, last_executed, next_scheduled,
                    created_at, updated_at, metadata
                ) VALUES (
                    :schedule_id, :floor_id, :building_id, :asset_id, :maintenance_type,
                    :frequency_days, :description, :assigned_technician, :estimated_duration_hours,
                    :parts_required, :instructions, :is_active, :last_executed, :next_scheduled,
                    :created_at, :updated_at, :metadata
                )
                """,
                schedule_data,
            )

            logger.info(f"Added maintenance schedule {schedule.schedule_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding maintenance schedule: {e}")
            return False


class WorkOrderManager:
    """Manages work orders with precision tracking"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def create_work_order(self, work_order: WorkOrder) -> bool:
        """Create a new work order"""
        try:
            work_order_data = {
                "work_order_id": work_order.work_order_id,
                "floor_id": work_order.floor_id,
                "building_id": work_order.building_id,
                "asset_id": work_order.asset_id,
                "schedule_id": work_order.schedule_id,
                "title": work_order.title,
                "description": work_order.description,
                "maintenance_type": work_order.maintenance_type.value,
                "priority": work_order.priority.value,
                "status": work_order.status.value,
                "assigned_technician": work_order.assigned_technician,
                "requested_by": work_order.requested_by,
                "estimated_duration_hours": work_order.estimated_duration_hours,
                "actual_duration_hours": work_order.actual_duration_hours,
                "scheduled_date": (
                    work_order.scheduled_date.isoformat()
                    if work_order.scheduled_date
                    else None
                ),
                "start_date": (
                    work_order.start_date.isoformat() if work_order.start_date else None
                ),
                "completion_date": (
                    work_order.completion_date.isoformat()
                    if work_order.completion_date
                    else None
                ),
                "parts_used": json.dumps(work_order.parts_used),
                "labor_cost": work_order.labor_cost,
                "parts_cost": work_order.parts_cost,
                "total_cost": work_order.total_cost,
                "notes": work_order.notes,
                "created_at": work_order.created_at.isoformat(),
                "updated_at": work_order.updated_at.isoformat(),
                "metadata": json.dumps(work_order.metadata),
            }

            await self.db_manager.execute(
                """
                INSERT INTO work_orders (
                    work_order_id, floor_id, building_id, asset_id, schedule_id,
                    title, description, maintenance_type, priority, status,
                    assigned_technician, requested_by, estimated_duration_hours,
                    actual_duration_hours, scheduled_date, start_date, completion_date,
                    parts_used, labor_cost, parts_cost, total_cost, notes,
                    created_at, updated_at, metadata
                ) VALUES (
                    :work_order_id, :floor_id, :building_id, :asset_id, :schedule_id,
                    :title, :description, :maintenance_type, :priority, :status,
                    :assigned_technician, :requested_by, :estimated_duration_hours,
                    :actual_duration_hours, :scheduled_date, :start_date, :completion_date,
                    :parts_used, :labor_cost, :parts_cost, :total_cost, :notes,
                    :created_at, :updated_at, :metadata
                )
                """,
                work_order_data,
            )

            logger.info(f"Created work order {work_order.work_order_id}")
            return True

        except Exception as e:
            logger.error(f"Error creating work order: {e}")
            return False


class CMMSIntegrationService:
    """Main CMMS integration service for SVGX Engine"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.asset_manager = FloorAssetManager(db_manager)
        self.scheduler = MaintenanceScheduler(db_manager)
        self.work_order_manager = WorkOrderManager(db_manager)
        self.precision_math = PrecisionMath()

    async def add_floor_asset(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a floor asset with precision coordinate validation"""
        try:
            # Validate precision coordinates
            location_x = asset_data.get("location_x", 0.0)
            location_y = asset_data.get("location_y", 0.0)
            location_z = asset_data.get("location_z", 0.0)

            precision_location = PrecisionCoordinate(location_x, location_y, location_z)

            asset = FloorAsset(
                asset_id=asset_data.get("asset_id", str(uuid.uuid4())),
                floor_id=asset_data["floor_id"],
                building_id=asset_data["building_id"],
                asset_name=asset_data["asset_name"],
                asset_type=asset_data["asset_type"],
                location_x=location_x,
                location_y=location_y,
                location_z=location_z,
                manufacturer=asset_data.get("manufacturer"),
                model=asset_data.get("model"),
                serial_number=asset_data.get("serial_number"),
                installation_date=(
                    datetime.fromisoformat(asset_data["installation_date"])
                    if asset_data.get("installation_date")
                    else None
                ),
                last_maintenance=(
                    datetime.fromisoformat(asset_data["last_maintenance"])
                    if asset_data.get("last_maintenance")
                    else None
                ),
                next_maintenance=(
                    datetime.fromisoformat(asset_data["next_maintenance"])
                    if asset_data.get("next_maintenance")
                    else None
                ),
                status=asset_data.get("status", "active"),
                condition=asset_data.get("condition", "good"),
                maintenance_interval_days=asset_data.get(
                    "maintenance_interval_days", 365
                ),
                metadata=asset_data.get("metadata", {}),
            )

            success = await self.asset_manager.add_floor_asset(asset)

            return {
                "success": success,
                "asset_id": asset.asset_id,
                "precision_location": {
                    "x": precision_location.x,
                    "y": precision_location.y,
                    "z": precision_location.z,
                },
                "message": (
                    "Asset added successfully" if success else "Failed to add asset"
                ),
            }

        except Exception as e:
            logger.error(f"Error adding floor asset: {e}")
            return {"success": False, "error": str(e)}

    async def get_floor_assets(self, floor_id: str, building_id: str) -> Dict[str, Any]:
        """Get all assets for a specific floor with precision coordinates"""
        try:
            assets = await self.asset_manager.get_floor_assets(floor_id, building_id)

            asset_list = []
            for asset in assets:
                asset_list.append(
                    {
                        "asset_id": asset.asset_id,
                        "asset_name": asset.asset_name,
                        "asset_type": asset.asset_type,
                        "precision_location": {
                            "x": asset.location_x,
                            "y": asset.location_y,
                            "z": asset.location_z,
                        },
                        "status": asset.status,
                        "condition": asset.condition,
                        "next_maintenance": (
                            asset.next_maintenance.isoformat()
                            if asset.next_maintenance
                            else None
                        ),
                    }
                )

            return {
                "success": True,
                "floor_id": floor_id,
                "building_id": building_id,
                "assets": asset_list,
                "total_assets": len(asset_list),
            }

        except Exception as e:
            logger.error(f"Error getting floor assets: {e}")
            return {"success": False, "error": str(e)}

    async def create_maintenance_schedule(
        self, schedule_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a maintenance schedule"""
        try:
            schedule = MaintenanceSchedule(
                schedule_id=schedule_data.get("schedule_id", str(uuid.uuid4())),
                floor_id=schedule_data["floor_id"],
                building_id=schedule_data["building_id"],
                asset_id=schedule_data.get("asset_id"),
                maintenance_type=MaintenanceType(
                    schedule_data.get("maintenance_type", "preventive")
                ),
                frequency_days=schedule_data.get("frequency_days", 30),
                description=schedule_data.get("description", ""),
                assigned_technician=schedule_data.get("assigned_technician"),
                estimated_duration_hours=schedule_data.get(
                    "estimated_duration_hours", 2.0
                ),
                parts_required=schedule_data.get("parts_required", []),
                instructions=schedule_data.get("instructions", ""),
                metadata=schedule_data.get("metadata", {}),
            )

            success = await self.scheduler.add_maintenance_schedule(schedule)

            return {
                "success": success,
                "schedule_id": schedule.schedule_id,
                "message": (
                    "Schedule created successfully"
                    if success
                    else "Failed to create schedule"
                ),
            }

        except Exception as e:
            logger.error(f"Error creating maintenance schedule: {e}")
            return {"success": False, "error": str(e)}

    async def create_work_order(
        self, work_order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a work order"""
        try:
            work_order = WorkOrder(
                work_order_id=work_order_data.get("work_order_id", str(uuid.uuid4())),
                floor_id=work_order_data["floor_id"],
                building_id=work_order_data["building_id"],
                asset_id=work_order_data.get("asset_id"),
                schedule_id=work_order_data.get("schedule_id"),
                title=work_order_data["title"],
                description=work_order_data["description"],
                maintenance_type=MaintenanceType(
                    work_order_data.get("maintenance_type", "corrective")
                ),
                priority=PriorityLevel(work_order_data.get("priority", "medium")),
                assigned_technician=work_order_data.get("assigned_technician"),
                requested_by=work_order_data.get("requested_by"),
                estimated_duration_hours=work_order_data.get(
                    "estimated_duration_hours"
                ),
                scheduled_date=(
                    datetime.fromisoformat(work_order_data["scheduled_date"])
                    if work_order_data.get("scheduled_date")
                    else None
                ),
                parts_used=work_order_data.get("parts_used", []),
                notes=work_order_data.get("notes", ""),
                metadata=work_order_data.get("metadata", {}),
            )

            success = await self.work_order_manager.create_work_order(work_order)

            return {
                "success": success,
                "work_order_id": work_order.work_order_id,
                "message": (
                    "Work order created successfully"
                    if success
                    else "Failed to create work order"
                ),
            }

        except Exception as e:
            logger.error(f"Error creating work order: {e}")
            return {"success": False, "error": str(e)}

    async def get_due_maintenance(
        self, floor_id: str, building_id: str
    ) -> Dict[str, Any]:
        """Get assets due for maintenance on a specific floor"""
        try:
            assets = await self.asset_manager.get_floor_assets(floor_id, building_id)
            due_assets = []

            current_date = datetime.utcnow()

            for asset in assets:
                if asset.next_maintenance and asset.next_maintenance <= current_date:
                    due_assets.append(
                        {
                            "asset_id": asset.asset_id,
                            "asset_name": asset.asset_name,
                            "asset_type": asset.asset_type,
                            "precision_location": {
                                "x": asset.location_x,
                                "y": asset.location_y,
                                "z": asset.location_z,
                            },
                            "next_maintenance": asset.next_maintenance.isoformat(),
                            "days_overdue": (
                                current_date - asset.next_maintenance
                            ).days,
                        }
                    )

            return {
                "success": True,
                "floor_id": floor_id,
                "building_id": building_id,
                "due_assets": due_assets,
                "total_due": len(due_assets),
            }

        except Exception as e:
            logger.error(f"Error getting due maintenance: {e}")
            return {"success": False, "error": str(e)}
