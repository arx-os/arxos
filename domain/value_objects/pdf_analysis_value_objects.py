"""
PDF Analysis Value Objects

This module contains value objects for PDF analysis domain concepts.
Value objects are immutable and represent domain characteristics.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from enum import Enum

from .base import ValueObject, raise_validation_error


class TaskStatus(Enum):
    """Task status value object."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class TaskId(ValueObject):
    """Task identifier value object."""
    value: str

    def __post_init__(self):
        """Validate task ID."""
        if not self.value:
            raise_validation_error("Task ID cannot be empty")
        if len(self.value) < 3:
            raise_validation_error("Task ID must be at least 3 characters")

    @classmethod
def generate(cls) -> 'TaskId':
        """Generate a new task ID."""
        return cls(str(uuid.uuid4()))

    def __str__(self) -> str:
        pass
    """
    Perform __str__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __str__(param)
        print(result)
    """
        return self.value


@dataclass(frozen=True)
class ConfidenceScore(ValueObject):
    """Confidence score value object."""
    value: float

    def __post_init__(self):
        """Validate confidence score."""
        if not isinstance(self.value, (int, float)):
            raise_validation_error("Confidence score must be a number")
        if self.value < 0.0 or self.value > 1.0:
            raise_validation_error("Confidence score must be between 0.0 and 1.0")

    @classmethod
def from_percentage(cls, percentage: float) -> 'ConfidenceScore':
        """Create from percentage (0-100)."""
        if percentage < 0 or percentage > 100:
            raise_validation_error("Percentage must be between 0 and 100")
        return cls(percentage / 100.0)

    def to_percentage(self) -> float:
        """Convert to percentage."""
        return self.value * 100.0

    def is_high(self) -> bool:
        """Check if confidence is high (>= 0.8)."""
        return self.value >= 0.8

    def is_medium(self) -> bool:
        """Check if confidence is medium (0.5-0.8)."""
        return 0.5 <= self.value < 0.8

    def is_low(self) -> bool:
        """Check if confidence is low (< 0.5)."""
        return self.value < 0.5

    def __float__(self) -> float:
        return self.value


@dataclass(frozen=True)
class FileName(ValueObject):
    """File name value object."""
    value: str

    def __post_init__(self):
        """Validate file name."""
        if not self.value:
            raise_validation_error("File name cannot be empty")
        if len(self.value) > 255:
            raise_validation_error("File name too long")
        if '/' in self.value or '\\' in self.value:
            raise_validation_error("File name cannot contain path separators")

    def get_extension(self) -> str:
        """Get file extension."""
        if '.' not in self.value:
            return ""
        return self.value.split('.')[-1].lower()

    def is_pdf(self) -> bool:
        """Check if file is PDF."""
        return self.get_extension() == 'pdf'

    def get_name_without_extension(self) -> str:
        """Get file name without extension."""
        if '.' not in self.value:
            return self.value
        return self.value.rsplit('.', 1)[0]

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class FilePath(ValueObject):
    """File path value object."""
    value: str

    def __post_init__(self):
        """Validate file path."""
        if not self.value:
            raise_validation_error("File path cannot be empty")
        if len(self.value) > 1000:
            raise_validation_error("File path too long")

    def get_filename(self) -> str:
        """Get filename from path."""
        return self.value.split('/')[-1].split('\\')[-1]

    def get_directory(self) -> str:
        """Get directory from path."""
        if '/' in self.value:
            return '/'.join(self.value.split('/')[:-1])
        elif '\\' in self.value:
            return '\\'.join(self.value.split('\\')[:-1])
        return ""

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class AnalysisResult(ValueObject):
    """Analysis result value object."""
    project_info: Dict[str, Any]
    systems: Dict[str, Any]
    quantities: Dict[str, Any]
    cost_estimates: Dict[str, float]
    timeline: Dict[str, Any]
    confidence: ConfidenceScore
    metadata: Dict[str, Any]
    created_at: datetime

    def __post_init__(self):
        """Validate analysis result."""
        if not isinstance(self.project_info, dict):
            raise_validation_error("Project info must be a dictionary")
        if not isinstance(self.systems, dict):
            raise_validation_error("Systems must be a dictionary")
        if not isinstance(self.quantities, dict):
            raise_validation_error("Quantities must be a dictionary")
        if not isinstance(self.cost_estimates, dict):
            raise_validation_error("Cost estimates must be a dictionary")
        if not isinstance(self.timeline, dict):
            raise_validation_error("Timeline must be a dictionary")
        if not isinstance(self.confidence, ConfidenceScore):
            raise_validation_error("Confidence must be a ConfidenceScore")
        if not isinstance(self.metadata, dict):
            raise_validation_error("Metadata must be a dictionary")
        if not isinstance(self.created_at, datetime):
            raise_validation_error("Created at must be a datetime")

    def get_total_cost(self) -> float:
        """Get total cost from estimates."""
        return sum(self.cost_estimates.values()
    def get_system_count(self) -> int:
        """Get number of systems found."""
        return len(self.systems)

    def get_total_components(self) -> int:
        """Get total number of components."""
        return self.quantities.get('total_components', 0)

    def get_system_names(self) -> List[str]:
        """Get list of system names."""
        return list(self.systems.keys()
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'project_info': self.project_info,
            'systems': self.systems,
            'quantities': self.quantities,
            'cost_estimates': self.cost_estimates,
            'timeline': self.timeline,
            'confidence': float(self.confidence),
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """Create from dictionary."""
        return cls(
            project_info=data['project_info'],
            systems=data['systems'],
            quantities=data['quantities'],
            cost_estimates=data['cost_estimates'],
            timeline=data['timeline'],
            confidence=ConfidenceScore(data['confidence']),
            metadata=data['metadata'],
            created_at=datetime.fromisoformat(data['created_at'])
@dataclass(frozen=True)
class AnalysisRequirements(ValueObject):
    """Analysis requirements value object."""
    include_cost_estimation: bool = True
    include_timeline: bool = True
    include_quantities: bool = True
    custom_requirements: Dict[str, Any] = None

    def __post_init__(self):
        """Validate requirements."""
        if self.custom_requirements is None:
            object.__setattr__(self, 'custom_requirements', {})
        if not isinstance(self.custom_requirements, dict):
            raise_validation_error("Custom requirements must be a dictionary")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'include_cost_estimation': self.include_cost_estimation,
            'include_timeline': self.include_timeline,
            'include_quantities': self.include_quantities,
            'custom_requirements': self.custom_requirements
        }

    @classmethod
def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisRequirements':
        """Create from dictionary."""
        return cls(
            include_cost_estimation=data.get('include_cost_estimation', True),
            include_timeline=data.get('include_timeline', True),
            include_quantities=data.get('include_quantities', True),
            custom_requirements=data.get('custom_requirements', {})
