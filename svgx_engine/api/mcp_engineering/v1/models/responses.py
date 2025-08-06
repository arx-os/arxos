#!/usr/bin/env python3
"""
Response Models for MCP-Engineering API

Response models for the MCP-Engineering integration API endpoints.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ValidationResult(BaseModel):
    """Result of engineering validation."""

    is_valid: bool = Field(..., description="Whether the element is valid")
    confidence_score: float = Field(
        ..., description="Confidence score of the validation"
    )
    system_type: str = Field(..., description="Engineering system type")
    validation_level: str = Field(..., description="Validation level used")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    suggestions: List[str] = Field(
        default_factory=list, description="Validation suggestions"
    )
    validation_time: float = Field(..., description="Time taken for validation")
    timestamp: datetime = Field(..., description="Validation timestamp")
    element_id: str = Field(..., description="Element identifier")
    validation_details: Dict[str, Any] = Field(
        default_factory=dict, description="Detailed validation information"
    )


class ComplianceViolation(BaseModel):
    """Code compliance violation."""

    code_section: str = Field(..., description="Code section reference")
    description: str = Field(..., description="Violation description")
    level: str = Field(..., description="Violation level (critical, warning, info)")
    standard: str = Field(..., description="Code standard (NEC, ASHRAE, IPC, IBC)")
    element_id: str = Field(..., description="Element identifier")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Violation details"
    )


class ComplianceResult(BaseModel):
    """Result of code compliance checking."""

    is_compliant: bool = Field(..., description="Whether the element is compliant")
    confidence_score: float = Field(
        ..., description="Confidence score of compliance check"
    )
    violations: List[ComplianceViolation] = Field(
        default_factory=list, description="Compliance violations"
    )
    warnings: List[str] = Field(default_factory=list, description="Compliance warnings")
    suggestions: List[str] = Field(
        default_factory=list, description="Compliance suggestions"
    )
    compliance_time: float = Field(..., description="Time taken for compliance check")
    timestamp: datetime = Field(..., description="Compliance check timestamp")
    element_id: str = Field(..., description="Element identifier")
    standards_checked: List[str] = Field(
        default_factory=list, description="Standards checked"
    )
    compliance_details: Dict[str, Any] = Field(
        default_factory=dict, description="Detailed compliance information"
    )


class SystemImpact(BaseModel):
    """Cross-system impact information."""

    source_system: str = Field(..., description="Source system")
    target_system: str = Field(..., description="Target system")
    impact_level: str = Field(
        ..., description="Impact level (critical, high, medium, low, none)"
    )
    interaction_type: str = Field(
        ..., description="Interaction type (conflict, dependency, enhancement, neutral)"
    )
    description: str = Field(..., description="Impact description")
    details: Dict[str, Any] = Field(default_factory=dict, description="Impact details")
    confidence_score: float = Field(
        ..., description="Confidence score of impact analysis"
    )


class CrossSystemAnalysisResult(BaseModel):
    """Result of cross-system analysis."""

    element_id: str = Field(..., description="Element identifier")
    system_type: str = Field(..., description="System type")
    impacts: List[SystemImpact] = Field(
        default_factory=list, description="System impacts"
    )
    conflicts: List[SystemImpact] = Field(
        default_factory=list, description="System conflicts"
    )
    dependencies: List[SystemImpact] = Field(
        default_factory=list, description="System dependencies"
    )
    enhancements: List[SystemImpact] = Field(
        default_factory=list, description="System enhancements"
    )
    analysis_time: float = Field(..., description="Time taken for analysis")
    timestamp: datetime = Field(..., description="Analysis timestamp")
    confidence_score: float = Field(..., description="Confidence score of analysis")
    analysis_details: Dict[str, Any] = Field(
        default_factory=dict, description="Detailed analysis information"
    )


class EngineeringSuggestion(BaseModel):
    """Engineering suggestion."""

    suggestion_id: str = Field(..., description="Suggestion identifier")
    suggestion_type: str = Field(..., description="Suggestion type")
    priority: str = Field(
        ..., description="Suggestion priority (critical, high, medium, low)"
    )
    title: str = Field(..., description="Suggestion title")
    description: str = Field(..., description="Suggestion description")
    rationale: str = Field(..., description="Suggestion rationale")
    implementation_details: Dict[str, Any] = Field(
        default_factory=dict, description="Implementation details"
    )
    estimated_impact: Dict[str, Any] = Field(
        default_factory=dict, description="Estimated impact"
    )
    confidence_score: float = Field(..., description="Confidence score of suggestion")
    system_type: str = Field(..., description="System type")
    element_id: str = Field(..., description="Element identifier")
    timestamp: datetime = Field(..., description="Suggestion timestamp")


class MCPEngineeringResult(BaseModel):
    """Comprehensive MCP-Engineering analysis result."""

    intelligence_analysis: Optional[Dict[str, Any]] = Field(
        None, description="MCP intelligence analysis"
    )
    engineering_validation: Optional[ValidationResult] = Field(
        None, description="Engineering validation result"
    )
    code_compliance: Optional[ComplianceResult] = Field(
        None, description="Code compliance result"
    )
    cross_system_analysis: Optional[CrossSystemAnalysisResult] = Field(
        None, description="Cross-system analysis result"
    )
    suggestions: List[EngineeringSuggestion] = Field(
        default_factory=list, description="Engineering suggestions"
    )
    timestamp: datetime = Field(..., description="Analysis timestamp")
    element_id: str = Field(..., description="Element identifier")
    processing_time: float = Field(..., description="Total processing time")
    confidence_score: float = Field(..., description="Overall confidence score")
    errors: List[str] = Field(default_factory=list, description="Processing errors")


class ValidationResponse(BaseModel):
    """Response for validation endpoints."""

    success: bool = Field(..., description="Whether the validation was successful")
    result: MCPEngineeringResult = Field(..., description="Validation result")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class BatchValidationResponse(BaseModel):
    """Response for batch validation endpoints."""

    success: bool = Field(
        ..., description="Whether the batch validation was successful"
    )
    results: List[MCPEngineeringResult] = Field(
        ..., description="Batch validation results"
    )
    total_elements: int = Field(..., description="Total number of elements processed")
    total_processing_time: float = Field(..., description="Total processing time")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class SuggestionResponse(BaseModel):
    """Response for suggestion endpoints."""

    success: bool = Field(
        ..., description="Whether the suggestion generation was successful"
    )
    suggestions: List[EngineeringSuggestion] = Field(
        ..., description="Generated suggestions"
    )
    total_suggestions: int = Field(..., description="Total number of suggestions")
    critical_suggestions: int = Field(..., description="Number of critical suggestions")
    high_priority_suggestions: int = Field(
        ..., description="Number of high priority suggestions"
    )
    generation_time: float = Field(..., description="Suggestion generation time")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class ComplianceResponse(BaseModel):
    """Response for compliance endpoints."""

    success: bool = Field(
        ..., description="Whether the compliance check was successful"
    )
    result: ComplianceResult = Field(..., description="Compliance check result")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class CrossSystemResponse(BaseModel):
    """Response for cross-system analysis endpoints."""

    success: bool = Field(
        ..., description="Whether the cross-system analysis was successful"
    )
    result: CrossSystemAnalysisResult = Field(
        ..., description="Cross-system analysis result"
    )
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Response timestamp"
    )


class HealthResponse(BaseModel):
    """Response for health check endpoints."""

    status: str = Field(..., description="Service status")
    services: Dict[str, bool] = Field(
        ..., description="Individual service health status"
    )
    config: Dict[str, Any] = Field(..., description="Service configuration")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Health check timestamp"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Error timestamp"
    )
    request_id: Optional[str] = Field(
        None, description="Request identifier for tracking"
    )
