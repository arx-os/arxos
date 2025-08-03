"""
PDF Analysis API Routes

This module contains the FastAPI routes for PDF analysis operations.
The routes interact with Application Layer use cases and DTOs.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from domain.value_objects import TaskId, UserId, TaskStatus
from domain.exceptions import (
    PDFAnalysisNotFoundError, InvalidPDFAnalysisError, 
    InvalidTaskStatusError, RepositoryError
)
from application.use_cases.pdf_analysis_use_cases import (
    CreatePDFAnalysisUseCase, GetPDFAnalysisUseCase,
    StartPDFAnalysisUseCase, CompletePDFAnalysisUseCase,
    FailPDFAnalysisUseCase, CancelPDFAnalysisUseCase,
    GetPDFAnalysisStatusUseCase, GetPDFAnalysisResultUseCase,
    ListPDFAnalysesUseCase, GetPDFAnalysisStatisticsUseCase
)
from application.dto.pdf_analysis_dto import (
    CreatePDFAnalysisRequest, CreatePDFAnalysisResponse,
    GetPDFAnalysisRequest, GetPDFAnalysisResponse,
    StartPDFAnalysisRequest, StartPDFAnalysisResponse,
    CompletePDFAnalysisRequest, CompletePDFAnalysisResponse,
    FailPDFAnalysisRequest, FailPDFAnalysisResponse,
    CancelPDFAnalysisRequest, CancelPDFAnalysisResponse,
    GetPDFAnalysisStatusRequest, GetPDFAnalysisStatusResponse,
    GetPDFAnalysisResultRequest, GetPDFAnalysisResultResponse,
    ListPDFAnalysesRequest, ListPDFAnalysesResponse,
    GetPDFAnalysisStatisticsRequest, GetPDFAnalysisStatisticsResponse
)
from application.services.pdf_analysis_orchestrator import PDFAnalysisOrchestrator
from infrastructure.repositories.postgresql_pdf_analysis_repository import PostgreSQLPDFAnalysisRepository
from infrastructure.services.gus_service import GUSService
from infrastructure.services.file_storage_service import FileStorageService
from infrastructure.database.connection_manager import DatabaseConnectionManager


# Pydantic models for API requests/responses
class PDFAnalysisCreateRequest(BaseModel):
    """Request model for creating PDF analysis."""
    include_cost_estimation: bool = Field(default=True, description="Include cost estimation")
    include_timeline: bool = Field(default=True, description="Include timeline")
    include_quantities: bool = Field(default=True, description="Include quantities")
    requirements: Dict[str, Any] = Field(default_factory=dict, description="Additional requirements")


class PDFAnalysisResponse(BaseModel):
    """Response model for PDF analysis."""
    task_id: str
    user_id: str
    filename: str
    status: str
    confidence: Optional[float] = None
    systems_found: Optional[List[str]] = None
    total_components: Optional[int] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str
    success: bool
    message: str


class PDFAnalysisStatusResponse(BaseModel):
    """Response model for PDF analysis status."""
    task_id: str
    status: str
    created_at: str
    updated_at: str
    success: bool
    message: str


class PDFAnalysisResultResponse(BaseModel):
    """Response model for PDF analysis result."""
    task_id: str
    status: str
    confidence: Optional[float] = None
    systems_found: Optional[List[str]] = None
    total_components: Optional[int] = None
    processing_time: Optional[float] = None
    project_info: Optional[Dict[str, Any]] = None
    systems: Optional[Dict[str, Any]] = None
    quantities: Optional[Dict[str, Any]] = None
    cost_estimates: Optional[Dict[str, float]] = None
    timeline: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    success: bool
    message: str


class PDFAnalysisListResponse(BaseModel):
    """Response model for PDF analysis list."""
    analyses: List[Dict[str, Any]]
    total_count: int
    success: bool
    message: str


class PDFAnalysisStatisticsResponse(BaseModel):
    """Response model for PDF analysis statistics."""
    statistics: Dict[str, Any]
    success: bool
    message: str


class PDFAnalysisExportRequest(BaseModel):
    """Request model for exporting PDF analysis."""
    export_format: str = Field(..., description="Export format (json, csv, pdf, excel)")
    include_metadata: bool = Field(default=True, description="Include metadata")


# Dependency injection
def get_pdf_analysis_orchestrator() -> PDFAnalysisOrchestrator:
    """Get PDF analysis orchestrator instance."""
    # Initialize dependencies
    from infrastructure.unit_of_work import SQLAlchemyUnitOfWork
    from infrastructure.database.connection_manager import DatabaseConnectionManager
    from infrastructure.repository_factory import SQLAlchemyRepositoryFactory
    from sqlalchemy.orm import sessionmaker
    
    # Create session factory
    connection_manager = DatabaseConnectionManager()
    session_factory = sessionmaker(bind=connection_manager.get_engine())
    
    # Create Unit of Work
    unit_of_work = SQLAlchemyUnitOfWork(session_factory)
    
    # Initialize services
    gus_service = GUSService("http://localhost:8001")  # GUS service URL
    file_storage_service = FileStorageService("/tmp/arxos/pdf_analysis")
    
    return PDFAnalysisOrchestrator(unit_of_work, gus_service, file_storage_service)


# Router
pdf_router = APIRouter(prefix="/api/v1/pdf-analysis", tags=["PDF Analysis"])
logger = logging.getLogger(__name__)


@pdf_router.post("/upload", response_model=PDFAnalysisResponse)
async def upload_pdf_for_analysis(
    file: UploadFile = File(...),
    request: PDFAnalysisCreateRequest = Depends(),
    orchestrator: PDFAnalysisOrchestrator = Depends(get_pdf_analysis_orchestrator)
):
    """
    Upload a PDF file for analysis.
    
    Args:
        file: PDF file to upload
        request: Analysis requirements
        orchestrator: PDF analysis orchestrator
        
    Returns:
        PDF analysis response with task ID
    """
    try:
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Read file content
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Create analysis (using orchestrator which handles use cases)
        response = await orchestrator.create_pdf_analysis(
            user_id=UserId("default_user"),  # TODO: Get from authentication
            filename=file.filename,
            file_content=file_content,
            include_cost_estimation=request.include_cost_estimation,
            include_timeline=request.include_timeline,
            include_quantities=request.include_quantities,
            requirements=request.requirements
        )
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        
        # Convert to API response
        return PDFAnalysisResponse(
            task_id=str(response.task_id),
            user_id=str(response.user_id),
            filename=str(response.filename),
            status=str(response.status),
            created_at=response.created_at.isoformat(),
            updated_at=response.created_at.isoformat(),
            success=response.success,
            message=response.message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@pdf_router.post("/{task_id}/start", response_model=PDFAnalysisStatusResponse)
async def start_pdf_analysis(
    task_id: str,
    orchestrator: PDFAnalysisOrchestrator = Depends(get_pdf_analysis_orchestrator)
):
    """
    Start PDF analysis processing.
    
    Args:
        task_id: Task ID to start
        orchestrator: PDF analysis orchestrator
        
    Returns:
        Status response
    """
    try:
        response = await orchestrator.start_pdf_analysis(TaskId(task_id))
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        
        return PDFAnalysisStatusResponse(
            task_id=str(response.task_id),
            status=str(response.status),
            created_at=response.started_at.isoformat(),
            updated_at=response.started_at.isoformat(),
            success=response.success,
            message=response.message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting PDF analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@pdf_router.get("/{task_id}/status", response_model=PDFAnalysisStatusResponse)
async def get_pdf_analysis_status(
    task_id: str,
    orchestrator: PDFAnalysisOrchestrator = Depends(get_pdf_analysis_orchestrator)
):
    """
    Get PDF analysis status.
    
    Args:
        task_id: Task ID to check
        orchestrator: PDF analysis orchestrator
        
    Returns:
        Status response
    """
    try:
        response = await orchestrator.get_pdf_analysis_status(TaskId(task_id))
        
        if not response.success:
            raise HTTPException(status_code=404, detail=response.message)
        
        return PDFAnalysisStatusResponse(
            task_id=str(response.task_id),
            status=str(response.status),
            created_at=response.created_at.isoformat(),
            updated_at=response.updated_at.isoformat(),
            success=response.success,
            message=response.message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PDF analysis status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@pdf_router.get("/{task_id}/result", response_model=PDFAnalysisResultResponse)
async def get_pdf_analysis_result(
    task_id: str,
    orchestrator: PDFAnalysisOrchestrator = Depends(get_pdf_analysis_orchestrator)
):
    """
    Get PDF analysis result.
    
    Args:
        task_id: Task ID to retrieve result for
        orchestrator: PDF analysis orchestrator
        
    Returns:
        Analysis result response
    """
    try:
        response = await orchestrator.get_pdf_analysis_result(TaskId(task_id))
        
        if not response.success:
            raise HTTPException(status_code=404, detail=response.message)
        
        # Extract analysis result data
        analysis_result = response.analysis_result
        project_info = analysis_result.project_info if analysis_result else None
        systems = analysis_result.systems if analysis_result else None
        quantities = analysis_result.quantities if analysis_result else None
        cost_estimates = analysis_result.cost_estimates if analysis_result else None
        timeline = analysis_result.timeline if analysis_result else None
        metadata = analysis_result.metadata if analysis_result else None
        
        return PDFAnalysisResultResponse(
            task_id=str(response.task_id),
            status=str(response.status),
            confidence=float(response.confidence) if response.confidence else None,
            systems_found=response.systems_found,
            total_components=response.total_components,
            processing_time=response.processing_time,
            project_info=project_info,
            systems=systems,
            quantities=quantities,
            cost_estimates=cost_estimates,
            timeline=timeline,
            metadata=metadata,
            success=response.success,
            message=response.message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PDF analysis result: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@pdf_router.post("/{task_id}/cancel", response_model=PDFAnalysisStatusResponse)
async def cancel_pdf_analysis(
    task_id: str,
    orchestrator: PDFAnalysisOrchestrator = Depends(get_pdf_analysis_orchestrator)
):
    """
    Cancel PDF analysis.
    
    Args:
        task_id: Task ID to cancel
        orchestrator: PDF analysis orchestrator
        
    Returns:
        Status response
    """
    try:
        response = await orchestrator.cancel_pdf_analysis(TaskId(task_id))
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        
        return PDFAnalysisStatusResponse(
            task_id=str(response.task_id),
            status=str(response.status),
            created_at=response.cancelled_at.isoformat(),
            updated_at=response.cancelled_at.isoformat(),
            success=response.success,
            message=response.message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling PDF analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@pdf_router.get("/list", response_model=PDFAnalysisListResponse)
async def list_pdf_analyses(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    orchestrator: PDFAnalysisOrchestrator = Depends(get_pdf_analysis_orchestrator)
):
    """
    List PDF analyses with filters.
    
    Args:
        user_id: Optional user ID filter
        status: Optional status filter
        limit: Maximum number of results
        orchestrator: PDF analysis orchestrator
        
    Returns:
        List of PDF analyses
    """
    try:
        # Convert status string to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = TaskStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        response = await orchestrator.list_pdf_analyses(
            user_id=UserId(user_id) if user_id else None,
            status=status_enum,
            limit=limit
        )
        
        return PDFAnalysisListResponse(
            analyses=response.analyses,
            total_count=response.total_count,
            success=response.success,
            message=response.message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing PDF analyses: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@pdf_router.get("/statistics", response_model=PDFAnalysisStatisticsResponse)
async def get_pdf_analysis_statistics(
    user_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    orchestrator: PDFAnalysisOrchestrator = Depends(get_pdf_analysis_orchestrator)
):
    """
    Get PDF analysis statistics.
    
    Args:
        user_id: Optional user ID filter
        date_from: Optional start date
        date_to: Optional end date
        orchestrator: PDF analysis orchestrator
        
    Returns:
        Statistics response
    """
    try:
        response = await orchestrator.get_pdf_analysis_statistics(
            user_id=UserId(user_id) if user_id else None,
            date_from=date_from,
            date_to=date_to
        )
        
        return PDFAnalysisStatisticsResponse(
            statistics=response.statistics,
            success=response.success,
            message=response.message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PDF analysis statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@pdf_router.get("/{task_id}/export")
async def export_pdf_analysis(
    task_id: str,
    export_format: str = "json",
    include_metadata: bool = True,
    orchestrator: PDFAnalysisOrchestrator = Depends(get_pdf_analysis_orchestrator)
):
    """
    Export PDF analysis result.
    
    Args:
        task_id: Task ID to export
        export_format: Export format (json, csv, pdf, excel)
        include_metadata: Whether to include metadata
        orchestrator: PDF analysis orchestrator
        
    Returns:
        Exported file as streaming response
    """
    try:
        # Validate export format
        valid_formats = ["json", "csv", "pdf", "excel"]
        if export_format not in valid_formats:
            raise HTTPException(status_code=400, detail=f"Invalid export format. Must be one of: {valid_formats}")
        
        # Get file storage service from orchestrator
        file_storage_service = orchestrator.file_storage_service
        
        # Export file
        content, filename = await file_storage_service.export_analysis_result(
            task_id=task_id,
            export_format=export_format,
            include_metadata=include_metadata
        )
        
        # Return as streaming response
        return StreamingResponse(
            iter([content]),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting PDF analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@pdf_router.post("/{task_id}/validate")
async def validate_pdf_analysis(
    task_id: str,
    orchestrator: PDFAnalysisOrchestrator = Depends(get_pdf_analysis_orchestrator)
):
    """
    Validate PDF analysis result.
    
    Args:
        task_id: Task ID to validate
        orchestrator: PDF analysis orchestrator
        
    Returns:
        Validation response
    """
    try:
        # Get GUS service from orchestrator
        gus_service = orchestrator.gus_service
        
        # Validate analysis
        validation_result = await gus_service.validate_analysis(task_id)
        
        return {
            "task_id": task_id,
            "validation_result": validation_result,
            "success": True,
            "message": "Analysis validation completed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating PDF analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@pdf_router.delete("/{task_id}")
async def delete_pdf_analysis(
    task_id: str,
    orchestrator: PDFAnalysisOrchestrator = Depends(get_pdf_analysis_orchestrator)
):
    """
    Delete PDF analysis and associated files.
    
    Args:
        task_id: Task ID to delete
        orchestrator: PDF analysis orchestrator
        
    Returns:
        Deletion response
    """
    try:
        # Get repository from orchestrator
        repository = orchestrator.repository
        
        # Delete from repository
        deleted = repository.delete(TaskId(task_id))
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"PDF analysis {task_id} not found")
        
        # Clean up files
        file_storage_service = orchestrator.file_storage_service
        await file_storage_service.cleanup_task_files(task_id)
        
        return {
            "task_id": task_id,
            "success": True,
            "message": "PDF analysis deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting PDF analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@pdf_router.get("/health")
async def pdf_analysis_health_check():
    """
    Health check for PDF analysis service.
    
    Returns:
        Health status
    """
    try:
        # Basic health check
        return {
            "service": "PDF Analysis API",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy") 