"""
PDF Analysis DTOs (Data Transfer Objects)

This module contains DTOs for PDF analysis operations.
DTOs are used for data transfer between layers without exposing domain objects.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.value_objects import (
    TaskId, UserId, TaskStatus, ConfidenceScore, 
    FileName, FilePath, AnalysisResult, AnalysisRequirements
)


# Request DTOs
@dataclass
class CreatePDFAnalysisRequest:
    """Request DTO for creating a PDF analysis."""
    task_id: TaskId
    user_id: UserId
    filename: FileName
    file_path: FilePath
    include_cost_estimation: bool = True
    include_timeline: bool = True
    include_quantities: bool = True
    requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GetPDFAnalysisRequest:
    """Request DTO for getting a PDF analysis."""
    task_id: TaskId


@dataclass
class UpdatePDFAnalysisRequest:
    """Request DTO for updating a PDF analysis."""
    task_id: TaskId
    include_cost_estimation: Optional[bool] = None
    include_timeline: Optional[bool] = None
    include_quantities: Optional[bool] = None
    requirements: Optional[Dict[str, Any]] = None


@dataclass
class DeletePDFAnalysisRequest:
    """Request DTO for deleting a PDF analysis."""
    task_id: TaskId


@dataclass
class StartPDFAnalysisRequest:
    """Request DTO for starting a PDF analysis."""
    task_id: TaskId


@dataclass
class CompletePDFAnalysisRequest:
    """Request DTO for completing a PDF analysis."""
    task_id: TaskId
    confidence: ConfidenceScore
    systems_found: List[str]
    total_components: int
    processing_time: float
    analysis_result: AnalysisResult


@dataclass
class FailPDFAnalysisRequest:
    """Request DTO for failing a PDF analysis."""
    task_id: TaskId
    error_message: str
    processing_time: float


@dataclass
class CancelPDFAnalysisRequest:
    """Request DTO for cancelling a PDF analysis."""
    task_id: TaskId


@dataclass
class GetPDFAnalysisStatusRequest:
    """Request DTO for getting PDF analysis status."""
    task_id: TaskId


@dataclass
class GetPDFAnalysisResultRequest:
    """Request DTO for getting PDF analysis results."""
    task_id: TaskId


@dataclass
class ExportPDFAnalysisRequest:
    """Request DTO for exporting PDF analysis."""
    task_id: TaskId
    export_format: str  # 'json', 'csv', 'pdf', 'excel'
    include_metadata: bool = True


@dataclass
class ValidatePDFAnalysisRequest:
    """Request DTO for validating PDF analysis."""
    task_id: TaskId
    validation_rules: Optional[Dict[str, Any]] = None


@dataclass
class ListPDFAnalysesRequest:
    """Request DTO for listing PDF analyses."""
    user_id: Optional[UserId] = None
    status: Optional[TaskStatus] = None
    limit: int = 50
    offset: int = 0


@dataclass
class GetPDFAnalysisStatisticsRequest:
    """Request DTO for getting PDF analysis statistics."""
    user_id: Optional[UserId] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# Response DTOs
@dataclass
class CreatePDFAnalysisResponse:
    """Response DTO for creating a PDF analysis."""
    task_id: TaskId
    user_id: Optional[UserId] = None
    filename: Optional[FileName] = None
    status: Optional[TaskStatus] = None
    created_at: Optional[datetime] = None
    success: bool
    message: str


@dataclass
class GetPDFAnalysisResponse:
    """Response DTO for getting a PDF analysis."""
    task_id: TaskId
    user_id: Optional[UserId] = None
    filename: Optional[FileName] = None
    file_path: Optional[FilePath] = None
    status: Optional[TaskStatus] = None
    include_cost_estimation: Optional[bool] = None
    include_timeline: Optional[bool] = None
    include_quantities: Optional[bool] = None
    requirements: Optional[Dict[str, Any]] = None
    confidence: Optional[ConfidenceScore] = None
    systems_found: Optional[List[str]] = None
    total_components: Optional[int] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    analysis_result: Optional[AnalysisResult] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    success: bool
    message: str


@dataclass
class UpdatePDFAnalysisResponse:
    """Response DTO for updating a PDF analysis."""
    task_id: TaskId
    status: Optional[TaskStatus] = None
    updated_at: Optional[datetime] = None
    success: bool
    message: str


@dataclass
class DeletePDFAnalysisResponse:
    """Response DTO for deleting a PDF analysis."""
    task_id: TaskId
    success: bool
    message: str


@dataclass
class StartPDFAnalysisResponse:
    """Response DTO for starting a PDF analysis."""
    task_id: TaskId
    status: Optional[TaskStatus] = None
    started_at: Optional[datetime] = None
    success: bool
    message: str


@dataclass
class CompletePDFAnalysisResponse:
    """Response DTO for completing a PDF analysis."""
    task_id: TaskId
    status: Optional[TaskStatus] = None
    confidence: Optional[ConfidenceScore] = None
    systems_found: Optional[List[str]] = None
    total_components: Optional[int] = None
    processing_time: Optional[float] = None
    completed_at: Optional[datetime] = None
    success: bool
    message: str


@dataclass
class FailPDFAnalysisResponse:
    """Response DTO for failing a PDF analysis."""
    task_id: TaskId
    status: Optional[TaskStatus] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    failed_at: Optional[datetime] = None
    success: bool
    message: str


@dataclass
class CancelPDFAnalysisResponse:
    """Response DTO for cancelling a PDF analysis."""
    task_id: TaskId
    status: Optional[TaskStatus] = None
    cancelled_at: Optional[datetime] = None
    success: bool
    message: str


@dataclass
class GetPDFAnalysisStatusResponse:
    """Response DTO for getting PDF analysis status."""
    task_id: TaskId
    status: Optional[TaskStatus] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    success: bool
    message: str


@dataclass
class GetPDFAnalysisResultResponse:
    """Response DTO for getting PDF analysis results."""
    task_id: TaskId
    status: Optional[TaskStatus] = None
    confidence: Optional[ConfidenceScore] = None
    systems_found: Optional[List[str]] = None
    total_components: Optional[int] = None
    processing_time: Optional[float] = None
    analysis_result: Optional[AnalysisResult] = None
    success: bool
    message: str


@dataclass
class ExportPDFAnalysisResponse:
    """Response DTO for exporting PDF analysis."""
    task_id: TaskId
    export_format: str
    download_url: Optional[str] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None
    success: bool
    message: str


@dataclass
class ValidatePDFAnalysisResponse:
    """Response DTO for validating PDF analysis."""
    task_id: TaskId
    validation_score: Optional[float] = None
    validation_issues: Optional[List[str]] = None
    validation_recommendations: Optional[List[str]] = None
    success: bool
    message: str


@dataclass
class ListPDFAnalysesResponse:
    """Response DTO for listing PDF analyses."""
    analyses: List[Dict[str, Any]]
    total_count: int
    success: bool
    message: str


@dataclass
class GetPDFAnalysisStatisticsResponse:
    """Response DTO for getting PDF analysis statistics."""
    statistics: Dict[str, Any]
    success: bool
    message: str


# Summary DTOs
@dataclass
class PDFAnalysisSummary:
    """Summary DTO for PDF analysis."""
    task_id: str
    user_id: str
    filename: str
    status: str
    confidence: Optional[float] = None
    systems_found: Optional[List[str]] = None
    total_components: Optional[int] = None
    processing_time: Optional[float] = None
    created_at: str
    updated_at: str


@dataclass
class PDFAnalysisDetails:
    """Detailed DTO for PDF analysis."""
    task_id: str
    user_id: str
    filename: str
    file_path: str
    status: str
    include_cost_estimation: bool
    include_timeline: bool
    include_quantities: bool
    requirements: Dict[str, Any]
    confidence: Optional[float] = None
    systems_found: Optional[List[str]] = None
    total_components: Optional[int] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    analysis_result: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str


@dataclass
class PDFAnalysisResult:
    """Result DTO for PDF analysis."""
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


@dataclass
class PDFAnalysisStatistics:
    """Statistics DTO for PDF analysis."""
    total_analyses: int
    completed_analyses: int
    failed_analyses: int
    pending_analyses: int
    processing_analyses: int
    cancelled_analyses: int
    average_processing_time: float
    average_confidence: float
    total_components_identified: int
    systems_found_count: Dict[str, int]
    success_rate: float
    error_rate: float


@dataclass
class PDFAnalysisExport:
    """Export DTO for PDF analysis."""
    task_id: str
    export_format: str
    download_url: str
    filename: str
    file_size: int
    export_timestamp: str
    export_metadata: Dict[str, Any]


@dataclass
class PDFAnalysisValidation:
    """Validation DTO for PDF analysis."""
    task_id: str
    validation_score: float
    validation_issues: List[str]
    validation_recommendations: List[str]
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    quality_assessment: Dict[str, Any] 