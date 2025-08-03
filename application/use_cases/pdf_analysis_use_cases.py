"""
PDF Analysis Use Cases

This module contains the application use cases for PDF analysis operations.
Use cases orchestrate domain logic and coordinate between layers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from domain.entities.pdf_analysis import PDFAnalysis
from domain.value_objects import (
    TaskId, UserId, TaskStatus, ConfidenceScore, 
    FileName, FilePath, AnalysisResult, AnalysisRequirements
)
from domain.repositories.pdf_analysis_repository import PDFAnalysisRepository
from domain.exceptions import (
    InvalidPDFAnalysisError, InvalidTaskStatusError,
    PDFAnalysisNotFoundError, PDFAnalysisAlreadyExistsError
)
from application.dto.pdf_analysis_dto import (
    CreatePDFAnalysisRequest, CreatePDFAnalysisResponse,
    GetPDFAnalysisRequest, GetPDFAnalysisResponse,
    UpdatePDFAnalysisRequest, UpdatePDFAnalysisResponse,
    DeletePDFAnalysisRequest, DeletePDFAnalysisResponse,
    StartPDFAnalysisRequest, StartPDFAnalysisResponse,
    CompletePDFAnalysisRequest, CompletePDFAnalysisResponse,
    FailPDFAnalysisRequest, FailPDFAnalysisResponse,
    CancelPDFAnalysisRequest, CancelPDFAnalysisResponse,
    GetPDFAnalysisStatusRequest, GetPDFAnalysisStatusResponse,
    GetPDFAnalysisResultRequest, GetPDFAnalysisResultResponse,
    ExportPDFAnalysisRequest, ExportPDFAnalysisResponse,
    ValidatePDFAnalysisRequest, ValidatePDFAnalysisResponse,
    ListPDFAnalysesRequest, ListPDFAnalysesResponse,
    GetPDFAnalysisStatisticsRequest, GetPDFAnalysisStatisticsResponse
)
from application.services.pdf_analysis_orchestrator import PDFAnalysisOrchestrator


class CreatePDFAnalysisUseCase:
    """Use case for creating a new PDF analysis."""
    
    def __init__(self, repository: PDFAnalysisRepository):
    """
    Perform __init__ operation

Args:
        repository: Description of repository

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.repository = repository
    
    def execute(self, request: CreatePDFAnalysisRequest) -> CreatePDFAnalysisResponse:
        """
        Execute the create PDF analysis use case.
        
        Args:
            request: The create request containing analysis details
            
        Returns:
            Response with created analysis details
            
        Raises:
            InvalidPDFAnalysisError: If request data is invalid
            PDFAnalysisAlreadyExistsError: If analysis already exists
        """
        try:
            # Validate request
            self._validate_create_request(request)
            
            # Check if analysis already exists
            if self.repository.exists(request.task_id):
                raise PDFAnalysisAlreadyExistsError(f"Analysis with task ID {request.task_id} already exists")
            
            # Create domain entity
            pdf_analysis = PDFAnalysis(
                task_id=request.task_id,
                user_id=request.user_id,
                filename=request.filename,
                file_path=request.file_path,
                status=TaskStatus.PENDING,
                include_cost_estimation=request.include_cost_estimation,
                include_timeline=request.include_timeline,
                include_quantities=request.include_quantities,
                requirements=request.requirements
            )
            
            # Save to repository
            created_analysis = self.repository.create(pdf_analysis)
            
            # Return response
            return CreatePDFAnalysisResponse(
                task_id=created_analysis.task_id,
                user_id=created_analysis.user_id,
                filename=created_analysis.filename,
                status=created_analysis.status,
                created_at=created_analysis.created_at,
                success=True,
                message="PDF analysis created successfully"
            )
            
        except Exception as e:
            return CreatePDFAnalysisResponse(
                task_id=request.task_id,
                user_id=request.user_id,
                filename=request.filename,
                status=TaskStatus.FAILED,
                created_at=datetime.utcnow(),
                success=False,
                message=str(e)
            )
    
    def _validate_create_request(self, request: CreatePDFAnalysisRequest) -> None:
        """Validate create request data."""
        if not request.task_id:
            raise InvalidPDFAnalysisError("Task ID is required")
        if not request.user_id:
            raise InvalidPDFAnalysisError("User ID is required")
        if not request.filename:
            raise InvalidPDFAnalysisError("Filename is required")
        if not request.file_path:
            raise InvalidPDFAnalysisError("File path is required")
        if not request.filename.is_pdf():
            raise InvalidPDFAnalysisError("File must be a PDF")


class GetPDFAnalysisUseCase:
    """
    Perform __init__ operation

Args:
        repository: Description of repository

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Use case for retrieving a PDF analysis."""
    
    def __init__(self, repository: PDFAnalysisRepository):
        self.repository = repository
    
    def execute(self, request: GetPDFAnalysisRequest) -> GetPDFAnalysisResponse:
        """
        Execute the get PDF analysis use case.
        
        Args:
            request: The get request containing task ID
            
        Returns:
            Response with analysis details
            
        Raises:
            PDFAnalysisNotFoundError: If analysis not found
        """
        try:
            # Get from repository
            pdf_analysis = self.repository.get_by_id(request.task_id)
            
            if not pdf_analysis:
                raise PDFAnalysisNotFoundError(f"Analysis with task ID {request.task_id} not found")
            
            # Return response
            return GetPDFAnalysisResponse(
                task_id=pdf_analysis.task_id,
                user_id=pdf_analysis.user_id,
                filename=pdf_analysis.filename,
                file_path=pdf_analysis.file_path,
                status=pdf_analysis.status,
                include_cost_estimation=pdf_analysis.include_cost_estimation,
                include_timeline=pdf_analysis.include_timeline,
                include_quantities=pdf_analysis.include_quantities,
                requirements=pdf_analysis.requirements,
                confidence=pdf_analysis.confidence,
                systems_found=pdf_analysis.systems_found,
                total_components=pdf_analysis.total_components,
                processing_time=pdf_analysis.processing_time,
                error_message=pdf_analysis.error_message,
                analysis_result=pdf_analysis.analysis_result,
                created_at=pdf_analysis.created_at,
                updated_at=pdf_analysis.updated_at,
                success=True,
                message="PDF analysis retrieved successfully"
            )
            
        except Exception as e:
            return GetPDFAnalysisResponse(
                task_id=request.task_id,
                success=False,
                message=str(e)
            )


class StartPDFAnalysisUseCase:
    """Use case for starting a PDF analysis."""
    
    def __init__(self, repository: PDFAnalysisRepository, orchestrator: PDFAnalysisOrchestrator):
        self.repository = repository
        self.orchestrator = orchestrator
    
    def execute(self, request: StartPDFAnalysisRequest) -> StartPDFAnalysisResponse:
        """
        Execute the start PDF analysis use case.
        
        Args:
            request: The start request containing task ID
            
        Returns:
            Response with start status
            
        Raises:
            PDFAnalysisNotFoundError: If analysis not found
            InvalidTaskStatusError: If analysis cannot be started
        """
        try:
            # Get analysis
            pdf_analysis = self.repository.get_by_id(request.task_id)
            
            if not pdf_analysis:
                raise PDFAnalysisNotFoundError(f"Analysis with task ID {request.task_id} not found")
            
            # Start analysis
            pdf_analysis.start_analysis()
            
            # Update in repository
            updated_analysis = self.repository.update(pdf_analysis)
            
            # Start processing in orchestrator
            self.orchestrator.start_processing(request.task_id)
            
            # Return response
            return StartPDFAnalysisResponse(
                task_id=updated_analysis.task_id,
                status=updated_analysis.status,
                started_at=updated_analysis.updated_at,
                success=True,
                message="PDF analysis started successfully"
            )
            
        except Exception as e:
            return StartPDFAnalysisResponse(
                task_id=request.task_id,
                success=False,
                message=str(e)
            )


class CompletePDFAnalysisUseCase:
    """Use case for completing a PDF analysis."""
    
    def __init__(self, repository: PDFAnalysisRepository):
        self.repository = repository
    
    def execute(self, request: CompletePDFAnalysisRequest) -> CompletePDFAnalysisResponse:
        """
        Execute the complete PDF analysis use case.
        
        Args:
            request: The complete request containing analysis results
            
        Returns:
            Response with completion status
            
        Raises:
            PDFAnalysisNotFoundError: If analysis not found
            InvalidTaskStatusError: If analysis cannot be completed
        """
        try:
            # Get analysis
            pdf_analysis = self.repository.get_by_id(request.task_id)
            
            if not pdf_analysis:
                raise PDFAnalysisNotFoundError(f"Analysis with task ID {request.task_id} not found")
            
            # Complete analysis
            pdf_analysis.complete_analysis(
                confidence=request.confidence,
                systems_found=request.systems_found,
                total_components=request.total_components,
                processing_time=request.processing_time,
                analysis_result=request.analysis_result
            )
            
            # Update in repository
            updated_analysis = self.repository.update(pdf_analysis)
            
            # Return response
            return CompletePDFAnalysisResponse(
                task_id=updated_analysis.task_id,
                status=updated_analysis.status,
                confidence=updated_analysis.confidence,
                systems_found=updated_analysis.systems_found,
                total_components=updated_analysis.total_components,
                processing_time=updated_analysis.processing_time,
                completed_at=updated_analysis.updated_at,
                success=True,
                message="PDF analysis completed successfully"
            )
            
        except Exception as e:
            return CompletePDFAnalysisResponse(
                task_id=request.task_id,
                success=False,
                message=str(e)
            )


class FailPDFAnalysisUseCase:
    """Use case for failing a PDF analysis."""
    
    def __init__(self, repository: PDFAnalysisRepository):
        self.repository = repository
    
    def execute(self, request: FailPDFAnalysisRequest) -> FailPDFAnalysisResponse:
        """
        Execute the fail PDF analysis use case.
        
        Args:
            request: The fail request containing error details
            
        Returns:
            Response with failure status
            
        Raises:
            PDFAnalysisNotFoundError: If analysis not found
            InvalidTaskStatusError: If analysis cannot be failed
        """
        try:
            # Get analysis
            pdf_analysis = self.repository.get_by_id(request.task_id)
            
            if not pdf_analysis:
                raise PDFAnalysisNotFoundError(f"Analysis with task ID {request.task_id} not found")
            
            # Fail analysis
            pdf_analysis.fail_analysis(
                error_message=request.error_message,
                processing_time=request.processing_time
            )
            
            # Update in repository
            updated_analysis = self.repository.update(pdf_analysis)
            
            # Return response
            return FailPDFAnalysisResponse(
                task_id=updated_analysis.task_id,
                status=updated_analysis.status,
                error_message=updated_analysis.error_message,
                processing_time=updated_analysis.processing_time,
                failed_at=updated_analysis.updated_at,
                success=True,
                message="PDF analysis failed"
            )
            
        except Exception as e:
            return FailPDFAnalysisResponse(
                task_id=request.task_id,
                success=False,
                message=str(e)
            )


class CancelPDFAnalysisUseCase:
    """Use case for cancelling a PDF analysis."""
    
    def __init__(self, repository: PDFAnalysisRepository):
        self.repository = repository
    
    def execute(self, request: CancelPDFAnalysisRequest) -> CancelPDFAnalysisResponse:
        """
        Execute the cancel PDF analysis use case.
        
        Args:
            request: The cancel request containing task ID
            
        Returns:
            Response with cancellation status
            
        Raises:
            PDFAnalysisNotFoundError: If analysis not found
            InvalidTaskStatusError: If analysis cannot be cancelled
        """
        try:
            # Get analysis
            pdf_analysis = self.repository.get_by_id(request.task_id)
            
            if not pdf_analysis:
                raise PDFAnalysisNotFoundError(f"Analysis with task ID {request.task_id} not found")
            
            # Cancel analysis
            pdf_analysis.cancel_analysis()
            
            # Update in repository
            updated_analysis = self.repository.update(pdf_analysis)
            
            # Return response
            return CancelPDFAnalysisResponse(
                task_id=updated_analysis.task_id,
                status=updated_analysis.status,
                cancelled_at=updated_analysis.updated_at,
                success=True,
                message="PDF analysis cancelled successfully"
            )
            
        except Exception as e:
            return CancelPDFAnalysisResponse(
                task_id=request.task_id,
                success=False,
                message=str(e)
            )


class GetPDFAnalysisStatusUseCase:
    """Use case for getting PDF analysis status."""
    
    def __init__(self, repository: PDFAnalysisRepository):
        self.repository = repository
    
    def execute(self, request: GetPDFAnalysisStatusRequest) -> GetPDFAnalysisStatusResponse:
        """
        Execute the get PDF analysis status use case.
        
        Args:
            request: The status request containing task ID
            
        Returns:
            Response with analysis status
            
        Raises:
            PDFAnalysisNotFoundError: If analysis not found
        """
        try:
            # Get analysis
            pdf_analysis = self.repository.get_by_id(request.task_id)
            
            if not pdf_analysis:
                raise PDFAnalysisNotFoundError(f"Analysis with task ID {request.task_id} not found")
            
            # Return response
            return GetPDFAnalysisStatusResponse(
                task_id=pdf_analysis.task_id,
                status=pdf_analysis.status,
                created_at=pdf_analysis.created_at,
                updated_at=pdf_analysis.updated_at,
                success=True,
                message="PDF analysis status retrieved successfully"
            )
            
        except Exception as e:
            return GetPDFAnalysisStatusResponse(
                task_id=request.task_id,
                success=False,
                message=str(e)
            )


class GetPDFAnalysisResultUseCase:
    """Use case for getting PDF analysis results."""
    
    def __init__(self, repository: PDFAnalysisRepository):
        self.repository = repository
    
    def execute(self, request: GetPDFAnalysisResultRequest) -> GetPDFAnalysisResultResponse:
        """
        Execute the get PDF analysis result use case.
        
        Args:
            request: The result request containing task ID
            
        Returns:
            Response with analysis results
            
        Raises:
            PDFAnalysisNotFoundError: If analysis not found
        """
        try:
            # Get analysis with result
            pdf_analysis = self.repository.get_analysis_with_result(request.task_id)
            
            if not pdf_analysis:
                raise PDFAnalysisNotFoundError(f"Analysis with task ID {request.task_id} not found")
            
            if not pdf_analysis.is_completed():
                return GetPDFAnalysisResultResponse(
                    task_id=pdf_analysis.task_id,
                    status=pdf_analysis.status,
                    success=False,
                    message="Analysis is not completed yet"
                )
            
            # Return response
            return GetPDFAnalysisResultResponse(
                task_id=pdf_analysis.task_id,
                status=pdf_analysis.status,
                confidence=pdf_analysis.confidence,
                systems_found=pdf_analysis.systems_found,
                total_components=pdf_analysis.total_components,
                processing_time=pdf_analysis.processing_time,
                analysis_result=pdf_analysis.analysis_result,
                success=True,
                message="PDF analysis result retrieved successfully"
            )
            
        except Exception as e:
            return GetPDFAnalysisResultResponse(
                task_id=request.task_id,
                success=False,
                message=str(e)
            )


class ListPDFAnalysesUseCase:
    """Use case for listing PDF analyses."""
    
    def __init__(self, repository: PDFAnalysisRepository):
        self.repository = repository
    
    def execute(self, request: ListPDFAnalysesRequest) -> ListPDFAnalysesResponse:
        """
        Execute the list PDF analyses use case.
        
        Args:
            request: The list request containing filters
            
        Returns:
            Response with list of analyses
        """
        try:
            analyses = []
            
            if request.user_id:
                analyses = self.repository.get_by_user_id(request.user_id, request.limit)
            elif request.status:
                analyses = self.repository.get_by_status(request.status, request.limit)
            else:
                # Get all analyses (implement pagination if needed)
                analyses = self.repository.get_by_user_id(request.user_id, request.limit)
            
            # Convert to DTOs
            analysis_dtos = []
            for analysis in analyses:
                analysis_dtos.append({
                    'task_id': str(analysis.task_id),
                    'user_id': str(analysis.user_id),
                    'filename': str(analysis.filename),
                    'status': str(analysis.status),
                    'confidence': float(analysis.confidence) if analysis.confidence else None,
                    'systems_found': analysis.systems_found or [],
                    'total_components': analysis.total_components or 0,
                    'processing_time': analysis.processing_time,
                    'created_at': analysis.created_at.isoformat(),
                    'updated_at': analysis.updated_at.isoformat()
                })
            
            # Return response
            return ListPDFAnalysesResponse(
                analyses=analysis_dtos,
                total_count=len(analysis_dtos),
                success=True,
                message=f"Retrieved {len(analysis_dtos)} PDF analyses"
            )
            
        except Exception as e:
            return ListPDFAnalysesResponse(
                analyses=[],
                total_count=0,
                success=False,
                message=str(e)
            )


class GetPDFAnalysisStatisticsUseCase:
    """Use case for getting PDF analysis statistics."""
    
    def __init__(self, repository: PDFAnalysisRepository):
        self.repository = repository
    
    def execute(self, request: GetPDFAnalysisStatisticsRequest) -> GetPDFAnalysisStatisticsResponse:
        """
        Execute the get PDF analysis statistics use case.
        
        Args:
            request: The statistics request
            
        Returns:
            Response with analysis statistics
        """
        try:
            # Get statistics from repository
            statistics = self.repository.get_statistics()
            
            # Return response
            return GetPDFAnalysisStatisticsResponse(
                statistics=statistics,
                success=True,
                message="PDF analysis statistics retrieved successfully"
            )
            
        except Exception as e:
            return GetPDFAnalysisStatisticsResponse(
                statistics={},
                success=False,
                message=str(e)
            ) 