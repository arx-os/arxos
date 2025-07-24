"""
SVGX Engine - Export API

This module provides FastAPI endpoints for the advanced export system,
enabling web-based access to all export functionalities including IFC, GLTF, DXF, STEP, IGES, and Parasolid formats.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from pydantic.json import pydantic_encoder

from ..services.export.advanced_export_system import (
    AdvancedExportSystem,
    ExportFormat,
    ExportQuality,
    ExportConfig,
    ExportResult,
    create_advanced_export_system,
    create_export_config
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SVGX Engine Export API",
    description="Advanced export system for professional CAD formats",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize export system
export_system = create_advanced_export_system()

# Pydantic models for API requests/responses
class ExportDataRequest(BaseModel):
    data: Dict[str, Any] = Field(..., description="Data to export")
    output_path: str = Field(..., description="Output file path")
    format: ExportFormat = Field(..., description="Export format")
    config: Optional[ExportConfig] = Field(None, description="Export configuration")

class ExportDataResponse(BaseModel):
    success: bool = Field(..., description="Export success status")
    output_path: str = Field(..., description="Output file path")
    file_size: int = Field(..., description="File size in bytes")
    export_time: float = Field(..., description="Export time in seconds")
    metadata: Dict[str, Any] = Field(..., description="Export metadata")
    error: Optional[str] = Field(None, description="Error message if failed")

class BatchExportRequest(BaseModel):
    exports: List[ExportDataRequest] = Field(..., description="List of export requests")

class BatchExportResponse(BaseModel):
    results: List[ExportDataResponse] = Field(..., description="Export results")

class ValidateExportRequest(BaseModel):
    data: Dict[str, Any] = Field(..., description="Data to validate")
    format: ExportFormat = Field(..., description="Export format")

class ValidateExportResponse(BaseModel):
    valid: bool = Field(..., description="Validation result")
    message: str = Field(..., description="Validation message")

class ExportProgressResponse(BaseModel):
    job_id: str = Field(..., description="Job ID")
    status: str = Field(..., description="Job status")
    progress: float = Field(..., description="Progress percentage")
    message: str = Field(..., description="Progress message")
    start_time: float = Field(..., description="Start time timestamp")
    end_time: Optional[float] = Field(None, description="End time timestamp")
    metadata: Dict[str, Any] = Field(..., description="Job metadata")

class ExportStatisticsResponse(BaseModel):
    total_exports: int = Field(..., description="Total number of exports")
    successful_exports: int = Field(..., description="Number of successful exports")
    failed_exports: int = Field(..., description="Number of failed exports")
    average_export_time: float = Field(..., description="Average export time")
    format_usage: Dict[str, int] = Field(..., description="Format usage statistics")
    recent_exports: List[ExportDataResponse] = Field(..., description="Recent exports")

# Background job storage
export_jobs: Dict[str, Dict[str, Any]] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize export system on startup."""
    logger.info("Export API starting up...")
    global export_system
    export_system = create_advanced_export_system()
    logger.info("Export API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Export API shutting down...")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "export-api"}

# Export data endpoint
@app.post("/export/data", response_model=ExportDataResponse)
async def export_data(request: ExportDataRequest):
    """Export data to the specified format."""
    try:
        start_time = time.time()
        
        # Create export config if not provided
        if request.config is None:
            request.config = create_export_config(
                format=request.format,
                quality=ExportQuality.MEDIUM
            )
        
        # Perform export
        result = export_system.export_data(
            data=request.data,
            output_path=request.output_path,
            format=request.format,
            config=request.config
        )
        
        export_time = time.time() - start_time
        
        return ExportDataResponse(
            success=result.success,
            output_path=str(result.output_path),
            file_size=result.file_size,
            export_time=export_time,
            metadata=result.metadata,
            error=result.error if not result.success else None
        )
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# IFC export endpoint
@app.post("/export/ifc", response_model=ExportDataResponse)
async def export_to_ifc(request: ExportDataRequest):
    """Export data to IFC format."""
    request.format = ExportFormat.IFC
    return await export_data(request)

# GLTF export endpoint
@app.post("/export/gltf", response_model=ExportDataResponse)
async def export_to_gltf(request: ExportDataRequest):
    """Export data to GLTF format."""
    request.format = ExportFormat.GLTF
    return await export_data(request)

# DXF export endpoint
@app.post("/export/dxf", response_model=ExportDataResponse)
async def export_to_dxf(request: ExportDataRequest):
    """Export data to DXF format."""
    request.format = ExportFormat.DXF
    return await export_data(request)

# STEP export endpoint
@app.post("/export/step", response_model=ExportDataResponse)
async def export_to_step(request: ExportDataRequest):
    """Export data to STEP format."""
    request.format = ExportFormat.STEP
    return await export_data(request)

# IGES export endpoint
@app.post("/export/iges", response_model=ExportDataResponse)
async def export_to_iges(request: ExportDataRequest):
    """Export data to IGES format."""
    request.format = ExportFormat.IGES
    return await export_data(request)

# Parasolid export endpoint
@app.post("/export/parasolid", response_model=ExportDataResponse)
async def export_to_parasolid(request: ExportDataRequest):
    """Export data to Parasolid format."""
    request.format = ExportFormat.PARASOLID
    return await export_data(request)

# Get supported formats endpoint
@app.get("/export/formats")
async def get_supported_formats():
    """Get list of supported export formats."""
    formats = [
        ExportFormat.IFC,
        ExportFormat.GLTF,
        ExportFormat.DXF,
        ExportFormat.STEP,
        ExportFormat.IGES,
        ExportFormat.PARASOLID,
        ExportFormat.EXCEL,
        ExportFormat.PARQUET,
        ExportFormat.GEOJSON
    ]
    return {"formats": [format.value for format in formats]}

# Get export history endpoint
@app.get("/export/history")
async def get_export_history(limit: int = 50):
    """Get export history."""
    try:
        history = export_system.export_history[-limit:] if export_system.export_history else []
        
        responses = []
        for result in history:
            response = ExportDataResponse(
                success=result.success,
                output_path=str(result.output_path),
                file_size=result.file_size,
                export_time=result.export_time,
                metadata=result.metadata,
                error=result.error if not result.success else None
            )
            responses.append(response)
        
        return {"history": responses}
        
    except Exception as e:
        logger.error(f"Failed to get export history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get export history: {str(e)}")

# Get export statistics endpoint
@app.get("/export/statistics", response_model=ExportStatisticsResponse)
async def get_export_statistics():
    """Get export statistics."""
    try:
        history = export_system.export_history
        
        total_exports = len(history)
        successful_exports = sum(1 for result in history if result.success)
        failed_exports = total_exports - successful_exports
        
        if history:
            average_export_time = sum(result.export_time for result in history) / len(history)
        else:
            average_export_time = 0.0
        
        # Calculate format usage
        format_usage = {}
        for result in history:
            format_name = result.metadata.get("format", "unknown")
            format_usage[format_name] = format_usage.get(format_name, 0) + 1
        
        # Get recent exports
        recent_exports = []
        for result in history[-10:]:  # Last 10 exports
            response = ExportDataResponse(
                success=result.success,
                output_path=str(result.output_path),
                file_size=result.file_size,
                export_time=result.export_time,
                metadata=result.metadata,
                error=result.error if not result.success else None
            )
            recent_exports.append(response)
        
        return ExportStatisticsResponse(
            total_exports=total_exports,
            successful_exports=successful_exports,
            failed_exports=failed_exports,
            average_export_time=average_export_time,
            format_usage=format_usage,
            recent_exports=recent_exports
        )
        
    except Exception as e:
        logger.error(f"Failed to get export statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get export statistics: {str(e)}")

# Validate export data endpoint
@app.post("/export/validate", response_model=ValidateExportResponse)
async def validate_export_data(request: ValidateExportRequest):
    """Validate export data."""
    try:
        # Basic validation
        if not request.data:
            return ValidateExportResponse(
                valid=False,
                message="No data provided"
            )
        
        # Check if data has required fields for the format
        if request.format == ExportFormat.IFC:
            if "elements" not in request.data:
                return ValidateExportResponse(
                    valid=False,
                    message="IFC export requires 'elements' field"
                )
        elif request.format == ExportFormat.GLTF:
            if "elements" not in request.data:
                return ValidateExportResponse(
                    valid=False,
                    message="GLTF export requires 'elements' field"
                )
        elif request.format == ExportFormat.DXF:
            if "elements" not in request.data:
                return ValidateExportResponse(
                    valid=False,
                    message="DXF export requires 'elements' field"
                )
        elif request.format == ExportFormat.STEP:
            if "elements" not in request.data:
                return ValidateExportResponse(
                    valid=False,
                    message="STEP export requires 'elements' field"
                )
        elif request.format == ExportFormat.IGES:
            if "elements" not in request.data:
                return ValidateExportResponse(
                    valid=False,
                    message="IGES export requires 'elements' field"
                )
        
        return ValidateExportResponse(
            valid=True,
            message="Data validation passed"
        )
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return ValidateExportResponse(
            valid=False,
            message=f"Validation failed: {str(e)}"
        )

# Batch export endpoint
@app.post("/export/batch", response_model=BatchExportResponse)
async def batch_export(request: BatchExportRequest):
    """Perform batch export operations."""
    try:
        results = []
        
        for export_request in request.exports:
            try:
                # Create export config if not provided
                if export_request.config is None:
                    export_request.config = create_export_config(
                        format=export_request.format,
                        quality=ExportQuality.MEDIUM
                    )
                
                # Perform export
                result = export_system.export_data(
                    data=export_request.data,
                    output_path=export_request.output_path,
                    format=export_request.format,
                    config=export_request.config
                )
                
                response = ExportDataResponse(
                    success=result.success,
                    output_path=str(result.output_path),
                    file_size=result.file_size,
                    export_time=result.export_time,
                    metadata=result.metadata,
                    error=result.error if not result.success else None
                )
                results.append(response)
                
            except Exception as e:
                logger.error(f"Batch export item failed: {e}")
                response = ExportDataResponse(
                    success=False,
                    output_path=export_request.output_path,
                    file_size=0,
                    export_time=0.0,
                    metadata={},
                    error=str(e)
                )
                results.append(response)
        
        return BatchExportResponse(results=results)
        
    except Exception as e:
        logger.error(f"Batch export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch export failed: {str(e)}")

# Background export job
async def background_export_job(job_id: str, request: ExportDataRequest):
    """Background export job."""
    try:
        export_jobs[job_id]["status"] = "running"
        export_jobs[job_id]["progress"] = 0.0
        export_jobs[job_id]["start_time"] = time.time()
        
        # Simulate progress updates
        for i in range(1, 11):
            await asyncio.sleep(0.1)  # Simulate work
            export_jobs[job_id]["progress"] = i * 10.0
        
        # Perform actual export
        if request.config is None:
            request.config = create_export_config(
                format=request.format,
                quality=ExportQuality.MEDIUM
            )
        
        result = export_system.export_data(
            data=request.data,
            output_path=request.output_path,
            format=request.format,
            config=request.config
        )
        
        export_jobs[job_id]["status"] = "completed"
        export_jobs[job_id]["progress"] = 100.0
        export_jobs[job_id]["end_time"] = time.time()
        export_jobs[job_id]["result"] = result
        
    except Exception as e:
        logger.error(f"Background export job failed: {e}")
        export_jobs[job_id]["status"] = "failed"
        export_jobs[job_id]["error"] = str(e)
        export_jobs[job_id]["end_time"] = time.time()

# Start background export job
@app.post("/export/start-job")
async def start_export_job(request: ExportDataRequest, background_tasks: BackgroundTasks):
    """Start a background export job."""
    try:
        job_id = str(uuid.uuid4())
        
        # Initialize job
        export_jobs[job_id] = {
            "status": "queued",
            "progress": 0.0,
            "start_time": None,
            "end_time": None,
            "result": None,
            "error": None
        }
        
        # Start background task
        background_tasks.add_task(background_export_job, job_id, request)
        
        return {"job_id": job_id, "status": "queued"}
        
    except Exception as e:
        logger.error(f"Failed to start export job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start export job: {str(e)}")

# Get export progress endpoint
@app.get("/export/progress/{job_id}")
async def get_export_progress(job_id: str):
    """Get export progress for a specific job."""
    try:
        if job_id not in export_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = export_jobs[job_id]
        
        return ExportProgressResponse(
            job_id=job_id,
            status=job["status"],
            progress=job["progress"],
            message=f"Export {job['status']}",
            start_time=job["start_time"] or 0.0,
            end_time=job["end_time"],
            metadata=job.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get export progress: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get export progress: {str(e)}")

# Cancel export job endpoint
@app.post("/export/cancel/{job_id}")
async def cancel_export_job(job_id: str):
    """Cancel an export job."""
    try:
        if job_id not in export_jobs:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = export_jobs[job_id]
        if job["status"] in ["completed", "failed", "cancelled"]:
            raise HTTPException(status_code=400, detail="Job cannot be cancelled")
        
        job["status"] = "cancelled"
        job["end_time"] = time.time()
        
        return {"message": "Export job cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel export job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel export job: {str(e)}")

# Download export file endpoint
@app.get("/export/download/{filename}")
async def download_export_file(filename: str):
    """Download an exported file."""
    try:
        # Security check - prevent path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Construct file path
        file_path = Path("exports") / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Determine content type based on file extension
        content_type = "application/octet-stream"
        if filename.endswith(".ifc"):
            content_type = "application/ifc"
        elif filename.endswith((".gltf", ".glb")):
            content_type = "model/gltf-binary"
        elif filename.endswith(".dxf"):
            content_type = "application/dxf"
        elif filename.endswith((".step", ".stp")):
            content_type = "application/step"
        elif filename.endswith((".iges", ".igs")):
            content_type = "application/iges"
        elif filename.endswith((".x_t", ".xmt_txt")):
            content_type = "application/parasolid"
        elif filename.endswith((".xlsx", ".xls")):
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif filename.endswith(".parquet"):
            content_type = "application/octet-stream"
        elif filename.endswith(".geojson"):
            content_type = "application/geo+json"
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=content_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download file: {str(e)}")

# Upload file for export endpoint
@app.post("/export/upload")
async def upload_file_for_export(file: UploadFile = File(...)):
    """Upload a file for export processing."""
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "filename": file.filename,
            "file_path": str(file_path),
            "file_size": len(content),
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

# Get export system info endpoint
@app.get("/export/info")
async def get_export_system_info():
    """Get export system information."""
    try:
        return {
            "system": "SVGX Engine Export System",
            "version": "1.0.0",
            "supported_formats": [
                ExportFormat.IFC.value,
                ExportFormat.GLTF.value,
                ExportFormat.DXF.value,
                ExportFormat.STEP.value,
                ExportFormat.IGES.value,
                ExportFormat.PARASOLID.value,
                ExportFormat.EXCEL.value,
                ExportFormat.PARQUET.value,
                ExportFormat.GEOJSON.value
            ],
            "quality_levels": [
                ExportQuality.LOW.value,
                ExportQuality.MEDIUM.value,
                ExportQuality.HIGH.value
            ],
            "active_jobs": len([job for job in export_jobs.values() if job["status"] == "running"]),
            "total_jobs": len(export_jobs)
        }
        
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system info: {str(e)}")

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    
    # Create necessary directories
    Path("exports").mkdir(exist_ok=True)
    Path("uploads").mkdir(exist_ok=True)
    
    # Run the application
    uvicorn.run(
        "export_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    ) 