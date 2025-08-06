"""
MCP-Engineering Domain Entities

This module contains the core domain entities for MCP-Engineering operations,
following domain-driven design principles and clean architecture patterns.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
from uuid import uuid4


class ValidationStatus(Enum):
    """Validation status enumeration."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    PENDING = "pending"
    ERROR = "error"


class ValidationType(Enum):
    """Validation type enumeration."""

    STRUCTURAL = "structural"
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    PLUMBING = "plumbing"
    FIRE = "fire"
    ACCESSIBILITY = "accessibility"
    ENERGY = "energy"


class IssueSeverity(Enum):
    """Issue severity enumeration."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SuggestionType(Enum):
    """Suggestion type enumeration."""

    OPTIMIZATION = "optimization"
    COMPLIANCE = "compliance"
    SAFETY = "safety"
    EFFICIENCY = "efficiency"
    COST_SAVING = "cost_saving"


class ReportType(Enum):
    """Report type enumeration."""

    COMPREHENSIVE = "comprehensive"
    SUMMARY = "summary"
    TECHNICAL = "technical"


class ReportFormat(Enum):
    """Report format enumeration."""

    PDF = "pdf"
    HTML = "html"
    JSON = "json"


@dataclass
class BuildingData:
    """Building data entity for validation."""

    area: float
    height: float
    building_type: str
    occupancy: Optional[str] = None
    floors: Optional[int] = None
    jurisdiction: Optional[str] = None
    address: Optional[str] = None
    construction_type: Optional[str] = None
    year_built: Optional[int] = None
    renovation_year: Optional[int] = None

    def __post_init__(self):
        """Validate building data after initialization."""
        if self.area <= 0:
            raise ValueError("Building area must be positive")
        if self.height <= 0:
            raise ValueError("Building height must be positive")
        if self.floors is not None and self.floors <= 0:
            raise ValueError("Number of floors must be positive")


@dataclass
class ComplianceIssue:
    """Compliance issue entity."""

    code_reference: str
    severity: IssueSeverity
    description: str
    resolution: str
    id: str = field(default_factory=lambda: str(uuid4()))
    affected_systems: List[str] = field(default_factory=list)
    estimated_cost: Optional[float] = None
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate compliance issue after initialization."""
        if not self.code_reference:
            raise ValueError("Code reference is required")
        if not self.description:
            raise ValueError("Description is required")
        if not self.resolution:
            raise ValueError("Resolution is required")


@dataclass
class AIRecommendation:
    """AI-powered recommendation entity."""

    type: SuggestionType
    description: str
    confidence: float
    impact_score: float
    id: str = field(default_factory=lambda: str(uuid4()))
    implementation_cost: Optional[float] = None
    estimated_savings: Optional[float] = None
    affected_systems: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate AI recommendation after initialization."""
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        if not 0 <= self.impact_score <= 1:
            raise ValueError("Impact score must be between 0 and 1")
        if not self.description:
            raise ValueError("Description is required")


@dataclass
class ValidationResult:
    """Validation result entity."""

    building_data: BuildingData
    validation_type: ValidationType
    status: ValidationStatus
    id: str = field(default_factory=lambda: str(uuid4()))
    issues: List[ComplianceIssue] = field(default_factory=list)
    suggestions: List[AIRecommendation] = field(default_factory=list)
    confidence_score: float = 0.0
    processing_time: float = 0.0
    model_version: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate validation result after initialization."""
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
        if self.processing_time < 0:
            raise ValueError("Processing time cannot be negative")

    @property
    def has_critical_issues(self) -> bool:
        """Check if validation has critical issues."""
        return any(issue.severity == IssueSeverity.CRITICAL for issue in self.issues)

    @property
    def has_high_priority_issues(self) -> bool:
        """Check if validation has high priority issues."""
        return any(
            issue.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]
            for issue in self.issues
        )

    @property
    def total_issues(self) -> int:
        """Get total number of issues."""
        return len(self.issues)

    @property
    def total_suggestions(self) -> int:
        """Get total number of suggestions."""
        return len(self.suggestions)

    def add_issue(self, issue: ComplianceIssue) -> None:
        """Add a compliance issue to the validation result."""
        self.issues.append(issue)

    def add_suggestion(self, suggestion: AIRecommendation) -> None:
        """Add an AI recommendation to the validation result."""
        self.suggestions.append(suggestion)

    def mark_completed(self) -> None:
        """Mark validation as completed."""
        self.completed_at = datetime.utcnow()


@dataclass
class KnowledgeSearchResult:
    """Knowledge base search result entity."""

    code_reference: str
    title: str
    content: str
    code_standard: str
    relevance_score: float
    id: str = field(default_factory=lambda: str(uuid4()))
    section_number: Optional[str] = None
    subsection: Optional[str] = None
    jurisdiction: Optional[str] = None
    effective_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate knowledge search result after initialization."""
        if not 0 <= self.relevance_score <= 1:
            raise ValueError("Relevance score must be between 0 and 1")
        if not self.code_reference:
            raise ValueError("Code reference is required")
        if not self.title:
            raise ValueError("Title is required")
        if not self.content:
            raise ValueError("Content is required")


@dataclass
class MLPrediction:
    """ML prediction entity."""

    prediction_type: str
    prediction_value: str
    confidence: float
    model_version: str
    model_name: str
    id: str = field(default_factory=lambda: str(uuid4()))
    features: List[Dict[str, Any]] = field(default_factory=list)
    processing_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate ML prediction after initialization."""
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        if self.processing_time < 0:
            raise ValueError("Processing time cannot be negative")
        if not self.model_version:
            raise ValueError("Model version is required")
        if not self.model_name:
            raise ValueError("Model name is required")


@dataclass
class ValidationSession:
    """Validation session entity for tracking validation operations."""

    user_id: str
    building_data: BuildingData
    validation_type: ValidationType
    id: str = field(default_factory=lambda: str(uuid4()))
    project_id: Optional[str] = None
    status: ValidationStatus = ValidationStatus.PENDING
    validation_result: Optional[ValidationResult] = None
    include_suggestions: bool = True
    confidence_threshold: float = 0.7
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None

    def __post_init__(self):
        """Validate validation session after initialization."""
        if not 0 <= self.confidence_threshold <= 1:
            raise ValueError("Confidence threshold must be between 0 and 1")

    def mark_completed(
        self, validation_result: ValidationResult, processing_time: float
    ) -> None:
        """Mark session as completed with results."""
        self.validation_result = validation_result
        self.completed_at = datetime.utcnow()
        self.processing_time = processing_time
        self.status = validation_result.status


@dataclass
class ComplianceReport:
    """Compliance report entity."""

    building_data: BuildingData
    validation_results: List[ValidationResult]
    report_type: ReportType
    format: ReportFormat
    user_id: str
    id: str = field(default_factory=lambda: str(uuid4()))
    project_id: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)
    download_url: Optional[str] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None

    def __post_init__(self):
        """Validate compliance report after initialization."""
        if not self.validation_results:
            raise ValueError("At least one validation result is required")

    @property
    def total_issues(self) -> int:
        """Get total number of issues across all validation results."""
        return sum(result.total_issues for result in self.validation_results)

    @property
    def total_suggestions(self) -> int:
        """Get total number of suggestions across all validation results."""
        return sum(result.total_suggestions for result in self.validation_results)

    @property
    def has_critical_issues(self) -> bool:
        """Check if any validation result has critical issues."""
        return any(result.has_critical_issues for result in self.validation_results)

    @property
    def overall_status(self) -> ValidationStatus:
        """Get overall validation status."""
        if any(
            result.status == ValidationStatus.FAIL for result in self.validation_results
        ):
            return ValidationStatus.FAIL
        elif any(
            result.status == ValidationStatus.WARNING
            for result in self.validation_results
        ):
            return ValidationStatus.WARNING
        else:
            return ValidationStatus.PASS


@dataclass
class ValidationStatistics:
    """Validation statistics entity."""

    total_validations: int = 0
    successful_validations: int = 0
    failed_validations: int = 0
    average_processing_time: float = 0.0
    total_processing_time: float = 0.0
    average_confidence_score: float = 0.0
    total_issues_found: int = 0
    total_suggestions_generated: int = 0
    most_common_validation_type: Optional[str] = None
    last_validation_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_validations == 0:
            return 0.0
        return self.successful_validations / self.total_validations

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_validations == 0:
            return 0.0
        return self.failed_validations / self.total_validations

    def update_from_validation(
        self, validation_result: ValidationResult, processing_time: float
    ) -> None:
        """Update statistics from a validation result."""
        self.total_validations += 1
        self.total_processing_time += processing_time
        self.average_processing_time = (
            self.total_processing_time / self.total_validations
        )

        if validation_result.status == ValidationStatus.PASS:
            self.successful_validations += 1
        elif validation_result.status == ValidationStatus.FAIL:
            self.failed_validations += 1

        # Update confidence score average
        total_confidence = (
            self.average_confidence_score * (self.total_validations - 1)
            + validation_result.confidence_score
        )
        self.average_confidence_score = total_confidence / self.total_validations

        # Update issue and suggestion counts
        self.total_issues_found += validation_result.total_issues
        self.total_suggestions_generated += validation_result.total_suggestions

        # Update last validation timestamp
        self.last_validation_at = validation_result.created_at
