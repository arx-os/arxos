"""
Status Value Object

Represents status values in the domain.
This is a value object that is immutable and defined by its attributes.
"""

from dataclasses import dataclass
from typing import Set, Optional
from enum import Enum


class StatusType(Enum):
    """Enumeration of status types."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"
    DRAFT = "draft"
    PUBLISHED = "published"
    DELETED = "deleted"


@dataclass(frozen=True)
class Status:
    """
    Status value object representing state or condition.
    
    Attributes:
        value: Status value
        description: Optional description of the status
        metadata: Optional additional metadata
    """
    
    value: str
    description: Optional[str] = None
    metadata: Optional[dict] = None
    
    def __post_init__(self):
        """Validate status after initialization."""
        self._validate_value()
        self._validate_description()
        self._validate_metadata()
    
    def _validate_value(self):
        """Validate status value."""
        if not self.value or not self.value.strip():
            raise ValueError("Status value cannot be empty")
        
        # Check if value is a valid StatusType
        valid_values = {status.value for status in StatusType}
        if self.value.lower() not in valid_values:
            raise ValueError(f"Invalid status value: {self.value}")
    
    def _validate_description(self):
        """Validate description if provided."""
        if self.description is not None and not self.description.strip():
            raise ValueError("Description cannot be empty if provided")
    
    def _validate_metadata(self):
        """Validate metadata if provided."""
        if self.metadata is not None and not isinstance(self.metadata, dict):
            raise ValueError("Metadata must be a dictionary")
    
    @classmethod
    def from_enum(cls, status_type: StatusType, description: Optional[str] = None,
                  metadata: Optional[dict] = None) -> 'Status':
        """
        Create Status from StatusType enum.
        
        Args:
            status_type: StatusType enum value
            description: Optional description
            metadata: Optional metadata
            
        Returns:
            New Status object
        """
        return cls(status_type.value, description, metadata)
    
    @classmethod
    def active(cls, description: Optional[str] = None) -> 'Status':
        """Create active status."""
        return cls.from_enum(StatusType.ACTIVE, description)
    
    @classmethod
    def inactive(cls, description: Optional[str] = None) -> 'Status':
        """Create inactive status."""
        return cls.from_enum(StatusType.INACTIVE, description)
    
    @classmethod
    def pending(cls, description: Optional[str] = None) -> 'Status':
        """Create pending status."""
        return cls.from_enum(StatusType.PENDING, description)
    
    @classmethod
    def approved(cls, description: Optional[str] = None) -> 'Status':
        """Create approved status."""
        return cls.from_enum(StatusType.APPROVED, description)
    
    @classmethod
    def rejected(cls, description: Optional[str] = None) -> 'Status':
        """Create rejected status."""
        return cls.from_enum(StatusType.REJECTED, description)
    
    @classmethod
    def completed(cls, description: Optional[str] = None) -> 'Status':
        """Create completed status."""
        return cls.from_enum(StatusType.COMPLETED, description)
    
    @classmethod
    def cancelled(cls, description: Optional[str] = None) -> 'Status':
        """Create cancelled status."""
        return cls.from_enum(StatusType.CANCELLED, description)
    
    @property
    def is_active(self) -> bool:
        """Check if status is active."""
        return self.value.lower() == StatusType.ACTIVE.value
    
    @property
    def is_inactive(self) -> bool:
        """Check if status is inactive."""
        return self.value.lower() == StatusType.INACTIVE.value
    
    @property
    def is_pending(self) -> bool:
        """Check if status is pending."""
        return self.value.lower() == StatusType.PENDING.value
    
    @property
    def is_approved(self) -> bool:
        """Check if status is approved."""
        return self.value.lower() == StatusType.APPROVED.value
    
    @property
    def is_rejected(self) -> bool:
        """Check if status is rejected."""
        return self.value.lower() == StatusType.REJECTED.value
    
    @property
    def is_completed(self) -> bool:
        """Check if status is completed."""
        return self.value.lower() == StatusType.COMPLETED.value
    
    @property
    def is_cancelled(self) -> bool:
        """Check if status is cancelled."""
        return self.value.lower() == StatusType.CANCELLED.value
    
    @property
    def is_final(self) -> bool:
        """Check if status is final (cannot be changed)."""
        final_statuses = {
            StatusType.COMPLETED.value,
            StatusType.CANCELLED.value,
            StatusType.REJECTED.value,
            StatusType.DELETED.value
        }
        return self.value.lower() in final_statuses
    
    def can_transition_to(self, new_status: 'Status') -> bool:
        """
        Check if status can transition to new status.
        
        Args:
            new_status: Target status
            
        Returns:
            True if transition is allowed
        """
        if not isinstance(new_status, Status):
            return False
        
        # Define allowed transitions
        transitions = {
            StatusType.ACTIVE.value: {StatusType.INACTIVE.value, StatusType.SUSPENDED.value, StatusType.ARCHIVED.value},
            StatusType.INACTIVE.value: {StatusType.ACTIVE.value, StatusType.ARCHIVED.value},
            StatusType.PENDING.value: {StatusType.APPROVED.value, StatusType.REJECTED.value, StatusType.CANCELLED.value},
            StatusType.APPROVED.value: {StatusType.COMPLETED.value, StatusType.CANCELLED.value},
            StatusType.SUSPENDED.value: {StatusType.ACTIVE.value, StatusType.INACTIVE.value},
            StatusType.DRAFT.value: {StatusType.PUBLISHED.value, StatusType.DELETED.value},
            StatusType.PUBLISHED.value: {StatusType.ARCHIVED.value, StatusType.DELETED.value}
        }
        
        current_status = self.value.lower()
        target_status = new_status.value.lower()
        
        return target_status in transitions.get(current_status, set())
    
    def get_allowed_transitions(self) -> Set[str]:
        """
        Get all allowed transitions from current status.
        
        Returns:
            Set of allowed status values
        """
        transitions = {
            StatusType.ACTIVE.value: {StatusType.INACTIVE.value, StatusType.SUSPENDED.value, StatusType.ARCHIVED.value},
            StatusType.INACTIVE.value: {StatusType.ACTIVE.value, StatusType.ARCHIVED.value},
            StatusType.PENDING.value: {StatusType.APPROVED.value, StatusType.REJECTED.value, StatusType.CANCELLED.value},
            StatusType.APPROVED.value: {StatusType.COMPLETED.value, StatusType.CANCELLED.value},
            StatusType.SUSPENDED.value: {StatusType.ACTIVE.value, StatusType.INACTIVE.value},
            StatusType.DRAFT.value: {StatusType.PUBLISHED.value, StatusType.DELETED.value},
            StatusType.PUBLISHED.value: {StatusType.ARCHIVED.value, StatusType.DELETED.value}
        }
        
        return transitions.get(self.value.lower(), set())
    
    def __str__(self) -> str:
        """String representation of status."""
        if self.description:
            return f"{self.value} ({self.description})"
        return self.value
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Status(value='{self.value}', description='{self.description}', metadata={self.metadata})" 