#!/usr/bin/env python3
"""
MCP Engineering Result Domain Model

Domain model for MCP-Engineering integration results.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MCPEngineeringResult:
    """Comprehensive MCP-Engineering analysis result."""

    intelligence_analysis: Optional[Dict[str, Any]]
    engineering_validation: Optional[Dict[str, Any]]
    code_compliance: Optional[Dict[str, Any]]
    cross_system_analysis: Optional[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    timestamp: datetime
    element_id: str
    processing_time: float
    confidence_score: float
    errors: Optional[List[str]] = None

    def __post_init__(self):
        """Post-initialization validation."""
        if self.errors is None:
            self.errors = []

    def is_successful(self) -> bool:
        """Check if the analysis was successful."""
        return len(self.errors) == 0

    def get_critical_issues(self) -> List[str]:
        """Get critical issues from the analysis."""
        critical_issues = []

        # Check for critical validation errors
        if self.engineering_validation:
            validation_errors = self.engineering_validation.get("errors", [])
            critical_issues.extend(
                [f"Validation: {error}" for error in validation_errors]
            )

        # Check for critical compliance violations
        if self.code_compliance:
            violations = self.code_compliance.get("violations", [])
            for violation in violations:
                if hasattr(violation, "level") and violation.level == "critical":
                    critical_issues.append(f"Compliance: {violation.description}")

        return critical_issues

    def get_warnings(self) -> List[str]:
        """Get warnings from the analysis."""
        warnings = []

        # Check for validation warnings
        if self.engineering_validation:
            validation_warnings = self.engineering_validation.get("warnings", [])
            warnings.extend(
                [f"Validation: {warning}" for warning in validation_warnings]
            )

        # Check for compliance warnings
        if self.code_compliance:
            compliance_warnings = self.code_compliance.get("warnings", [])
            warnings.extend(
                [f"Compliance: {warning}" for warning in compliance_warnings]
            )

        return warnings

    def get_suggestions(self) -> List[Dict[str, Any]]:
        """Get all suggestions from the analysis."""
        return self.suggestions

    def get_critical_suggestions(self) -> List[Dict[str, Any]]:
        """Get critical priority suggestions."""
        return [s for s in self.suggestions if s.get("priority") == "critical"]

    def get_high_priority_suggestions(self) -> List[Dict[str, Any]]:
        """Get high priority suggestions."""
        return [s for s in self.suggestions if s.get("priority") == "high"]

    def get_system_type(self) -> str:
        """Get the primary system type from the analysis."""
        if self.engineering_validation:
            return self.engineering_validation.get("system_type", "unknown")
        return "unknown"

    def get_overall_confidence(self) -> float:
        """Get overall confidence score."""
        return self.confidence_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "intelligence_analysis": self.intelligence_analysis,
            "engineering_validation": self.engineering_validation,
            "code_compliance": self.code_compliance,
            "cross_system_analysis": self.cross_system_analysis,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat(),
            "element_id": self.element_id,
            "processing_time": self.processing_time,
            "confidence_score": self.confidence_score,
            "errors": self.errors,
            "is_successful": self.is_successful(),
            "critical_issues": self.get_critical_issues(),
            "warnings": self.get_warnings(),
            "system_type": self.get_system_type(),
        }
