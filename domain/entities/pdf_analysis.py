"""
PDF Analysis Domain Entity

This module contains the PDFAnalysis domain entity that represents
the core business object for PDF analysis operations with identity,
lifecycle, and business logic.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from ..value_objects import (
    TaskId, UserId, TaskStatus, ConfidenceScore,
    FilePath, FileName, AnalysisResult
)
from ..events import (
    PDFAnalysisCreated, PDFAnalysisStarted, PDFAnalysisCompleted,
    PDFAnalysisFailed, PDFAnalysisCancelled, publish_event
)
from ..exceptions import (
    InvalidPDFAnalysisError, InvalidTaskStatusError,
    raise_domain_exception
)


@dataclass
class PDFAnalysis:
    """
    PDF Analysis domain entity with business logic and validation.

    This entity represents a PDF analysis task with its lifecycle,
    business rules, and domain logic.
    """

    # Identity
    task_id: TaskId

    # Core attributes
    user_id: UserId
    filename: FileName
    file_path: FilePath
    status: TaskStatus

    # Analysis requirements
    include_cost_estimation: bool = True
    include_timeline: bool = True
    include_quantities: bool = True
    requirements: Dict[str, Any] = field(default_factory=dict)

    # Analysis results
    confidence: Optional[ConfidenceScore] = None
    systems_found: Optional[List[str]] = None
    total_components: Optional[int] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None

    # Analysis result data
    analysis_result: Optional[AnalysisResult] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate entity invariants after initialization."""
        self._validate_invariants()

    def _validate_invariants(self):
        """Validate entity business rules and invariants."""
        if not self.task_id:
            raise_domain_exception(InvalidPDFAnalysisError, "Task ID is required")

        if not self.user_id:
            raise_domain_exception(InvalidPDFAnalysisError, "User ID is required")

        if not self.filename:
            raise_domain_exception(InvalidPDFAnalysisError, "Filename is required")

        if not self.file_path:
            raise_domain_exception(InvalidPDFAnalysisError, "File path is required")

        if not self.status:
            raise_domain_exception(InvalidPDFAnalysisError, "Status is required")

        # Validate filename extension
        if not str(self.filename).lower().endswith('.pdf'):
            raise_domain_exception(InvalidPDFAnalysisError, "File must be a PDF")

    def start_analysis(self) -> None:
        """Start the PDF analysis process."""
        if self.status != TaskStatus.PENDING:
            raise_domain_exception(
                InvalidTaskStatusError,
                f"Cannot start analysis from status: {self.status}"
            )

        self.status = TaskStatus.PROCESSING
        self.updated_at = datetime.utcnow()

        # Publish domain event
        publish_event(PDFAnalysisStarted(
            task_id=self.task_id,
            user_id=self.user_id,
            timestamp=datetime.utcnow()
        ))

    def complete_analysis(
        self,
        confidence: ConfidenceScore,
        systems_found: List[str],
        total_components: int,
        processing_time: float,
        analysis_result: AnalysisResult
    ) -> None:
        """Complete the PDF analysis with results."""
        if self.status != TaskStatus.PROCESSING:
            raise_domain_exception(
                InvalidTaskStatusError,
                f"Cannot complete analysis from status: {self.status}"
            )

        self.status = TaskStatus.COMPLETED
        self.confidence = confidence
        self.systems_found = systems_found
        self.total_components = total_components
        self.processing_time = processing_time
        self.analysis_result = analysis_result
        self.updated_at = datetime.utcnow()

        # Publish domain event
        publish_event(PDFAnalysisCompleted(
            task_id=self.task_id,
            user_id=self.user_id,
            confidence=confidence,
            systems_found=systems_found,
            total_components=total_components,
            processing_time=processing_time,
            timestamp=datetime.utcnow()
        ))

    def fail_analysis(self, error_message: str, processing_time: float) -> None:
        """Mark the PDF analysis as failed."""
        if self.status != TaskStatus.PROCESSING:
            raise_domain_exception(
                InvalidTaskStatusError,
                f"Cannot fail analysis from status: {self.status}"
            )

        self.status = TaskStatus.FAILED
        self.error_message = error_message
        self.processing_time = processing_time
        self.updated_at = datetime.utcnow()

        # Publish domain event
        publish_event(PDFAnalysisFailed(
            task_id=self.task_id,
            user_id=self.user_id,
            error_message=error_message,
            processing_time=processing_time,
            timestamp=datetime.utcnow()
        ))

    def cancel_analysis(self) -> None:
        """Cancel the PDF analysis."""
        if self.status not in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
            raise_domain_exception(
                InvalidTaskStatusError,
                f"Cannot cancel analysis from status: {self.status}"
            )

        self.status = TaskStatus.CANCELLED
        self.updated_at = datetime.utcnow()

        # Publish domain event
        publish_event(PDFAnalysisCancelled(
            task_id=self.task_id,
            user_id=self.user_id,
            timestamp=datetime.utcnow()
        ))

    def update_requirements(self, requirements: Dict[str, Any]) -> None:
        """Update analysis requirements."""
        self.requirements = requirements
        self.updated_at = datetime.utcnow()

    def is_completed(self) -> bool:
        """Check if analysis is completed."""
        return self.status == TaskStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if analysis failed."""
        return self.status == TaskStatus.FAILED

    def is_cancelled(self) -> bool:
        """Check if analysis was cancelled."""
        return self.status == TaskStatus.CANCELLED

    def is_processing(self) -> bool:
        """Check if analysis is processing."""
        return self.status == TaskStatus.PROCESSING

    def can_be_cancelled(self) -> bool:
        """Check if analysis can be cancelled."""
        return self.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]

    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get analysis summary for reporting."""
        return {
            'task_id': str(self.task_id),
            'user_id': str(self.user_id),
            'status': str(self.status),
            'filename': str(self.filename),
            'confidence': float(self.confidence) if self.confidence else None,
            'systems_found': self.systems_found or [],
            'total_components': self.total_components or 0,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for persistence."""
        return {
            'task_id': str(self.task_id),
            'user_id': str(self.user_id),
            'filename': str(self.filename),
            'file_path': str(self.file_path),
            'status': str(self.status),
            'include_cost_estimation': self.include_cost_estimation,
            'include_timeline': self.include_timeline,
            'include_quantities': self.include_quantities,
            'requirements': self.requirements,
            'confidence': float(self.confidence) if self.confidence else None,
            'systems_found': self.systems_found,
            'total_components': self.total_components,
            'processing_time': self.processing_time,
            'error_message': self.error_message,
            'analysis_result': self.analysis_result.to_dict() if self.analysis_result else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PDFAnalysis':
        """Create entity from dictionary."""
        from ..value_objects import TaskId, UserId, FileName, FilePath, TaskStatus, ConfidenceScore, AnalysisResult

        return cls(
            task_id=TaskId(data['task_id']),
            user_id=UserId(data['user_id']),
            filename=FileName(data['filename']),
            file_path=FilePath(data['file_path']),
            status=TaskStatus(data['status']),
            include_cost_estimation=data.get('include_cost_estimation', True),
            include_timeline=data.get('include_timeline', True),
            include_quantities=data.get('include_quantities', True),
            requirements=data.get('requirements', {}),
            confidence=ConfidenceScore(data['confidence']) if data.get('confidence') else None,
            systems_found=data.get('systems_found'),
            total_components=data.get('total_components'),
            processing_time=data.get('processing_time'),
            error_message=data.get('error_message'),
            analysis_result=AnalysisResult.from_dict(data['analysis_result']) if data.get('analysis_result') else None,
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
