"""
Advanced Export & Interoperability API Router

Provides RESTful API endpoints for BIM data export in various industry-standard formats:
- IFC-lite for BIM interoperability
- glTF for 3D visualization  
- ASCII-BIM for roundtrip conversion
- Excel, Parquet, GeoJSON for analytics and GIS
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from pathlib import Path
import tempfile
import os
import uuid
from datetime import datetime

from services.advanced_export_interoperability import (
    AdvancedExportInteroperabilityService,
    ExportFormat
)

# Initialize router
router = APIRouter(prefix="/api/v1/export", tags=["Advanced Export & Interoperability"])

# Initialize service
export_service = AdvancedExportInteroperabilityService()

# Pydantic models for request/response
class ExportRequest(BaseModel):
    """Export request model."""
    data: Dict[str, Any] = Field(..., description="BIM data to export")
    format: str = Field(..., description="Export format (ifc-lite, gltf, ascii-bim, excel, parquet, geojson)")
    options: Optional[Dict[str, Any]] = Field(None, description="Export options")
    filename: Optional[str] = Field(None, description="Output filename")

class ExportResponse(BaseModel):
    """Export response model."""
    success: bool = Field(..., description="Export success status")
    file_path: Optional[str] = Field(None, description="Path to exported file")
    format: str = Field(..., description="Export format used")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    export_time: Optional[float] = Field(None, description="Export time in seconds")
    message: str = Field(..., description="Export result message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ExportStatusResponse(BaseModel):
    """Export status response model."""
    export_id: str = Field(..., description="Unique export ID")
    status: str = Field(..., description="Export status (pending, processing, completed, failed)")
    progress: float = Field(..., description="Export progress (0-100)")
    format: str = Field(..., description="Export format")
    created_at: datetime = Field(..., description="Export creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Export completion timestamp")
    file_path: Optional[str] = Field(None, description="Path to exported file")
    error_message: Optional[str] = Field(None, description="Error message if failed")

class SupportedFormatsResponse(BaseModel):
    """Supported export formats response."""
    formats: List[Dict[str, Any]] = Field(..., description="List of supported export formats")
    total_formats: int = Field(..., description="Total number of supported formats")

# In-memory storage for export jobs (in production, use Redis or database)
export_jobs = {}

@router.post("/export", response_model=ExportResponse)
async def export_bim_data(
    request: ExportRequest,
    background_tasks: BackgroundTasks
):
    """
    Export BIM data to specified format.
    
    Args:
        request: Export request with data, format, and options
        background_tasks: FastAPI background tasks for async processing
        
    Returns:
        ExportResponse with export details
    """
    try:
        # Validate export format
        if request.format not in [
            ExportFormat.IFC_LITE,
            ExportFormat.GLTF,
            ExportFormat.ASCII_BIM,
            ExportFormat.EXCEL,
            ExportFormat.PARQUET,
            ExportFormat.GEOJSON
        ]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported export format: {request.format}"
            )
        
        # Generate unique export ID
        export_id = str(uuid.uuid4())
        
        # Create temporary file path
        filename = request.filename or f"export_{export_id}.{request.format}"
        temp_dir = Path(tempfile.gettempdir()) / "arxos_exports"
        temp_dir.mkdir(exist_ok=True)
        output_path = temp_dir / filename
        
        # Record export job
        export_jobs[export_id] = {
            "status": "processing",
            "progress": 0,
            "format": request.format,
            "created_at": datetime.now(),
            "output_path": str(output_path),
            "error_message": None
        }
        
        # Perform export
        start_time = datetime.now()
        exported_path = export_service.export(
            data=request.data,
            format=request.format,
            output_path=output_path,
            options=request.options
        )
        end_time = datetime.now()
        
        # Update job status
        export_jobs[export_id].update({
            "status": "completed",
            "progress": 100,
            "completed_at": end_time,
            "file_path": str(exported_path)
        })
        
        # Get file size
        file_size = exported_path.stat().st_size if exported_path.exists() else 0
        export_time = (end_time - start_time).total_seconds()
        
        return ExportResponse(
            success=True,
            file_path=str(exported_path),
            format=request.format,
            file_size=file_size,
            export_time=export_time,
            message=f"Successfully exported to {request.format} format",
            metadata={
                "export_id": export_id,
                "filename": filename,
                "options": request.options
            }
        )
        
    except Exception as e:
        # Update job status on error
        if export_id in export_jobs:
            export_jobs[export_id].update({
                "status": "failed",
                "error_message": str(e)
            })
        
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(e)}"
        )

@router.get("/export/{export_id}/status", response_model=ExportStatusResponse)
async def get_export_status(export_id: str):
    """
    Get export job status.
    
    Args:
        export_id: Unique export job ID
        
    Returns:
        ExportStatusResponse with current status
    """
    if export_id not in export_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Export job not found: {export_id}"
        )
    
    job = export_jobs[export_id]
    
    return ExportStatusResponse(
        export_id=export_id,
        status=job["status"],
        progress=job["progress"],
        format=job["format"],
        created_at=job["created_at"],
        completed_at=job.get("completed_at"),
        file_path=job.get("file_path"),
        error_message=job.get("error_message")
    )

@router.get("/export/{export_id}/download")
async def download_export_file(export_id: str):
    """
    Download exported file.
    
    Args:
        export_id: Unique export job ID
        
    Returns:
        FileResponse with exported file
    """
    if export_id not in export_jobs:
        raise HTTPException(
            status_code=404,
            detail=f"Export job not found: {export_id}"
        )
    
    job = export_jobs[export_id]
    
    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Export not completed. Status: {job['status']}"
        )
    
    file_path = job.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="Exported file not found"
        )
    
    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/octet-stream"
    )

@router.get("/formats", response_model=SupportedFormatsResponse)
async def get_supported_formats():
    """
    Get list of supported export formats.
    
    Returns:
        SupportedFormatsResponse with available formats
    """
    formats = [
        {
            "format": ExportFormat.IFC_LITE,
            "name": "IFC-Lite",
            "description": "Industry Foundation Classes (IFC) for BIM interoperability",
            "extensions": [".ifc"],
            "category": "bim"
        },
        {
            "format": ExportFormat.GLTF,
            "name": "glTF",
            "description": "3D visualization format for web and mobile",
            "extensions": [".gltf", ".glb"],
            "category": "visualization"
        },
        {
            "format": ExportFormat.ASCII_BIM,
            "name": "ASCII-BIM",
            "description": "Text-based BIM format for roundtrip conversion",
            "extensions": [".bim"],
            "category": "bim"
        },
        {
            "format": ExportFormat.EXCEL,
            "name": "Excel",
            "description": "Microsoft Excel format for data analysis",
            "extensions": [".xlsx"],
            "category": "analytics"
        },
        {
            "format": ExportFormat.PARQUET,
            "name": "Parquet",
            "description": "Columnar storage format for big data analytics",
            "extensions": [".parquet"],
            "category": "analytics"
        },
        {
            "format": ExportFormat.GEOJSON,
            "name": "GeoJSON",
            "description": "Geographic data format for GIS applications",
            "extensions": [".geojson"],
            "category": "gis"
        }
    ]
    
    return SupportedFormatsResponse(
        formats=formats,
        total_formats=len(formats)
    )

@router.post("/validate")
async def validate_export_data(data: Dict[str, Any]):
    """
    Validate BIM data for export.
    
    Args:
        data: BIM data to validate
        
    Returns:
        Validation result
    """
    try:
        # Basic validation (can be expanded)
        required_fields = ["elements", "metadata"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return {
                "valid": False,
                "errors": [f"Missing required field: {field}" for field in missing_fields],
                "warnings": []
            }
        
        # Check data structure
        warnings = []
        if "elements" in data and not isinstance(data["elements"], list):
            warnings.append("Elements should be a list")
        
        if "metadata" in data and not isinstance(data["metadata"], dict):
            warnings.append("Metadata should be a dictionary")
        
        return {
            "valid": True,
            "errors": [],
            "warnings": warnings
        }
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"],
            "warnings": []
        }

@router.get("/health")
async def export_service_health():
    """
    Health check for export service.
    
    Returns:
        Service health status
    """
    return {
        "status": "healthy",
        "service": "Advanced Export & Interoperability",
        "timestamp": datetime.now().isoformat(),
        "supported_formats": [
            ExportFormat.IFC_LITE,
            ExportFormat.GLTF,
            ExportFormat.ASCII_BIM,
            ExportFormat.EXCEL,
            ExportFormat.PARQUET,
            ExportFormat.GEOJSON
        ],
        "active_jobs": len([job for job in export_jobs.values() if job["status"] == "processing"])
    } 