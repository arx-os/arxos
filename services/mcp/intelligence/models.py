#!/usr/bin/env python3
"""
Intelligence Layer Data Models

Defines the data structures for the MCP Intelligence Layer including
context analysis, suggestions, alerts, and validation results.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class SuggestionType(str, Enum):
    """Types of intelligent suggestions"""

    PLACEMENT = "placement"
    CODE_COMPLIANCE = "code_compliance"
    SAFETY = "safety"
    ACCESSIBILITY = "accessibility"
    EFFICIENCY = "efficiency"
    BEST_PRACTICE = "best_practice"
    ALTERNATIVE = "alternative"


class AlertSeverity(str, Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationStatus(str, Enum):
    """Validation result status"""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    UNKNOWN = "unknown"


class UserIntent(BaseModel):
    """User intent analysis result"""

    action: str = Field(..., description="The action the user is performing")
    object_type: Optional[str] = Field(
        None, description="Type of object being manipulated"
    )
    location: Optional[Dict[str, Any]] = Field(None, description="Location information")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in intent detection"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ModelContext(BaseModel):
    """Current model state context"""

    building_type: Optional[str] = Field(None, description="Type of building")
    jurisdiction: Optional[str] = Field(None, description="Building code jurisdiction")
    floor_count: Optional[int] = Field(None, description="Number of floors")
    total_area: Optional[float] = Field(None, description="Total building area")
    occupancy_type: Optional[str] = Field(None, description="Occupancy classification")
    elements: List[Dict[str, Any]] = Field(
        default_factory=list, description="Building elements"
    )
    systems: List[Dict[str, Any]] = Field(
        default_factory=list, description="Building systems"
    )
    violations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Current violations"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Suggestion(BaseModel):
    """Intelligent suggestion for user"""

    id: UUID = Field(default_factory=uuid4)
    type: SuggestionType = Field(..., description="Type of suggestion")
    title: str = Field(..., description="Suggestion title")
    description: str = Field(..., description="Detailed description")
    code_reference: Optional[str] = Field(None, description="Relevant code section")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in suggestion"
    )
    priority: int = Field(default=1, ge=1, le=5, description="Priority level (1-5)")
    action_required: bool = Field(
        default=False, description="Whether action is required"
    )
    estimated_impact: Optional[str] = Field(
        None, description="Estimated impact of suggestion"
    )
    alternatives: List[Dict[str, Any]] = Field(
        default_factory=list, description="Alternative solutions"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Alert(BaseModel):
    """Proactive alert for potential issues"""

    id: UUID = Field(default_factory=uuid4)
    severity: AlertSeverity = Field(..., description="Alert severity")
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Detailed description")
    category: str = Field(..., description="Alert category")
    affected_elements: List[str] = Field(
        default_factory=list, description="Affected elements"
    )
    code_reference: Optional[str] = Field(None, description="Relevant code section")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Improvement(BaseModel):
    """Suggested model improvement"""

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., description="Improvement title")
    description: str = Field(..., description="Detailed description")
    category: str = Field(..., description="Improvement category")
    impact_score: float = Field(..., ge=0.0, le=1.0, description="Impact score")
    effort_required: str = Field(..., description="Effort required (low/medium/high)")
    cost_impact: Optional[str] = Field(None, description="Cost impact")
    time_impact: Optional[str] = Field(None, description="Time impact")
    implementation_steps: List[str] = Field(
        default_factory=list, description="Implementation steps"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Conflict(BaseModel):
    """Detected conflict between elements"""

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., description="Conflict title")
    description: str = Field(..., description="Detailed description")
    severity: AlertSeverity = Field(..., description="Conflict severity")
    elements_involved: List[str] = Field(
        ..., description="Elements involved in conflict"
    )
    conflict_type: str = Field(..., description="Type of conflict")
    code_reference: Optional[str] = Field(None, description="Relevant code section")
    resolution_suggestions: List[str] = Field(
        default_factory=list, description="Resolution suggestions"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CodeReference(BaseModel):
    """Building code reference"""

    code: str = Field(..., description="Code identifier (e.g., IFC 2018)")
    section: str = Field(..., description="Code section")
    title: str = Field(..., description="Section title")
    description: str = Field(..., description="Code description")
    requirements: List[str] = Field(..., description="Specific requirements")
    exceptions: List[str] = Field(default_factory=list, description="Exceptions")
    related_sections: List[str] = Field(
        default_factory=list, description="Related sections"
    )
    jurisdiction: str = Field(..., description="Jurisdiction")
    effective_date: Optional[datetime] = Field(None, description="Effective date")


class ValidationResult(BaseModel):
    """Validation result"""

    status: ValidationStatus = Field(..., description="Validation status")
    message: str = Field(..., description="Validation message")
    code_references: List[CodeReference] = Field(
        default_factory=list, description="Code references"
    )
    violations: List[Dict[str, Any]] = Field(
        default_factory=list, description="Violations found"
    )
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="Warnings")
    suggestions: List[Suggestion] = Field(
        default_factory=list, description="Suggestions"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Validation confidence")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IntelligenceContext(BaseModel):
    """Complete intelligence context"""

    user_intent: Optional[UserIntent] = Field(None, description="User intent analysis")
    model_context: Optional[ModelContext] = Field(None, description="Model context")
    suggestions: List[Suggestion] = Field(
        default_factory=list, description="Intelligent suggestions"
    )
    alerts: List[Alert] = Field(default_factory=list, description="Proactive alerts")
    improvements: List[Improvement] = Field(
        default_factory=list, description="Model improvements"
    )
    conflicts: List[Conflict] = Field(
        default_factory=list, description="Detected conflicts"
    )
    validation_result: Optional[ValidationResult] = Field(
        None, description="Validation result"
    )
    code_references: List[CodeReference] = Field(
        default_factory=list, description="Relevant code references"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @validator("suggestions")
    def sort_suggestions_by_priority(cls, v):
        """Sort suggestions by priority and confidence"""
        return sorted(v, key=lambda x: (x.priority, x.confidence), reverse=True)

    @validator("alerts")
    def sort_alerts_by_severity(cls, v):
        """Sort alerts by severity"""
        severity_order = {
            AlertSeverity.CRITICAL: 4,
            AlertSeverity.ERROR: 3,
            AlertSeverity.WARNING: 2,
            AlertSeverity.INFO: 1,
        }
        return sorted(v, key=lambda x: severity_order[x.severity], reverse=True)
