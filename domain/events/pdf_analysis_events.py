"""
PDF Analysis Domain Events

This module contains domain events for PDF analysis operations.
Domain events represent significant occurrences in the domain.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..value_objects import TaskId, UserId, ConfidenceScore


@dataclass
class PDFAnalysisCreated:
    """Event raised when a PDF analysis is created."""
    task_id: TaskId
    user_id: UserId
    filename: str
    timestamp: datetime


@dataclass
class PDFAnalysisStarted:
    """Event raised when a PDF analysis starts processing."""
    task_id: TaskId
    user_id: UserId
    timestamp: datetime


@dataclass
class PDFAnalysisCompleted:
    """Event raised when a PDF analysis is completed successfully."""
    task_id: TaskId
    user_id: UserId
    confidence: ConfidenceScore
    systems_found: List[str]
    total_components: int
    processing_time: float
    timestamp: datetime


@dataclass
class PDFAnalysisFailed:
    """Event raised when a PDF analysis fails."""
    task_id: TaskId
    user_id: UserId
    error_message: str
    processing_time: float
    timestamp: datetime


@dataclass
class PDFAnalysisCancelled:
    """Event raised when a PDF analysis is cancelled."""
    task_id: TaskId
    user_id: UserId
    timestamp: datetime


@dataclass
class PDFAnalysisResultGenerated:
    """Event raised when analysis results are generated."""
    task_id: TaskId
    user_id: UserId
    project_info: Dict[str, Any]
    systems: Dict[str, Any]
    quantities: Dict[str, Any]
    cost_estimates: Dict[str, float]
    timeline: Dict[str, Any]
    confidence: ConfidenceScore
    timestamp: datetime


@dataclass
class PDFAnalysisExported:
    """Event raised when a PDF analysis is exported."""
    task_id: TaskId
    user_id: UserId
    export_format: str
    export_path: str
    timestamp: datetime


@dataclass
class PDFAnalysisValidated:
    """Event raised when a PDF analysis is validated."""
    task_id: TaskId
    user_id: UserId
    validation_score: float
    validation_issues: List[str]
    validation_recommendations: List[str]
    timestamp: datetime


@dataclass
class PDFAnalysisRequirementsUpdated:
    """Event raised when PDF analysis requirements are updated."""
    task_id: TaskId
    user_id: UserId
    old_requirements: Dict[str, Any]
    new_requirements: Dict[str, Any]
    timestamp: datetime


@dataclass
class PDFAnalysisStatusChanged:
    """Event raised when PDF analysis status changes."""
    task_id: TaskId
    user_id: UserId
    old_status: str
    new_status: str
    timestamp: datetime


@dataclass
class PDFAnalysisProcessingStarted:
    """Event raised when PDF processing begins."""
    task_id: TaskId
    user_id: UserId
    file_size: int
    processing_engine: str
    timestamp: datetime


@dataclass
class PDFAnalysisProcessingProgress:
    """Event raised during PDF processing progress."""
    task_id: TaskId
    user_id: UserId
    progress_percentage: float
    current_step: str
    estimated_time_remaining: Optional[float]
    timestamp: datetime


@dataclass
class PDFAnalysisSymbolRecognized:
    """Event raised when a symbol is recognized in the PDF."""
    task_id: TaskId
    user_id: UserId
    symbol_type: str
    symbol_confidence: ConfidenceScore
    symbol_position: Dict[str, float]
    symbol_properties: Dict[str, Any]
    timestamp: datetime


@dataclass
class PDFAnalysisSystemIdentified:
    """Event raised when a system is identified in the PDF."""
    task_id: TaskId
    user_id: UserId
    system_type: str
    system_confidence: ConfidenceScore
    component_count: int
    system_properties: Dict[str, Any]
    timestamp: datetime


@dataclass
class PDFAnalysisQualityAssessed:
    """Event raised when PDF analysis quality is assessed."""
    task_id: TaskId
    user_id: UserId
    overall_score: float
    completeness_score: float
    accuracy_score: float
    consistency_score: float
    quality_issues: List[str]
    quality_recommendations: List[str]
    timestamp: datetime


@dataclass
class PDFAnalysisCostEstimated:
    """Event raised when costs are estimated for the analysis."""
    task_id: TaskId
    user_id: UserId
    total_cost: float
    cost_breakdown: Dict[str, float]
    currency: str
    timestamp: datetime


@dataclass
class PDFAnalysisTimelineGenerated:
    """Event raised when timeline is generated for the analysis."""
    task_id: TaskId
    user_id: UserId
    total_duration: float
    timeline_breakdown: Dict[str, float]
    critical_path: List[str]
    timestamp: datetime


@dataclass
class PDFAnalysisBackupCreated:
    """Event raised when a backup is created for the analysis."""
    task_id: TaskId
    user_id: UserId
    backup_path: str
    backup_size: int
    timestamp: datetime


@dataclass
class PDFAnalysisRestored:
    """Event raised when a PDF analysis is restored from backup."""
    task_id: TaskId
    user_id: UserId
    backup_path: str
    restore_timestamp: datetime
    timestamp: datetime


@dataclass
class PDFAnalysisArchived:
    """Event raised when a PDF analysis is archived."""
    task_id: TaskId
    user_id: UserId
    archive_path: str
    archive_reason: str
    timestamp: datetime


@dataclass
class PDFAnalysisShared:
    """Event raised when a PDF analysis is shared."""
    task_id: TaskId
    user_id: UserId
    shared_with: List[str]
    share_permissions: Dict[str, Any]
    timestamp: datetime


@dataclass
class PDFAnalysisCommented:
    """Event raised when a comment is added to the analysis."""
    task_id: TaskId
    user_id: UserId
    comment_id: str
    comment_text: str
    comment_type: str
    timestamp: datetime


@dataclass
class PDFAnalysisVersionCreated:
    """Event raised when a new version of the analysis is created."""
    task_id: TaskId
    user_id: UserId
    version_number: int
    version_reason: str
    previous_version: Optional[str]
    timestamp: datetime


@dataclass
class PDFAnalysisCollaboratorAdded:
    """Event raised when a collaborator is added to the analysis."""
    task_id: TaskId
    user_id: UserId
    collaborator_id: str
    collaborator_role: str
    collaborator_permissions: Dict[str, Any]
    timestamp: datetime


@dataclass
class PDFAnalysisCollaboratorRemoved:
    """Event raised when a collaborator is removed from the analysis."""
    task_id: TaskId
    user_id: UserId
    collaborator_id: str
    removal_reason: str
    timestamp: datetime


@dataclass
class PDFAnalysisNotificationSent:
    """Event raised when a notification is sent about the analysis."""
    task_id: TaskId
    user_id: UserId
    notification_type: str
    notification_recipients: List[str]
    notification_content: Dict[str, Any]
    timestamp: datetime


@dataclass
class PDFAnalysisAuditLogCreated:
    """Event raised when an audit log entry is created."""
    task_id: TaskId
    user_id: UserId
    audit_action: str
    audit_details: Dict[str, Any]
    audit_timestamp: datetime
    timestamp: datetime
