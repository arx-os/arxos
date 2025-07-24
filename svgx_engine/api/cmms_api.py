"""
CMMS API for SVGX Engine

This module provides FastAPI endpoints for CMMS integration services including:
- Data synchronization
- Work order processing
- Maintenance scheduling
- Asset tracking
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union
from uuid import UUID

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from svgx_engine.services.cmms.data_synchronization import CMMSDataSynchronizationService
from svgx_engine.services.cmms.work_order_processing import WorkOrderProcessingService
from svgx_engine.services.cmms.maintenance_scheduling import MaintenanceSchedulingService
from svgx_engine.services.cmms.asset_tracking import AssetTrackingService

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CMMS Integration API",
    description="API for CMMS integration services including data synchronization, work orders, maintenance scheduling, and asset tracking",
    version="1.0.0"
)

# Initialize services
data_sync_service = CMMSDataSynchronizationService()
work_order_service = WorkOrderProcessingService()
maintenance_service = MaintenanceSchedulingService()
asset_tracking_service = AssetTrackingService()


# Data Models for API
class CMMSConnectionRequest(BaseModel):
    """Request model for adding CMMS connection"""
    cmms_type: str = Field(..., description="Type of CMMS system")
    api_url: str = Field(..., description="API endpoint URL")
    api_key: str = Field(..., description="API authentication key")
    username: Optional[str] = None
    password: Optional[str] = None
    connection_name: str = Field(..., description="Friendly name for connection")


class FieldMappingRequest(BaseModel):
    """Request model for field mapping"""
    cmms_connection_id: UUID = Field(..., description="CMMS connection ID")
    source_field: str = Field(..., description="Source field name")
    target_field: str = Field(..., description="Target field name")
    transformation_rule: Optional[str] = None
    is_required: bool = Field(default=False)


class SyncRequest(BaseModel):
    """Request model for data synchronization"""
    cmms_connection_id: UUID = Field(..., description="CMMS connection ID")
    sync_type: str = Field(..., description="Type of data to sync")
    force_sync: bool = Field(default=False)


class WorkOrderRequest(BaseModel):
    """Request model for work order operations"""
    template_id: Optional[UUID] = None
    asset_id: str = Field(..., description="Asset identifier")
    title: str = Field(..., description="Work order title")
    description: str = Field(..., description="Work order description")
    priority: str = Field(..., description="Priority level")
    estimated_hours: float = Field(..., description="Estimated hours")
    assigned_to: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None


class MaintenanceScheduleRequest(BaseModel):
    """Request model for maintenance schedule"""
    name: str = Field(..., description="Schedule name")
    description: str = Field(..., description="Schedule description")
    maintenance_type: str = Field(..., description="Type of maintenance")
    priority: str = Field(..., description="Priority level")
    frequency: str = Field(..., description="Frequency")
    trigger_type: str = Field(..., description="Trigger type")
    trigger_value: Union[int, float, str] = Field(..., description="Trigger value")
    estimated_duration: int = Field(..., description="Estimated duration in minutes")
    estimated_cost: float = Field(..., description="Estimated cost")
    required_skills: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    required_parts: List[str] = Field(default_factory=list)


class MaintenanceTaskRequest(BaseModel):
    """Request model for maintenance task"""
    schedule_id: UUID = Field(..., description="Schedule ID")
    asset_id: str = Field(..., description="Asset ID")
    scheduled_start: datetime = Field(..., description="Scheduled start time")
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_team: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class AssetRegistrationRequest(BaseModel):
    """Request model for asset registration"""
    asset_id: str = Field(..., description="Asset identifier")
    name: str = Field(..., description="Asset name")
    asset_type: str = Field(..., description="Type of asset")
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    installation_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    expected_lifespan: Optional[int] = None
    department: Optional[str] = None
    responsible_person: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    specifications: Dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)


class PerformanceDataRequest(BaseModel):
    """Request model for performance data"""
    asset_id: str = Field(..., description="Asset identifier")
    uptime_percentage: float = Field(..., description="Uptime percentage")
    efficiency_rating: float = Field(..., description="Efficiency rating")
    throughput: Optional[float] = None
    energy_consumption: Optional[float] = None
    temperature: Optional[float] = None
    vibration: Optional[float] = None
    pressure: Optional[float] = None
    speed: Optional[float] = None
    load_percentage: Optional[float] = None
    error_count: int = Field(default=0)
    warning_count: int = Field(default=0)
    maintenance_hours: Optional[float] = None
    cost_per_hour: Optional[float] = None


# Data Synchronization Endpoints
@app.post("/cmms/connections", response_model=Dict)
async def add_cmms_connection(request: CMMSConnectionRequest):
    """Add a new CMMS connection"""
    try:
        connection = await data_sync_service.add_cmms_connection(
            cmms_type=request.cmms_type,
            api_url=request.api_url,
            api_key=request.api_key,
            username=request.username,
            password=request.password,
            connection_name=request.connection_name
        )
        return {"success": True, "connection_id": str(connection.id), "message": "CMMS connection added successfully"}
    except Exception as e:
        logger.error(f"Failed to add CMMS connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cmms/mappings", response_model=Dict)
async def add_field_mapping(request: FieldMappingRequest):
    """Add a field mapping for data transformation"""
    try:
        mapping = await data_sync_service.add_field_mapping(
            cmms_connection_id=request.cmms_connection_id,
            source_field=request.source_field,
            target_field=request.target_field,
            transformation_rule=request.transformation_rule,
            is_required=request.is_required
        )
        return {"success": True, "mapping_id": str(mapping.id), "message": "Field mapping added successfully"}
    except Exception as e:
        logger.error(f"Failed to add field mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cmms/sync/work-orders", response_model=Dict)
async def sync_work_orders(request: SyncRequest):
    """Synchronize work orders from CMMS"""
    try:
        result = await data_sync_service.sync_work_orders(
            cmms_connection_id=request.cmms_connection_id,
            force_sync=request.force_sync
        )
        return {
            "success": True,
            "synced_count": result.synced_count,
            "errors": result.errors,
            "message": f"Synced {result.synced_count} work orders"
        }
    except Exception as e:
        logger.error(f"Failed to sync work orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cmms/sync/maintenance-schedules", response_model=Dict)
async def sync_maintenance_schedules(request: SyncRequest):
    """Synchronize maintenance schedules from CMMS"""
    try:
        result = await data_sync_service.sync_maintenance_schedules(
            cmms_connection_id=request.cmms_connection_id,
            force_sync=request.force_sync
        )
        return {
            "success": True,
            "synced_count": result.synced_count,
            "errors": result.errors,
            "message": f"Synced {result.synced_count} maintenance schedules"
        }
    except Exception as e:
        logger.error(f"Failed to sync maintenance schedules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cmms/sync/assets", response_model=Dict)
async def sync_assets(request: SyncRequest):
    """Synchronize assets from CMMS"""
    try:
        result = await data_sync_service.sync_assets(
            cmms_connection_id=request.cmms_connection_id,
            force_sync=request.force_sync
        )
        return {
            "success": True,
            "synced_count": result.synced_count,
            "errors": result.errors,
            "message": f"Synced {result.synced_count} assets"
        }
    except Exception as e:
        logger.error(f"Failed to sync assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cmms/sync/all", response_model=Dict)
async def sync_all_data(request: SyncRequest):
    """Synchronize all data from CMMS"""
    try:
        result = await data_sync_service.sync_all(
            cmms_connection_id=request.cmms_connection_id,
            force_sync=request.force_sync
        )
        return {
            "success": True,
            "work_orders_synced": result.work_orders_synced,
            "schedules_synced": result.schedules_synced,
            "assets_synced": result.assets_synced,
            "errors": result.errors,
            "message": "All data synchronized successfully"
        }
    except Exception as e:
        logger.error(f"Failed to sync all data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Work Order Processing Endpoints
@app.post("/work-orders", response_model=Dict)
async def create_work_order(request: WorkOrderRequest):
    """Create a new work order"""
    try:
        if request.template_id:
            work_order = await work_order_service.create_work_order_from_template(
                template_id=request.template_id,
                asset_id=request.asset_id,
                assigned_to=request.assigned_to,
                scheduled_start=request.scheduled_start,
                scheduled_end=request.scheduled_end
            )
        else:
            work_order = await work_order_service.create_work_order(
                asset_id=request.asset_id,
                title=request.title,
                description=request.description,
                priority=request.priority,
                estimated_hours=request.estimated_hours,
                assigned_to=request.assigned_to,
                scheduled_start=request.scheduled_start,
                scheduled_end=request.scheduled_end
            )
        
        return {
            "success": True,
            "work_order_id": str(work_order.id),
            "work_order_number": work_order.work_order_number,
            "message": "Work order created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create work order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/work-orders/{work_order_id}", response_model=Dict)
async def get_work_order(work_order_id: UUID):
    """Get work order by ID"""
    try:
        work_order = await work_order_service.get_work_order(work_order_id)
        if not work_order:
            raise HTTPException(status_code=404, detail="Work order not found")
        
        return {"success": True, "work_order": work_order.dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get work order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/work-orders", response_model=Dict)
async def get_work_orders(
    status: Optional[str] = None,
    asset_id: Optional[str] = None,
    assigned_to: Optional[str] = None
):
    """Get work orders with optional filters"""
    try:
        work_orders = await work_order_service.get_work_orders(
            status=status,
            asset_id=asset_id,
            assigned_to=assigned_to
        )
        
        return {
            "success": True,
            "work_orders": [wo.dict() for wo in work_orders],
            "count": len(work_orders)
        }
    except Exception as e:
        logger.error(f"Failed to get work orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/work-orders/{work_order_id}/status", response_model=Dict)
async def update_work_order_status(work_order_id: UUID, status: str):
    """Update work order status"""
    try:
        work_order = await work_order_service.update_work_order_status(work_order_id, status)
        if not work_order:
            raise HTTPException(status_code=404, detail="Work order not found")
        
        return {"success": True, "message": f"Work order status updated to {status}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update work order status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Maintenance Scheduling Endpoints
@app.post("/maintenance/schedules", response_model=Dict)
async def create_maintenance_schedule(request: MaintenanceScheduleRequest):
    """Create a new maintenance schedule"""
    try:
        schedule = await maintenance_service.create_maintenance_schedule(
            name=request.name,
            description=request.description,
            maintenance_type=request.maintenance_type,
            priority=request.priority,
            frequency=request.frequency,
            trigger_type=request.trigger_type,
            trigger_value=request.trigger_value,
            estimated_duration=request.estimated_duration,
            estimated_cost=request.estimated_cost,
            required_skills=request.required_skills,
            required_tools=request.required_tools,
            required_parts=request.required_parts
        )
        
        return {
            "success": True,
            "schedule_id": str(schedule.id),
            "message": "Maintenance schedule created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create maintenance schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/maintenance/schedules", response_model=Dict)
async def get_maintenance_schedules():
    """Get all maintenance schedules"""
    try:
        schedules = await maintenance_service.get_all_maintenance_schedules()
        return {
            "success": True,
            "schedules": [s.dict() for s in schedules],
            "count": len(schedules)
        }
    except Exception as e:
        logger.error(f"Failed to get maintenance schedules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/maintenance/tasks", response_model=Dict)
async def create_maintenance_task(request: MaintenanceTaskRequest):
    """Create a new maintenance task"""
    try:
        task = await maintenance_service.create_maintenance_task(
            schedule_id=request.schedule_id,
            asset_id=request.asset_id,
            scheduled_start=request.scheduled_start,
            priority=request.priority,
            assigned_to=request.assigned_to,
            assigned_team=request.assigned_team,
            location=request.location,
            notes=request.notes
        )
        
        if not task:
            raise HTTPException(status_code=404, detail="Maintenance schedule not found")
        
        return {
            "success": True,
            "task_id": str(task.id),
            "message": "Maintenance task created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create maintenance task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/maintenance/tasks", response_model=Dict)
async def get_maintenance_tasks(
    status: Optional[str] = None,
    asset_id: Optional[str] = None,
    assigned_to: Optional[str] = None
):
    """Get maintenance tasks with optional filters"""
    try:
        tasks = await maintenance_service.get_maintenance_tasks(
            status=status,
            asset_id=asset_id,
            assigned_to=assigned_to
        )
        
        return {
            "success": True,
            "tasks": [t.dict() for t in tasks],
            "count": len(tasks)
        }
    except Exception as e:
        logger.error(f"Failed to get maintenance tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/maintenance/tasks/{task_id}/start", response_model=Dict)
async def start_maintenance_task(task_id: UUID, performer: str):
    """Start a maintenance task"""
    try:
        task = await maintenance_service.start_maintenance_task(task_id, performer)
        if not task:
            raise HTTPException(status_code=404, detail="Maintenance task not found")
        
        return {"success": True, "message": "Maintenance task started successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start maintenance task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/maintenance/tasks/{task_id}/complete", response_model=Dict)
async def complete_maintenance_task(
    task_id: UUID,
    actual_duration: Optional[int] = None,
    actual_cost: Optional[float] = None,
    notes: Optional[str] = None,
    findings: Optional[str] = None,
    recommendations: Optional[str] = None
):
    """Complete a maintenance task"""
    try:
        task = await maintenance_service.complete_maintenance_task(
            task_id=task_id,
            actual_duration=actual_duration,
            actual_cost=actual_cost,
            notes=notes,
            findings=findings,
            recommendations=recommendations
        )
        
        if not task:
            raise HTTPException(status_code=404, detail="Maintenance task not found")
        
        return {"success": True, "message": "Maintenance task completed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete maintenance task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/maintenance/schedule-recurring", response_model=Dict)
async def schedule_recurring_maintenance():
    """Schedule recurring maintenance tasks"""
    try:
        new_tasks = await maintenance_service.schedule_recurring_maintenance()
        return {
            "success": True,
            "new_tasks_count": len(new_tasks),
            "message": f"Scheduled {len(new_tasks)} new maintenance tasks"
        }
    except Exception as e:
        logger.error(f"Failed to schedule recurring maintenance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/maintenance/statistics", response_model=Dict)
async def get_maintenance_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get maintenance statistics"""
    try:
        stats = await maintenance_service.get_maintenance_statistics(
            start_date=start_date,
            end_date=end_date
        )
        return {"success": True, "statistics": stats}
    except Exception as e:
        logger.error(f"Failed to get maintenance statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Asset Tracking Endpoints
@app.post("/assets", response_model=Dict)
async def register_asset(request: AssetRegistrationRequest):
    """Register a new asset"""
    try:
        asset = await asset_tracking_service.register_asset(
            asset_id=request.asset_id,
            name=request.name,
            asset_type=request.asset_type,
            description=request.description,
            manufacturer=request.manufacturer,
            model=request.model,
            serial_number=request.serial_number,
            installation_date=request.installation_date,
            warranty_expiry=request.warranty_expiry,
            expected_lifespan=request.expected_lifespan,
            department=request.department,
            responsible_person=request.responsible_person,
            tags=request.tags,
            specifications=request.specifications
        )
        
        return {
            "success": True,
            "asset_id": asset.id,
            "message": "Asset registered successfully"
        }
    except Exception as e:
        logger.error(f"Failed to register asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assets/{asset_id}", response_model=Dict)
async def get_asset(asset_id: str):
    """Get asset by ID"""
    try:
        asset = await asset_tracking_service.get_asset(asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        return {"success": True, "asset": asset.dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assets", response_model=Dict)
async def get_assets(
    asset_type: Optional[str] = None,
    status: Optional[str] = None,
    department: Optional[str] = None
):
    """Get assets with optional filters"""
    try:
        assets = await asset_tracking_service.get_all_assets(
            asset_type=asset_type,
            status=status,
            department=department
        )
        
        return {
            "success": True,
            "assets": [a.dict() for a in assets],
            "count": len(assets)
        }
    except Exception as e:
        logger.error(f"Failed to get assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assets/{asset_id}/location", response_model=Dict)
async def update_asset_location(
    asset_id: str,
    location_name: str,
    building: Optional[str] = None,
    floor: Optional[str] = None,
    room: Optional[str] = None,
    coordinates: Optional[List[float]] = None,
    address: Optional[str] = None,
    zone: Optional[str] = None,
    department: Optional[str] = None,
    updated_by: Optional[str] = None
):
    """Update asset location"""
    try:
        coords_tuple = tuple(coordinates) if coordinates else None
        
        location = await asset_tracking_service.update_asset_location(
            asset_id=asset_id,
            location_name=location_name,
            building=building,
            floor=floor,
            room=room,
            coordinates=coords_tuple,
            address=address,
            zone=zone,
            department=department,
            updated_by=updated_by
        )
        
        if not location:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        return {"success": True, "message": "Asset location updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update asset location: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assets/{asset_id}/condition", response_model=Dict)
async def assess_asset_condition(
    asset_id: str,
    condition: str,
    assessed_by: str,
    notes: Optional[str] = None,
    visual_inspection: Optional[str] = None,
    functional_test: Optional[str] = None,
    performance_metrics: Optional[Dict] = None,
    recommendations: Optional[str] = None,
    next_assessment_date: Optional[datetime] = None
):
    """Assess asset condition"""
    try:
        condition_assessment = await asset_tracking_service.assess_asset_condition(
            asset_id=asset_id,
            condition=condition,
            assessed_by=assessed_by,
            notes=notes,
            visual_inspection=visual_inspection,
            functional_test=functional_test,
            performance_metrics=performance_metrics,
            recommendations=recommendations,
            next_assessment_date=next_assessment_date
        )
        
        if not condition_assessment:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        return {"success": True, "message": "Asset condition assessed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to assess asset condition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assets/{asset_id}/performance", response_model=Dict)
async def record_performance_data(asset_id: str, request: PerformanceDataRequest):
    """Record performance data for an asset"""
    try:
        performance = await asset_tracking_service.record_performance_data(
            asset_id=asset_id,
            uptime_percentage=request.uptime_percentage,
            efficiency_rating=request.efficiency_rating,
            throughput=request.throughput,
            energy_consumption=request.energy_consumption,
            temperature=request.temperature,
            vibration=request.vibration,
            pressure=request.pressure,
            speed=request.speed,
            load_percentage=request.load_percentage,
            error_count=request.error_count,
            warning_count=request.warning_count,
            maintenance_hours=request.maintenance_hours,
            cost_per_hour=request.cost_per_hour
        )
        
        if not performance:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        return {"success": True, "message": "Performance data recorded successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record performance data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assets/{asset_id}/performance", response_model=Dict)
async def get_asset_performance_history(
    asset_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get asset performance history"""
    try:
        performance_data = await asset_tracking_service.get_asset_performance_history(
            asset_id=asset_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "success": True,
            "performance_data": [p.dict() for p in performance_data],
            "count": len(performance_data)
        }
    except Exception as e:
        logger.error(f"Failed to get asset performance history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assets/{asset_id}/alerts", response_model=Dict)
async def get_asset_alerts(
    asset_id: str,
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    is_acknowledged: Optional[bool] = None,
    is_resolved: Optional[bool] = None
):
    """Get asset alerts"""
    try:
        alerts = await asset_tracking_service.get_asset_alerts(
            asset_id=asset_id,
            alert_type=alert_type,
            severity=severity,
            is_acknowledged=is_acknowledged,
            is_resolved=is_resolved
        )
        
        return {
            "success": True,
            "alerts": [a.dict() for a in alerts],
            "count": len(alerts)
        }
    except Exception as e:
        logger.error(f"Failed to get asset alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assets/{asset_id}/alerts/{alert_id}/acknowledge", response_model=Dict)
async def acknowledge_asset_alert(asset_id: str, alert_id: UUID, acknowledged_by: str):
    """Acknowledge an asset alert"""
    try:
        alert = await asset_tracking_service.acknowledge_alert(alert_id, acknowledged_by)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"success": True, "message": "Alert acknowledged successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assets/{asset_id}/alerts/{alert_id}/resolve", response_model=Dict)
async def resolve_asset_alert(
    asset_id: str,
    alert_id: UUID,
    resolved_by: str,
    resolution_notes: Optional[str] = None
):
    """Resolve an asset alert"""
    try:
        alert = await asset_tracking_service.resolve_alert(alert_id, resolved_by, resolution_notes)
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return {"success": True, "message": "Alert resolved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/assets/statistics", response_model=Dict)
async def get_asset_statistics(
    asset_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get asset statistics"""
    try:
        stats = await asset_tracking_service.get_asset_statistics(
            asset_id=asset_id,
            start_date=start_date,
            end_date=end_date
        )
        return {"success": True, "statistics": stats}
    except Exception as e:
        logger.error(f"Failed to get asset statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@app.get("/health", response_model=Dict)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CMMS Integration API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 