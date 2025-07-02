"""
Asset Lifecycle Management Router
Handles floor-based asset lifecycle tracking, replacement schedules, analytics, and compliance reporting
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
from arx_svg_parser.services.cmms_integration import cmms_integration_service
from arx_svg_parser.utils.auth import get_current_user_optional

router = APIRouter(prefix="/asset-lifecycle", tags=["asset_lifecycle"])

# --- Asset Lifecycle Events ---
@router.post("/event")
async def log_lifecycle_event(event: Dict[str, Any], current_user: Optional[Dict] = Depends(get_current_user_optional)):
    """Log a lifecycle event for a floor asset (install, maintain, repair, replace, retire)"""
    try:
        result = await cmms_integration_service.log_lifecycle_event(event)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events/{building_id}/{floor_id}/{asset_id}")
async def get_lifecycle_events(building_id: str, floor_id: str, asset_id: str, current_user: Optional[Dict] = Depends(get_current_user_optional)):
    """Get lifecycle events for a specific asset on a floor"""
    try:
        result = await cmms_integration_service.get_lifecycle_events(floor_id, building_id, asset_id)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Replacement Schedules ---
@router.post("/replacement-schedule")
async def create_replacement_schedule(schedule: Dict[str, Any], current_user: Optional[Dict] = Depends(get_current_user_optional)):
    """Create a replacement schedule for a floor asset"""
    try:
        result = await cmms_integration_service.create_replacement_schedule(schedule)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/replacement-schedules/{building_id}/{floor_id}")
async def get_replacement_schedules(building_id: str, floor_id: str, current_user: Optional[Dict] = Depends(get_current_user_optional)):
    """Get all replacement schedules for a floor"""
    try:
        result = await cmms_integration_service.get_replacement_schedules(floor_id, building_id)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Analytics ---
@router.get("/analytics/{building_id}/{floor_id}")
async def get_asset_analytics(building_id: str, floor_id: str, current_user: Optional[Dict] = Depends(get_current_user_optional)):
    """Get asset performance analytics for a floor (failures, downtime, MTBF, cost)"""
    try:
        result = await cmms_integration_service.get_asset_analytics(floor_id, building_id)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Compliance Reporting ---
@router.get("/compliance/{building_id}/{floor_id}")
async def get_compliance_report(building_id: str, floor_id: str, current_user: Optional[Dict] = Depends(get_current_user_optional)):
    """Get compliance report for all assets on a floor"""
    try:
        result = await cmms_integration_service.get_compliance_report(floor_id, building_id)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 