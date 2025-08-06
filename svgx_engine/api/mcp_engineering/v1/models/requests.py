#!/usr/bin/env python3
"""
Request Models for MCP-Engineering API

Request models for the MCP-Engineering integration API endpoints.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DesignElement(BaseModel):
    """Design element data model."""

    id: str = Field(..., description="Unique identifier for the design element")
    system_type: str = Field(
        ...,
        description="Engineering system type (electrical, hvac, plumbing, structural)",
    )
    element_type: str = Field(..., description="Type of design element")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Element properties"
    )
    geometry: Optional[Dict[str, Any]] = Field(
        None, description="Element geometry data"
    )
    location: Optional[Dict[str, Any]] = Field(
        None, description="Element location data"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    timestamp: Optional[datetime] = Field(
        None, description="Element creation timestamp"
    )


class DesignElementRequest(BaseModel):
    """Request model for design element validation."""

    element: DesignElement = Field(..., description="Design element to validate")
    validation_level: Optional[str] = Field(
        "standard", description="Validation level (basic, standard, comprehensive)"
    )
    include_suggestions: Optional[bool] = Field(
        True, description="Include AI-powered suggestions"
    )
    include_compliance: Optional[bool] = Field(
        True, description="Include code compliance checking"
    )
    include_cross_system: Optional[bool] = Field(
        True, description="Include cross-system analysis"
    )


class BatchValidationRequest(BaseModel):
    """Request model for batch validation of multiple design elements."""

    elements: List[DesignElement] = Field(
        ..., description="List of design elements to validate"
    )
    validation_level: Optional[str] = Field(
        "standard", description="Validation level for all elements"
    )
    include_suggestions: Optional[bool] = Field(
        True, description="Include AI-powered suggestions"
    )
    include_compliance: Optional[bool] = Field(
        True, description="Include code compliance checking"
    )
    include_cross_system: Optional[bool] = Field(
        True, description="Include cross-system analysis"
    )
    parallel_processing: Optional[bool] = Field(
        True, description="Enable parallel processing for batch validation"
    )


class HealthCheckRequest(BaseModel):
    """Request model for health check."""

    include_details: Optional[bool] = Field(
        False, description="Include detailed health information"
    )
    check_services: Optional[List[str]] = Field(
        None, description="Specific services to check"
    )


class SuggestionRequest(BaseModel):
    """Request model for generating engineering suggestions."""

    element: DesignElement = Field(
        ..., description="Design element for suggestion generation"
    )
    suggestion_types: Optional[List[str]] = Field(
        None, description="Types of suggestions to generate"
    )
    priority_levels: Optional[List[str]] = Field(
        None, description="Priority levels to include"
    )
    max_suggestions: Optional[int] = Field(
        10, description="Maximum number of suggestions to return"
    )


class ComplianceCheckRequest(BaseModel):
    """Request model for code compliance checking."""

    element: DesignElement = Field(
        ..., description="Design element to check for compliance"
    )
    standards: Optional[List[str]] = Field(
        None, description="Specific standards to check (NEC, ASHRAE, IPC, IBC)"
    )
    include_details: Optional[bool] = Field(
        True, description="Include detailed compliance information"
    )
    strict_mode: Optional[bool] = Field(
        False, description="Enable strict compliance checking"
    )


class CrossSystemAnalysisRequest(BaseModel):
    """Request model for cross-system analysis."""

    element: DesignElement = Field(
        ..., description="Design element for cross-system analysis"
    )
    target_systems: Optional[List[str]] = Field(
        None, description="Target systems to analyze"
    )
    include_impacts: Optional[bool] = Field(True, description="Include impact analysis")
    include_conflicts: Optional[bool] = Field(
        True, description="Include conflict detection"
    )
    include_dependencies: Optional[bool] = Field(
        True, description="Include dependency analysis"
    )
