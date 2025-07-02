"""
CMMS Integration Service for Floor-Specific Maintenance Management
Handles floor-based maintenance schedules, work orders, and asset tracking
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path
import sqlite3
import uuid

logger = logging.getLogger(__name__)

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
    """Floor-specific asset information"""
    asset_id: str
    floor_id: str
    building_id: str
    asset_name: str
    asset_type: str
    location_x: float
    location_y: float
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
    estimated_duration_hours: float = 2.0
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
    """Manages floor-specific assets"""
    
    def __init__(self, db_path: str = "./data/cmms.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize CMMS database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create assets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS floor_assets (
                asset_id TEXT PRIMARY KEY,
                floor_id TEXT NOT NULL,
                building_id TEXT NOT NULL,
                asset_name TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                location_x REAL NOT NULL,
                location_y REAL NOT NULL,
                manufacturer TEXT,
                model TEXT,
                serial_number TEXT,
                installation_date TEXT,
                last_maintenance TEXT,
                next_maintenance TEXT,
                status TEXT DEFAULT 'active',
                condition TEXT DEFAULT 'good',
                maintenance_interval_days INTEGER DEFAULT 365,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        ''')
        
        # Create maintenance schedules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_schedules (
                schedule_id TEXT PRIMARY KEY,
                floor_id TEXT NOT NULL,
                building_id TEXT NOT NULL,
                asset_id TEXT,
                maintenance_type TEXT NOT NULL,
                frequency_days INTEGER NOT NULL,
                description TEXT,
                assigned_technician TEXT,
                estimated_duration_hours REAL DEFAULT 2.0,
                parts_required TEXT,
                instructions TEXT,
                is_active INTEGER DEFAULT 1,
                last_executed TEXT,
                next_scheduled TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        ''')
        
        # Create work orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS work_orders (
                work_order_id TEXT PRIMARY KEY,
                floor_id TEXT NOT NULL,
                building_id TEXT NOT NULL,
                asset_id TEXT,
                schedule_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                maintenance_type TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                assigned_technician TEXT,
                requested_by TEXT,
                estimated_duration_hours REAL DEFAULT 2.0,
                actual_duration_hours REAL,
                scheduled_date TEXT,
                start_date TEXT,
                completion_date TEXT,
                parts_used TEXT,
                labor_cost REAL,
                parts_cost REAL,
                total_cost REAL,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        ''')
        
        # Create maintenance history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_history (
                history_id TEXT PRIMARY KEY,
                floor_id TEXT NOT NULL,
                building_id TEXT NOT NULL,
                asset_id TEXT,
                work_order_id TEXT,
                maintenance_type TEXT NOT NULL,
                performed_by TEXT NOT NULL,
                performed_date TEXT NOT NULL,
                description TEXT,
                parts_replaced TEXT,
                labor_hours REAL DEFAULT 0.0,
                cost REAL,
                notes TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_assets_floor ON floor_assets(floor_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_assets_building ON floor_assets(building_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_schedules_floor ON maintenance_schedules(floor_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_orders_floor ON work_orders(floor_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_floor ON maintenance_history(floor_id)')
        
        conn.commit()
        conn.close()
    
    def add_floor_asset(self, asset: FloorAsset) -> bool:
        """Add a floor asset"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO floor_assets (
                    asset_id, floor_id, building_id, asset_name, asset_type,
                    location_x, location_y, manufacturer, model, serial_number,
                    installation_date, last_maintenance, next_maintenance,
                    status, condition, maintenance_interval_days,
                    created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                asset.asset_id, asset.floor_id, asset.building_id, asset.asset_name,
                asset.asset_type, asset.location_x, asset.location_y, asset.manufacturer,
                asset.model, asset.serial_number,
                asset.installation_date.isoformat() if asset.installation_date else None,
                asset.last_maintenance.isoformat() if asset.last_maintenance else None,
                asset.next_maintenance.isoformat() if asset.next_maintenance else None,
                asset.status, asset.condition, asset.maintenance_interval_days,
                asset.created_at.isoformat(), asset.updated_at.isoformat(),
                json.dumps(asset.metadata)
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Added floor asset: {asset.asset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add floor asset: {e}")
            return False
    
    def get_floor_assets(self, floor_id: str, building_id: str) -> List[FloorAsset]:
        """Get all assets for a floor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM floor_assets 
                WHERE floor_id = ? AND building_id = ?
                ORDER BY asset_name
            ''', (floor_id, building_id))
            
            assets = []
            for row in cursor.fetchall():
                asset = FloorAsset(
                    asset_id=row[0],
                    floor_id=row[1],
                    building_id=row[2],
                    asset_name=row[3],
                    asset_type=row[4],
                    location_x=row[5],
                    location_y=row[6],
                    manufacturer=row[7],
                    model=row[8],
                    serial_number=row[9],
                    installation_date=datetime.fromisoformat(row[10]) if row[10] else None,
                    last_maintenance=datetime.fromisoformat(row[11]) if row[11] else None,
                    next_maintenance=datetime.fromisoformat(row[12]) if row[12] else None,
                    status=row[13],
                    condition=row[14],
                    maintenance_interval_days=row[15],
                    created_at=datetime.fromisoformat(row[16]),
                    updated_at=datetime.fromisoformat(row[17]),
                    metadata=json.loads(row[18]) if row[18] else {}
                )
                assets.append(asset)
            
            conn.close()
            return assets
            
        except Exception as e:
            logger.error(f"Failed to get floor assets: {e}")
            return []
    
    def get_asset(self, asset_id: str) -> Optional[FloorAsset]:
        """Get a specific asset"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM floor_assets WHERE asset_id = ?', (asset_id,))
            row = cursor.fetchone()
            
            if row:
                asset = FloorAsset(
                    asset_id=row[0],
                    floor_id=row[1],
                    building_id=row[2],
                    asset_name=row[3],
                    asset_type=row[4],
                    location_x=row[5],
                    location_y=row[6],
                    manufacturer=row[7],
                    model=row[8],
                    serial_number=row[9],
                    installation_date=datetime.fromisoformat(row[10]) if row[10] else None,
                    last_maintenance=datetime.fromisoformat(row[11]) if row[11] else None,
                    next_maintenance=datetime.fromisoformat(row[12]) if row[12] else None,
                    status=row[13],
                    condition=row[14],
                    maintenance_interval_days=row[15],
                    created_at=datetime.fromisoformat(row[16]),
                    updated_at=datetime.fromisoformat(row[17]),
                    metadata=json.loads(row[18]) if row[18] else {}
                )
                conn.close()
                return asset
            
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get asset: {e}")
            return None
    
    def update_asset(self, asset: FloorAsset) -> bool:
        """Update an asset"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE floor_assets SET
                    asset_name = ?, asset_type = ?, location_x = ?, location_y = ?,
                    manufacturer = ?, model = ?, serial_number = ?,
                    installation_date = ?, last_maintenance = ?, next_maintenance = ?,
                    status = ?, condition = ?, maintenance_interval_days = ?,
                    updated_at = ?, metadata = ?
                WHERE asset_id = ?
            ''', (
                asset.asset_name, asset.asset_type, asset.location_x, asset.location_y,
                asset.manufacturer, asset.model, asset.serial_number,
                asset.installation_date.isoformat() if asset.installation_date else None,
                asset.last_maintenance.isoformat() if asset.last_maintenance else None,
                asset.next_maintenance.isoformat() if asset.next_maintenance else None,
                asset.status, asset.condition, asset.maintenance_interval_days,
                datetime.utcnow().isoformat(), json.dumps(asset.metadata),
                asset.asset_id
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Updated asset: {asset.asset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update asset: {e}")
            return False
    
    def delete_asset(self, asset_id: str) -> bool:
        """Delete an asset"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM floor_assets WHERE asset_id = ?', (asset_id,))
            
            conn.commit()
            conn.close()
            logger.info(f"Deleted asset: {asset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete asset: {e}")
            return False

class MaintenanceScheduler:
    """Manages floor-specific maintenance schedules"""
    
    def __init__(self, db_path: str = "./data/cmms.db"):
        self.db_path = db_path
    
    def add_maintenance_schedule(self, schedule: MaintenanceSchedule) -> bool:
        """Add a maintenance schedule"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO maintenance_schedules (
                    schedule_id, floor_id, building_id, asset_id, maintenance_type,
                    frequency_days, description, assigned_technician,
                    estimated_duration_hours, parts_required, instructions,
                    is_active, last_executed, next_scheduled,
                    created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                schedule.schedule_id, schedule.floor_id, schedule.building_id,
                schedule.asset_id, schedule.maintenance_type.value,
                schedule.frequency_days, schedule.description, schedule.assigned_technician,
                schedule.estimated_duration_hours, json.dumps(schedule.parts_required),
                schedule.instructions, 1 if schedule.is_active else 0,
                schedule.last_executed.isoformat() if schedule.last_executed else None,
                schedule.next_scheduled.isoformat() if schedule.next_scheduled else None,
                schedule.created_at.isoformat(), schedule.updated_at.isoformat(),
                json.dumps(schedule.metadata)
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Added maintenance schedule: {schedule.schedule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add maintenance schedule: {e}")
            return False
    
    def get_floor_schedules(self, floor_id: str, building_id: str) -> List[MaintenanceSchedule]:
        """Get all maintenance schedules for a floor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM maintenance_schedules 
                WHERE floor_id = ? AND building_id = ?
                ORDER BY next_scheduled
            ''', (floor_id, building_id))
            
            schedules = []
            for row in cursor.fetchall():
                schedule = MaintenanceSchedule(
                    schedule_id=row[0],
                    floor_id=row[1],
                    building_id=row[2],
                    asset_id=row[3],
                    maintenance_type=MaintenanceType(row[4]),
                    frequency_days=row[5],
                    description=row[6],
                    assigned_technician=row[7],
                    estimated_duration_hours=row[8],
                    parts_required=json.loads(row[9]) if row[9] else [],
                    instructions=row[10],
                    is_active=bool(row[11]),
                    last_executed=datetime.fromisoformat(row[12]) if row[12] else None,
                    next_scheduled=datetime.fromisoformat(row[13]) if row[13] else None,
                    created_at=datetime.fromisoformat(row[14]),
                    updated_at=datetime.fromisoformat(row[15]),
                    metadata=json.loads(row[16]) if row[16] else {}
                )
                schedules.append(schedule)
            
            conn.close()
            return schedules
            
        except Exception as e:
            logger.error(f"Failed to get floor schedules: {e}")
            return []
    
    def get_due_schedules(self, floor_id: str, building_id: str) -> List[MaintenanceSchedule]:
        """Get maintenance schedules due for execution"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.utcnow()
            cursor.execute('''
                SELECT * FROM maintenance_schedules 
                WHERE floor_id = ? AND building_id = ? 
                AND is_active = 1 AND next_scheduled <= ?
                ORDER BY next_scheduled
            ''', (floor_id, building_id, now.isoformat()))
            
            schedules = []
            for row in cursor.fetchall():
                schedule = MaintenanceSchedule(
                    schedule_id=row[0],
                    floor_id=row[1],
                    building_id=row[2],
                    asset_id=row[3],
                    maintenance_type=MaintenanceType(row[4]),
                    frequency_days=row[5],
                    description=row[6],
                    assigned_technician=row[7],
                    estimated_duration_hours=row[8],
                    parts_required=json.loads(row[9]) if row[9] else [],
                    instructions=row[10],
                    is_active=bool(row[11]),
                    last_executed=datetime.fromisoformat(row[12]) if row[12] else None,
                    next_scheduled=datetime.fromisoformat(row[13]) if row[13] else None,
                    created_at=datetime.fromisoformat(row[14]),
                    updated_at=datetime.fromisoformat(row[15]),
                    metadata=json.loads(row[16]) if row[16] else {}
                )
                schedules.append(schedule)
            
            conn.close()
            return schedules
            
        except Exception as e:
            logger.error(f"Failed to get due schedules: {e}")
            return []

class WorkOrderManager:
    """Manages floor-specific work orders"""
    
    def __init__(self, db_path: str = "./data/cmms.db"):
        self.db_path = db_path
    
    def create_work_order(self, work_order: WorkOrder) -> bool:
        """Create a new work order"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO work_orders (
                    work_order_id, floor_id, building_id, asset_id, schedule_id,
                    title, description, maintenance_type, priority, status,
                    assigned_technician, requested_by, estimated_duration_hours,
                    actual_duration_hours, scheduled_date, start_date, completion_date,
                    parts_used, labor_cost, parts_cost, total_cost, notes,
                    created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                work_order.work_order_id, work_order.floor_id, work_order.building_id,
                work_order.asset_id, work_order.schedule_id, work_order.title,
                work_order.description, work_order.maintenance_type.value,
                work_order.priority.value, work_order.status.value,
                work_order.assigned_technician, work_order.requested_by,
                work_order.estimated_duration_hours, work_order.actual_duration_hours,
                work_order.scheduled_date.isoformat() if work_order.scheduled_date else None,
                work_order.start_date.isoformat() if work_order.start_date else None,
                work_order.completion_date.isoformat() if work_order.completion_date else None,
                json.dumps(work_order.parts_used), work_order.labor_cost,
                work_order.parts_cost, work_order.total_cost, work_order.notes,
                work_order.created_at.isoformat(), work_order.updated_at.isoformat(),
                json.dumps(work_order.metadata)
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"Created work order: {work_order.work_order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create work order: {e}")
            return False
    
    def get_floor_work_orders(self, floor_id: str, building_id: str, 
                            status: Optional[WorkOrderStatus] = None) -> List[WorkOrder]:
        """Get work orders for a floor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status:
                cursor.execute('''
                    SELECT * FROM work_orders 
                    WHERE floor_id = ? AND building_id = ? AND status = ?
                    ORDER BY created_at DESC
                ''', (floor_id, building_id, status.value))
            else:
                cursor.execute('''
                    SELECT * FROM work_orders 
                    WHERE floor_id = ? AND building_id = ?
                    ORDER BY created_at DESC
                ''', (floor_id, building_id))
            
            work_orders = []
            for row in cursor.fetchall():
                work_order = WorkOrder(
                    work_order_id=row[0],
                    floor_id=row[1],
                    building_id=row[2],
                    asset_id=row[3],
                    schedule_id=row[4],
                    title=row[5],
                    description=row[6],
                    maintenance_type=MaintenanceType(row[7]),
                    priority=PriorityLevel(row[8]),
                    status=WorkOrderStatus(row[9]),
                    assigned_technician=row[10],
                    requested_by=row[11],
                    estimated_duration_hours=row[12],
                    actual_duration_hours=row[13],
                    scheduled_date=datetime.fromisoformat(row[14]) if row[14] else None,
                    start_date=datetime.fromisoformat(row[15]) if row[15] else None,
                    completion_date=datetime.fromisoformat(row[16]) if row[16] else None,
                    parts_used=json.loads(row[17]) if row[17] else [],
                    labor_cost=row[18],
                    parts_cost=row[19],
                    total_cost=row[20],
                    notes=row[21],
                    created_at=datetime.fromisoformat(row[22]),
                    updated_at=datetime.fromisoformat(row[23]),
                    metadata=json.loads(row[24]) if row[24] else {}
                )
                work_orders.append(work_order)
            
            conn.close()
            return work_orders
            
        except Exception as e:
            logger.error(f"Failed to get work orders: {e}")
            return []
    
    def update_work_order_status(self, work_order_id: str, status: WorkOrderStatus,
                               technician: Optional[str] = None) -> bool:
        """Update work order status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if technician:
                cursor.execute('''
                    UPDATE work_orders SET 
                        status = ?, assigned_technician = ?, updated_at = ?
                    WHERE work_order_id = ?
                ''', (status.value, technician, datetime.utcnow().isoformat(), work_order_id))
            else:
                cursor.execute('''
                    UPDATE work_orders SET 
                        status = ?, updated_at = ?
                    WHERE work_order_id = ?
                ''', (status.value, datetime.utcnow().isoformat(), work_order_id))
            
            conn.commit()
            conn.close()
            logger.info(f"Updated work order {work_order_id} status to {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update work order status: {e}")
            return False

class CMMSIntegrationService:
    """Main CMMS integration service"""
    
    def __init__(self, db_path: str = "./data/cmms.db"):
        self.db_path = db_path
        self.asset_manager = FloorAssetManager(db_path)
        self.scheduler = MaintenanceScheduler(db_path)
        self.work_order_manager = WorkOrderManager(db_path)
    
    async def add_floor_asset(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a floor asset"""
        try:
            asset = FloorAsset(
                asset_id=str(uuid.uuid4()),
                floor_id=asset_data["floor_id"],
                building_id=asset_data["building_id"],
                asset_name=asset_data["asset_name"],
                asset_type=asset_data["asset_type"],
                location_x=asset_data["location_x"],
                location_y=asset_data["location_y"],
                manufacturer=asset_data.get("manufacturer"),
                model=asset_data.get("model"),
                serial_number=asset_data.get("serial_number"),
                installation_date=datetime.fromisoformat(asset_data["installation_date"]) if asset_data.get("installation_date") else None,
                maintenance_interval_days=asset_data.get("maintenance_interval_days", 365),
                metadata=asset_data.get("metadata", {})
            )
            
            success = self.asset_manager.add_floor_asset(asset)
            
            if success:
                return {
                    "success": True,
                    "asset_id": asset.asset_id,
                    "message": "Asset added successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to add asset"
                }
                
        except Exception as e:
            logger.error(f"Error adding floor asset: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    async def get_floor_assets(self, floor_id: str, building_id: str) -> Dict[str, Any]:
        """Get all assets for a floor"""
        try:
            assets = self.asset_manager.get_floor_assets(floor_id, building_id)
            
            asset_list = []
            for asset in assets:
                asset_list.append({
                    "asset_id": asset.asset_id,
                    "floor_id": asset.floor_id,
                    "building_id": asset.building_id,
                    "asset_name": asset.asset_name,
                    "asset_type": asset.asset_type,
                    "location_x": asset.location_x,
                    "location_y": asset.location_y,
                    "manufacturer": asset.manufacturer,
                    "model": asset.model,
                    "serial_number": asset.serial_number,
                    "installation_date": asset.installation_date.isoformat() if asset.installation_date else None,
                    "last_maintenance": asset.last_maintenance.isoformat() if asset.last_maintenance else None,
                    "next_maintenance": asset.next_maintenance.isoformat() if asset.next_maintenance else None,
                    "status": asset.status,
                    "condition": asset.condition,
                    "maintenance_interval_days": asset.maintenance_interval_days,
                    "created_at": asset.created_at.isoformat(),
                    "updated_at": asset.updated_at.isoformat(),
                    "metadata": asset.metadata
                })
            
            return {
                "success": True,
                "floor_id": floor_id,
                "building_id": building_id,
                "assets": asset_list,
                "total_assets": len(asset_list)
            }
            
        except Exception as e:
            logger.error(f"Error getting floor assets: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    async def create_maintenance_schedule(self, schedule_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a maintenance schedule"""
        try:
            schedule = MaintenanceSchedule(
                schedule_id=str(uuid.uuid4()),
                floor_id=schedule_data["floor_id"],
                building_id=schedule_data["building_id"],
                asset_id=schedule_data.get("asset_id"),
                maintenance_type=MaintenanceType(schedule_data["maintenance_type"]),
                frequency_days=schedule_data["frequency_days"],
                description=schedule_data.get("description", ""),
                assigned_technician=schedule_data.get("assigned_technician"),
                estimated_duration_hours=schedule_data.get("estimated_duration_hours", 2.0),
                parts_required=schedule_data.get("parts_required", []),
                instructions=schedule_data.get("instructions", ""),
                next_scheduled=datetime.utcnow() + timedelta(days=schedule_data["frequency_days"]),
                metadata=schedule_data.get("metadata", {})
            )
            
            success = self.scheduler.add_maintenance_schedule(schedule)
            
            if success:
                return {
                    "success": True,
                    "schedule_id": schedule.schedule_id,
                    "message": "Maintenance schedule created successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to create maintenance schedule"
                }
                
        except Exception as e:
            logger.error(f"Error creating maintenance schedule: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    async def get_floor_schedules(self, floor_id: str, building_id: str) -> Dict[str, Any]:
        """Get maintenance schedules for a floor"""
        try:
            schedules = self.scheduler.get_floor_schedules(floor_id, building_id)
            
            schedule_list = []
            for schedule in schedules:
                schedule_list.append({
                    "schedule_id": schedule.schedule_id,
                    "floor_id": schedule.floor_id,
                    "building_id": schedule.building_id,
                    "asset_id": schedule.asset_id,
                    "maintenance_type": schedule.maintenance_type.value,
                    "frequency_days": schedule.frequency_days,
                    "description": schedule.description,
                    "assigned_technician": schedule.assigned_technician,
                    "estimated_duration_hours": schedule.estimated_duration_hours,
                    "parts_required": schedule.parts_required,
                    "instructions": schedule.instructions,
                    "is_active": schedule.is_active,
                    "last_executed": schedule.last_executed.isoformat() if schedule.last_executed else None,
                    "next_scheduled": schedule.next_scheduled.isoformat() if schedule.next_scheduled else None,
                    "created_at": schedule.created_at.isoformat(),
                    "updated_at": schedule.updated_at.isoformat(),
                    "metadata": schedule.metadata
                })
            
            return {
                "success": True,
                "floor_id": floor_id,
                "building_id": building_id,
                "schedules": schedule_list,
                "total_schedules": len(schedule_list)
            }
            
        except Exception as e:
            logger.error(f"Error getting floor schedules: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    async def create_work_order(self, work_order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a work order"""
        try:
            work_order = WorkOrder(
                work_order_id=str(uuid.uuid4()),
                floor_id=work_order_data["floor_id"],
                building_id=work_order_data["building_id"],
                asset_id=work_order_data.get("asset_id"),
                schedule_id=work_order_data.get("schedule_id"),
                title=work_order_data["title"],
                description=work_order_data.get("description", ""),
                maintenance_type=MaintenanceType(work_order_data["maintenance_type"]),
                priority=PriorityLevel(work_order_data["priority"]),
                assigned_technician=work_order_data.get("assigned_technician"),
                requested_by=work_order_data.get("requested_by"),
                estimated_duration_hours=work_order_data.get("estimated_duration_hours", 2.0),
                scheduled_date=datetime.fromisoformat(work_order_data["scheduled_date"]) if work_order_data.get("scheduled_date") else None,
                notes=work_order_data.get("notes", ""),
                metadata=work_order_data.get("metadata", {})
            )
            
            success = self.work_order_manager.create_work_order(work_order)
            
            if success:
                return {
                    "success": True,
                    "work_order_id": work_order.work_order_id,
                    "message": "Work order created successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to create work order"
                }
                
        except Exception as e:
            logger.error(f"Error creating work order: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    async def get_floor_work_orders(self, floor_id: str, building_id: str,
                                  status: Optional[str] = None) -> Dict[str, Any]:
        """Get work orders for a floor"""
        try:
            work_order_status = WorkOrderStatus(status) if status else None
            work_orders = self.work_order_manager.get_floor_work_orders(
                floor_id, building_id, work_order_status
            )
            
            work_order_list = []
            for work_order in work_orders:
                work_order_list.append({
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
                    "scheduled_date": work_order.scheduled_date.isoformat() if work_order.scheduled_date else None,
                    "start_date": work_order.start_date.isoformat() if work_order.start_date else None,
                    "completion_date": work_order.completion_date.isoformat() if work_order.completion_date else None,
                    "parts_used": work_order.parts_used,
                    "labor_cost": work_order.labor_cost,
                    "parts_cost": work_order.parts_cost,
                    "total_cost": work_order.total_cost,
                    "notes": work_order.notes,
                    "created_at": work_order.created_at.isoformat(),
                    "updated_at": work_order.updated_at.isoformat(),
                    "metadata": work_order.metadata
                })
            
            return {
                "success": True,
                "floor_id": floor_id,
                "building_id": building_id,
                "work_orders": work_order_list,
                "total_work_orders": len(work_order_list),
                "filtered_by_status": status
            }
            
        except Exception as e:
            logger.error(f"Error getting floor work orders: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    async def update_work_order_status(self, work_order_id: str, status: str,
                                     technician: Optional[str] = None) -> Dict[str, Any]:
        """Update work order status"""
        try:
            work_order_status = WorkOrderStatus(status)
            success = self.work_order_manager.update_work_order_status(
                work_order_id, work_order_status, technician
            )
            
            if success:
                return {
                    "success": True,
                    "work_order_id": work_order_id,
                    "status": status,
                    "message": "Work order status updated successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to update work order status"
                }
                
        except Exception as e:
            logger.error(f"Error updating work order status: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }
    
    async def get_due_maintenance(self, floor_id: str, building_id: str) -> Dict[str, Any]:
        """Get maintenance schedules due for execution"""
        try:
            due_schedules = self.scheduler.get_due_schedules(floor_id, building_id)
            
            schedule_list = []
            for schedule in due_schedules:
                schedule_list.append({
                    "schedule_id": schedule.schedule_id,
                    "floor_id": schedule.floor_id,
                    "building_id": schedule.building_id,
                    "asset_id": schedule.asset_id,
                    "maintenance_type": schedule.maintenance_type.value,
                    "frequency_days": schedule.frequency_days,
                    "description": schedule.description,
                    "assigned_technician": schedule.assigned_technician,
                    "estimated_duration_hours": schedule.estimated_duration_hours,
                    "parts_required": schedule.parts_required,
                    "instructions": schedule.instructions,
                    "last_executed": schedule.last_executed.isoformat() if schedule.last_executed else None,
                    "next_scheduled": schedule.next_scheduled.isoformat() if schedule.next_scheduled else None,
                    "days_overdue": (datetime.utcnow() - schedule.next_scheduled).days if schedule.next_scheduled else 0
                })
            
            return {
                "success": True,
                "floor_id": floor_id,
                "building_id": building_id,
                "due_schedules": schedule_list,
                "total_due": len(schedule_list)
            }
            
        except Exception as e:
            logger.error(f"Error getting due maintenance: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }

    # --- Asset Lifecycle Management Extensions ---
    async def log_lifecycle_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Log a lifecycle event for a floor asset (install, maintain, repair, replace, retire)"""
        # For demo: store in maintenance_history with event type in metadata
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            history_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            cursor.execute('''
                INSERT INTO maintenance_history (
                    history_id, floor_id, building_id, asset_id, work_order_id, maintenance_type,
                    performed_by, performed_date, description, parts_replaced, labor_hours, cost, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                history_id,
                event["floor_id"],
                event["building_id"],
                event.get("asset_id"),
                event.get("work_order_id"),
                event.get("maintenance_type", "inspection"),
                event.get("performed_by", "system"),
                event.get("performed_date", now),
                event.get("description", event.get("event_type", "event")),
                json.dumps(event.get("parts_replaced", [])),
                event.get("labor_hours", 0.0),
                event.get("cost"),
                event.get("notes", event.get("event_type", "event")),
                now
            ))
            conn.commit()
            conn.close()
            return {"success": True, "history_id": history_id, "message": "Lifecycle event logged"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def get_lifecycle_events(self, floor_id: str, building_id: str, asset_id: str) -> Dict[str, Any]:
        """Get lifecycle events for a specific asset on a floor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM maintenance_history WHERE floor_id = ? AND building_id = ? AND asset_id = ?
                ORDER BY performed_date DESC
            ''', (floor_id, building_id, asset_id))
            events = []
            for row in cursor.fetchall():
                events.append({
                    "history_id": row[0],
                    "floor_id": row[1],
                    "building_id": row[2],
                    "asset_id": row[3],
                    "work_order_id": row[4],
                    "maintenance_type": row[5],
                    "performed_by": row[6],
                    "performed_date": row[7],
                    "description": row[8],
                    "parts_replaced": json.loads(row[9]) if row[9] else [],
                    "labor_hours": row[10],
                    "cost": row[11],
                    "notes": row[12],
                    "created_at": row[13]
                })
            conn.close()
            return {"success": True, "events": events, "total": len(events)}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def create_replacement_schedule(self, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """Create a replacement schedule for a floor asset"""
        # For demo: store as a special maintenance schedule with type 'replacement'
        try:
            schedule_data = schedule.copy()
            schedule_data["maintenance_type"] = "replacement"
            schedule_data["description"] = schedule.get("description", "Asset replacement schedule")
            return await self.create_maintenance_schedule(schedule_data)
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def get_replacement_schedules(self, floor_id: str, building_id: str) -> Dict[str, Any]:
        """Get all replacement schedules for a floor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM maintenance_schedules WHERE floor_id = ? AND building_id = ? AND maintenance_type = 'replacement'
                ORDER BY next_scheduled
            ''', (floor_id, building_id))
            schedules = []
            for row in cursor.fetchall():
                schedules.append({
                    "schedule_id": row[0],
                    "floor_id": row[1],
                    "building_id": row[2],
                    "asset_id": row[3],
                    "maintenance_type": row[4],
                    "frequency_days": row[5],
                    "description": row[6],
                    "assigned_technician": row[7],
                    "estimated_duration_hours": row[8],
                    "parts_required": json.loads(row[9]) if row[9] else [],
                    "instructions": row[10],
                    "is_active": bool(row[11]),
                    "last_executed": row[12],
                    "next_scheduled": row[13],
                    "created_at": row[14],
                    "updated_at": row[15],
                    "metadata": json.loads(row[16]) if row[16] else {}
                })
            conn.close()
            return {"success": True, "schedules": schedules, "total": len(schedules)}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def get_asset_analytics(self, floor_id: str, building_id: str) -> Dict[str, Any]:
        """Get asset performance analytics for a floor (failures, downtime, MTBF, cost)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Example: count failures, sum downtime, average MTBF, total cost
            cursor.execute('''
                SELECT asset_id, COUNT(*) as events, SUM(labor_hours) as total_hours, SUM(cost) as total_cost
                FROM maintenance_history
                WHERE floor_id = ? AND building_id = ?
                GROUP BY asset_id
            ''', (floor_id, building_id))
            analytics = []
            for row in cursor.fetchall():
                analytics.append({
                    "asset_id": row[0],
                    "event_count": row[1],
                    "total_labor_hours": row[2],
                    "total_cost": row[3]
                })
            conn.close()
            return {"success": True, "analytics": analytics, "total_assets": len(analytics)}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def get_compliance_report(self, floor_id: str, building_id: str) -> Dict[str, Any]:
        """Get compliance report for all assets on a floor"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Example: assets with overdue maintenance or missing inspection
            cursor.execute('''
                SELECT a.asset_id, a.asset_name, a.asset_type, a.status, a.condition, a.next_maintenance, a.last_maintenance
                FROM floor_assets a
                WHERE a.floor_id = ? AND a.building_id = ?
            ''', (floor_id, building_id))
            assets = []
            now = datetime.utcnow()
            for row in cursor.fetchall():
                overdue = False
                if row[5]:
                    try:
                        next_maint = datetime.fromisoformat(row[5])
                        overdue = next_maint < now
                    except Exception:
                        overdue = False
                assets.append({
                    "asset_id": row[0],
                    "asset_name": row[1],
                    "asset_type": row[2],
                    "status": row[3],
                    "condition": row[4],
                    "next_maintenance": row[5],
                    "last_maintenance": row[6],
                    "overdue": overdue
                })
            conn.close()
            return {"success": True, "assets": assets, "total": len(assets)}
        except Exception as e:
            return {"success": False, "message": str(e)}

# Global service instance
cmms_integration_service = CMMSIntegrationService() 