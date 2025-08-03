"""
PDF Analysis Orchestrator Service

This module contains the orchestrator service for PDF analysis operations.
The orchestrator coordinates between use cases and external services.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import asyncio
import logging

from domain.entities.pdf_analysis import PDFAnalysis
from domain.value_objects import TaskId, UserId, TaskStatus, ConfidenceScore
from domain.repositories import UnitOfWork
from domain.exceptions import (
    PDFAnalysisNotFoundError, InvalidTaskStatusError,
    OrchestratorError, ProcessingError
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
from infrastructure.services.gus_service import GUSService
from infrastructure.services.file_storage_service import FileStorageService


class PDFAnalysisOrchestrator:
    """
    Orchestrator service for PDF analysis operations.
    
    This service coordinates between use cases and external services,
    manages the processing workflow, and handles cross-cutting concerns.
    """
    
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        gus_service: GUSService,
        file_storage_service: FileStorageService
    ):
        self.unit_of_work = unit_of_work
        self.gus_service = gus_service
        self.file_storage_service = file_storage_service
        self.logger = logging.getLogger(__name__)
        
        # Processing state
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # Processing state
        self.active_tasks: Dict[str, asyncio.Task] = {}
    
    async def create_pdf_analysis(
        self,
        user_id: UserId,
        filename: str,
        file_content: bytes,
        include_cost_estimation: bool = True,
        include_timeline: bool = True,
        include_quantities: bool = True,
        requirements: Optional[Dict[str, Any]] = None
    ) -> CreatePDFAnalysisResponse:
        """
        Create a new PDF analysis with file upload.
        
        Args:
            user_id: User ID
            filename: Original filename
            file_content: File content bytes
            include_cost_estimation: Whether to include cost estimation
            include_timeline: Whether to include timeline
            include_quantities: Whether to include quantities
            requirements: Additional requirements
            
        Returns:
            Response with created analysis details
        """
        try:
            # Generate task ID
            task_id = TaskId.generate()
            
            # Validate and save file
            file_path = await self.file_storage_service.save_uploaded_file(
                task_id=str(task_id),
                filename=filename,
                file_content=file_content
            )
            
            # Create request
            request = CreatePDFAnalysisRequest(
                task_id=task_id,
                user_id=user_id,
                filename=filename,
                file_path=file_path,
                include_cost_estimation=include_cost_estimation,
                include_timeline=include_timeline,
                include_quantities=include_quantities,
                requirements=requirements or {}
            )
            
            # Execute use case with Unit of Work
            with self.unit_of_work as uow:
                create_use_case = CreatePDFAnalysisUseCase(uow.pdf_analyses)
                response = create_use_case.execute(request)
                
                if response.success:
                    uow.commit()
                    self.logger.info(f"Created PDF analysis: {task_id}")
                else:
                    uow.rollback()
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error creating PDF analysis: {e}")
            return CreatePDFAnalysisResponse(
                task_id=TaskId.generate(),
                user_id=user_id,
                filename=filename,
                status=TaskStatus.FAILED,
                created_at=datetime.utcnow(),
                success=False,
                message=str(e)
            )
    
    async def get_pdf_analysis(self, task_id: TaskId) -> GetPDFAnalysisResponse:
        """
        Get a PDF analysis by task ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Response with analysis details
        """
        try:
            request = GetPDFAnalysisRequest(task_id=task_id)
            
            with self.unit_of_work as uow:
                get_use_case = GetPDFAnalysisUseCase(uow.pdf_analyses)
                response = get_use_case.execute(request)
            
            if response.success:
                self.logger.info(f"Retrieved PDF analysis: {task_id}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting PDF analysis {task_id}: {e}")
            return GetPDFAnalysisResponse(
                task_id=task_id,
                success=False,
                message=str(e)
            )
    
    async def start_pdf_analysis(self, task_id: TaskId) -> StartPDFAnalysisResponse:
        """
        Start processing a PDF analysis.
        
        Args:
            task_id: Task ID
            
        Returns:
            Response with start status
        """
        try:
            request = StartPDFAnalysisRequest(task_id=task_id)
            
            with self.unit_of_work as uow:
                start_use_case = StartPDFAnalysisUseCase(uow.pdf_analyses, self)
                response = start_use_case.execute(request)
                
                if response.success:
                    uow.commit()
                    self.logger.info(f"Started PDF analysis: {task_id}")
                else:
                    uow.rollback()
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error starting PDF analysis {task_id}: {e}")
            return StartPDFAnalysisResponse(
                task_id=task_id,
                success=False,
                message=str(e)
            )
    
    async def get_pdf_analysis_status(self, task_id: TaskId) -> GetPDFAnalysisStatusResponse:
        """
        Get PDF analysis status.
        
        Args:
            task_id: Task ID
            
        Returns:
            Response with analysis status
        """
        try:
            request = GetPDFAnalysisStatusRequest(task_id=task_id)
            response = self.status_use_case.execute(request)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting PDF analysis status {task_id}: {e}")
            return GetPDFAnalysisStatusResponse(
                task_id=task_id,
                success=False,
                message=str(e)
            )
    
    async def get_pdf_analysis_result(self, task_id: TaskId) -> GetPDFAnalysisResultResponse:
        """
        Get PDF analysis results.
        
        Args:
            task_id: Task ID
            
        Returns:
            Response with analysis results
        """
        try:
            request = GetPDFAnalysisResultRequest(task_id=task_id)
            response = self.result_use_case.execute(request)
            
            if response.success:
                self.logger.info(f"Retrieved PDF analysis result: {task_id}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting PDF analysis result {task_id}: {e}")
            return GetPDFAnalysisResultResponse(
                task_id=task_id,
                success=False,
                message=str(e)
            )
    
    async def cancel_pdf_analysis(self, task_id: TaskId) -> CancelPDFAnalysisResponse:
        """
        Cancel a PDF analysis.
        
        Args:
            task_id: Task ID
            
        Returns:
            Response with cancellation status
        """
        try:
            # Cancel active processing task if exists
            await self._cancel_processing_task(task_id)
            
            request = CancelPDFAnalysisRequest(task_id=task_id)
            response = self.cancel_use_case.execute(request)
            
            if response.success:
                self.logger.info(f"Cancelled PDF analysis: {task_id}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error cancelling PDF analysis {task_id}: {e}")
            return CancelPDFAnalysisResponse(
                task_id=task_id,
                success=False,
                message=str(e)
            )
    
    async def list_pdf_analyses(
        self,
        user_id: Optional[UserId] = None,
        status: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> ListPDFAnalysesResponse:
        """
        List PDF analyses with filters.
        
        Args:
            user_id: Optional user ID filter
            status: Optional status filter
            limit: Maximum number of results
            
        Returns:
            Response with list of analyses
        """
        try:
            request = ListPDFAnalysesRequest(
                user_id=user_id,
                status=status,
                limit=limit
            )
            response = self.list_use_case.execute(request)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error listing PDF analyses: {e}")
            return ListPDFAnalysesResponse(
                analyses=[],
                total_count=0,
                success=False,
                message=str(e)
            )
    
    async def get_pdf_analysis_statistics(
        self,
        user_id: Optional[UserId] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> GetPDFAnalysisStatisticsResponse:
        """
        Get PDF analysis statistics.
        
        Args:
            user_id: Optional user ID filter
            date_from: Optional start date
            date_to: Optional end date
            
        Returns:
            Response with statistics
        """
        try:
            request = GetPDFAnalysisStatisticsRequest(
                user_id=user_id,
                date_from=date_from,
                date_to=date_to
            )
            response = self.statistics_use_case.execute(request)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error getting PDF analysis statistics: {e}")
            return GetPDFAnalysisStatisticsResponse(
                statistics={},
                success=False,
                message=str(e)
            )
    
    def start_processing(self, task_id: TaskId) -> None:
        """
        Start processing a PDF analysis in background.
        
        Args:
            task_id: Task ID to process
        """
        if str(task_id) in self.active_tasks:
            self.logger.warning(f"Task {task_id} is already being processed")
            return
        
        # Create background task
        task = asyncio.create_task(self._process_pdf_analysis(task_id))
        self.active_tasks[str(task_id)] = task
        
        self.logger.info(f"Started background processing for task: {task_id}")
    
    async def _process_pdf_analysis(self, task_id: TaskId) -> None:
        """
        Process PDF analysis in background.
        
        Args:
            task_id: Task ID to process
        """
        start_time = datetime.utcnow()
        
        try:
            # Get analysis using Unit of Work
            with self.unit_of_work as uow:
                analysis = uow.pdf_analyses.get_by_id(task_id)
                if not analysis:
                    raise PDFAnalysisNotFoundError(f"Analysis {task_id} not found")
                
                self.logger.info(f"Processing PDF analysis: {task_id}")
                
                # Get file content
                file_content = await self.file_storage_service.get_file_content(
                    str(task_id), str(analysis.filename)
                )
                
                # Process with GUS service
                result = await self.gus_service.analyze_pdf(
                    task_id=str(task_id),
                    file_content=file_content,
                    filename=str(analysis.filename),
                    requirements=analysis.requirements
                )
                
                # Calculate processing time
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Complete analysis
                complete_request = CompletePDFAnalysisRequest(
                    task_id=task_id,
                    confidence=result.confidence,
                    systems_found=result.systems_found,
                    total_components=result.total_components,
                    processing_time=processing_time,
                    analysis_result=result.analysis_result
                )
                
                complete_use_case = CompletePDFAnalysisUseCase(uow.pdf_analyses)
                response = complete_use_case.execute(complete_request)
                
                if response.success:
                    uow.commit()
                    self.logger.info(f"Completed PDF analysis: {task_id}")
                else:
                    uow.rollback()
                    self.logger.error(f"Failed to complete PDF analysis: {task_id}")
                    
        except Exception as e:
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Fail analysis using Unit of Work
            with self.unit_of_work as uow:
                fail_request = FailPDFAnalysisRequest(
                    task_id=task_id,
                    error_message=str(e),
                    processing_time=processing_time
                )
                
                fail_use_case = FailPDFAnalysisUseCase(uow.pdf_analyses)
                response = fail_use_case.execute(fail_request)
                
                if response.success:
                    uow.commit()
                    self.logger.error(f"Failed PDF analysis: {task_id} - {e}")
                else:
                    uow.rollback()
                    self.logger.error(f"Failed to mark PDF analysis as failed: {task_id}")
        
        finally:
            # Clean up active task
            if str(task_id) in self.active_tasks:
                del self.active_tasks[str(task_id)]
    
    async def _cancel_processing_task(self, task_id: TaskId) -> None:
        """
        Cancel active processing task.
        
        Args:
            task_id: Task ID to cancel
        """
        task_key = str(task_id)
        if task_key in self.active_tasks:
            task = self.active_tasks[task_key]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            del self.active_tasks[task_key]
            self.logger.info(f"Cancelled processing task: {task_id}")
    
    async def cleanup_old_analyses(self, days_to_keep: int = 30) -> int:
        """
        Clean up old PDF analyses.
        
        Args:
            days_to_keep: Number of days to keep analyses
            
        Returns:
            Number of analyses cleaned up
        """
        try:
            cleaned_count = self.repository.cleanup_old_analyses(days_to_keep)
            self.logger.info(f"Cleaned up {cleaned_count} old PDF analyses")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old analyses: {e}")
            return 0
    
    def get_active_tasks(self) -> List[str]:
        """
        Get list of active task IDs.
        
        Returns:
            List of active task IDs
        """
        return list(self.active_tasks.keys())
    
    def is_task_processing(self, task_id: TaskId) -> bool:
        """
        Check if a task is currently being processed.
        
        Args:
            task_id: Task ID to check
            
        Returns:
            True if task is processing, False otherwise
        """
        return str(task_id) in self.active_tasks 