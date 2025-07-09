"""
Export Interoperability API Router

Provides REST API endpoints for export and interoperability functionality:
- IFC-lite export
- glTF export
- ASCII-BIM export
- Excel export
- GeoJSON export
- Export job management
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import tempfile
import logging

from services.export_interoperability import (
    ExportInteroperabilityService, ExportFormat, ExportStatus
)
from utils.response_helpers import ResponseHelper
from utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["Export & Interoperability"])

# Initialize export service
export_service = ExportInteroperabilityService()

class ExportRequest(BaseModel):
    """Export request model."""
    building_id: str = Field(..., description="Building ID to export")
    format: ExportFormat = Field(..., description="Export format")
    options: Dict[str, Any] = Field(default_factory=dict, description="Export options")

class ExportJobResponse(BaseModel):
    """Export job response model."""
    job_id: str
    building_id: str
    format: ExportFormat
    status: ExportStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExportStatisticsResponse(BaseModel):
    """Export statistics response model."""
    total_jobs: int
    by_format: Dict[str, Dict[str, int]]
    by_status: Dict[str, int]

@router.post("/create-job", response_model=ExportJobResponse)
async def create_export_job(
    request: ExportRequest,
    current_user: str = Depends(get_current_user)
):
    """Create a new export job."""
    try:
        job_id = export_service.create_export_job(
            building_id=request.building_id,
            format=request.format,
            options=request.options
        )
        
        job = export_service.get_export_job_status(job_id)
        
        logger.info(f"Created export job {job_id} for building {request.building_id}")
        
        return ExportJobResponse(
            job_id=job.job_id,
            building_id=job.building_id,
            format=job.format,
            status=job.status,
            created_at=job.created_at,
            completed_at=job.completed_at,
            file_path=job.file_path,
            error_message=job.error_message,
            metadata=job.metadata
        )
        
    except Exception as e:
        logger.error(f"Failed to create export job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create export job: {str(e)}")

@router.get("/jobs", response_model=List[ExportJobResponse])
async def list_export_jobs(
    building_id: Optional[str] = None,
    current_user: str = Depends(get_current_user)
):
    """List export jobs, optionally filtered by building ID."""
    try:
        jobs = export_service.list_export_jobs(building_id=building_id)
        
        return [
            ExportJobResponse(
                job_id=job.job_id,
                building_id=job.building_id,
                format=job.format,
                status=job.status,
                created_at=job.created_at,
                completed_at=job.completed_at,
                file_path=job.file_path,
                error_message=job.error_message,
                metadata=job.metadata
            )
            for job in jobs
        ]
        
    except Exception as e:
        logger.error(f"Failed to list export jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list export jobs: {str(e)}")

@router.get("/jobs/{job_id}", response_model=ExportJobResponse)
async def get_export_job_status(
    job_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get export job status."""
    try:
        job = export_service.get_export_job_status(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Export job not found")
        
        return ExportJobResponse(
            job_id=job.job_id,
            building_id=job.building_id,
            format=job.format,
            status=job.status,
            created_at=job.created_at,
            completed_at=job.completed_at,
            file_path=job.file_path,
            error_message=job.error_message,
            metadata=job.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get export job status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get export job status: {str(e)}")

@router.delete("/jobs/{job_id}")
async def cancel_export_job(
    job_id: str,
    current_user: str = Depends(get_current_user)
):
    """Cancel an export job."""
    try:
        result = export_service.cancel_export_job(job_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Export job not found")
        
        logger.info(f"Cancelled export job {job_id}")
        
        return {"message": "Export job cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel export job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel export job: {str(e)}")

@router.get("/statistics", response_model=ExportStatisticsResponse)
async def get_export_statistics(
    current_user: str = Depends(get_current_user)
):
    """Get export statistics."""
    try:
        stats = export_service.get_export_statistics()
        
        return ExportStatisticsResponse(
            total_jobs=stats["total_jobs"],
            by_format=stats["by_format"],
            by_status=stats["by_status"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get export statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get export statistics: {str(e)}")

@router.post("/export-ifc-lite")
async def export_to_ifc_lite(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """Export building data to IFC-lite format."""
    try:
        # Create temporary file for export
        with tempfile.NamedTemporaryFile(suffix='.ifc', delete=False) as f:
            temp_path = f.name
        
        # Update options with temporary path
        options = request.options.copy()
        options["output_path"] = temp_path
        
        # Perform export
        result_path = export_service.export_to_ifc_lite(
            building_data={"building_id": request.building_id},  # Simplified for demo
            options=options
        )
        
        logger.info(f"IFC-lite export completed: {result_path}")
        
        # Return file as download
        return FileResponse(
            path=result_path,
            filename=f"{request.building_id}_ifc_lite.ifc",
            media_type="application/octet-stream"
        )
        
    except Exception as e:
        logger.error(f"IFC-lite export failed: {e}")
        raise HTTPException(status_code=500, detail=f"IFC-lite export failed: {str(e)}")

@router.post("/export-gltf")
async def export_to_gltf(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """Export building data to glTF format."""
    try:
        # Create temporary file for export
        with tempfile.NamedTemporaryFile(suffix='.gltf', delete=False) as f:
            temp_path = f.name
        
        # Update options with temporary path
        options = request.options.copy()
        options["output_path"] = temp_path
        
        # Perform export
        result_path = export_service.export_to_gltf(
            building_data={"building_id": request.building_id},  # Simplified for demo
            options=options
        )
        
        logger.info(f"glTF export completed: {result_path}")
        
        # Return file as download
        return FileResponse(
            path=result_path,
            filename=f"{request.building_id}_gltf.gltf",
            media_type="application/json"
        )
        
    except Exception as e:
        logger.error(f"glTF export failed: {e}")
        raise HTTPException(status_code=500, detail=f"glTF export failed: {str(e)}")

@router.post("/export-ascii-bim")
async def export_to_ascii_bim(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """Export building data to ASCII-BIM format."""
    try:
        # Create temporary file for export
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            temp_path = f.name
        
        # Update options with temporary path
        options = request.options.copy()
        options["output_path"] = temp_path
        
        # Perform export
        result_path = export_service.export_to_ascii_bim(
            building_data={"building_id": request.building_id},  # Simplified for demo
            options=options
        )
        
        logger.info(f"ASCII-BIM export completed: {result_path}")
        
        # Return file as download
        return FileResponse(
            path=result_path,
            filename=f"{request.building_id}_ascii_bim.txt",
            media_type="text/plain"
        )
        
    except Exception as e:
        logger.error(f"ASCII-BIM export failed: {e}")
        raise HTTPException(status_code=500, detail=f"ASCII-BIM export failed: {str(e)}")

@router.post("/export-geojson")
async def export_to_geojson(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """Export building data to GeoJSON format."""
    try:
        # Create temporary file for export
        with tempfile.NamedTemporaryFile(suffix='.geojson', delete=False) as f:
            temp_path = f.name
        
        # Update options with temporary path
        options = request.options.copy()
        options["output_path"] = temp_path
        
        # Perform export
        result_path = export_service.export_to_geojson(
            building_data={"building_id": request.building_id},  # Simplified for demo
            options=options
        )
        
        logger.info(f"GeoJSON export completed: {result_path}")
        
        # Return file as download
        return FileResponse(
            path=result_path,
            filename=f"{request.building_id}_geojson.geojson",
            media_type="application/geo+json"
        )
        
    except Exception as e:
        logger.error(f"GeoJSON export failed: {e}")
        raise HTTPException(status_code=500, detail=f"GeoJSON export failed: {str(e)}")

@router.post("/export-excel")
async def export_to_excel(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_user)
):
    """Export building data to Excel format."""
    try:
        # Create temporary file for export
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            temp_path = f.name
        
        # Update options with temporary path
        options = request.options.copy()
        options["output_path"] = temp_path
        
        # Perform export
        result_path = export_service.export_to_excel(
            building_data={"building_id": request.building_id},  # Simplified for demo
            options=options
        )
        
        logger.info(f"Excel export completed: {result_path}")
        
        # Return file as download
        return FileResponse(
            path=result_path,
            filename=f"{request.building_id}_excel.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        logger.error(f"Excel export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Excel export failed: {str(e)}")

@router.get("/formats")
async def get_supported_formats():
    """Get list of supported export formats."""
    return {
        "formats": [
            {
                "value": format.value,
                "name": format.name,
                "description": f"Export to {format.value.replace('_', ' ').title()} format"
            }
            for format in ExportFormat
        ]
    }

@router.get("/statuses")
async def get_export_statuses():
    """Get list of export status values."""
    return {
        "statuses": [
            {
                "value": status.value,
                "name": status.name,
                "description": f"Export job is {status.value}"
            }
            for status in ExportStatus
        ]
    } 