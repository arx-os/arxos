#!/usr/bin/env python3
"""
Intelligence Layer API Routes

FastAPI routes for the MCP Intelligence Layer providing context analysis,
suggestions, and proactive monitoring capabilities.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from .intelligence_service import MCPIntelligenceService
from .models import (
    IntelligenceContext,
    Suggestion,
    Alert,
    Improvement,
    Conflict,
    ValidationResult,
    CodeReference,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/intelligence", tags=["intelligence"])


# Request/Response Models
class ContextRequest(BaseModel):
    """Request for context analysis"""

    object_type: str = Field(..., description="Type of object being placed")
    location: Dict[str, Any] = Field(..., description="Location information")
    model_state: Optional[Dict[str, Any]] = Field(
        None, description="Current model state"
    )


class ContextResponse(BaseModel):
    """Response for context analysis"""

    context: IntelligenceContext = Field(
        ..., description="Complete intelligence context"
    )
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")


class SuggestionRequest(BaseModel):
    """Request for suggestions"""

    action: str = Field(..., description="User action being performed")
    model_state: Dict[str, Any] = Field(..., description="Current model state")
    object_type: Optional[str] = Field(None, description="Type of object")
    location: Optional[Dict[str, Any]] = Field(None, description="Location information")


class SuggestionResponse(BaseModel):
    """Response for suggestions"""

    suggestions: List[Suggestion] = Field(..., description="List of suggestions")
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")


class ValidationRequest(BaseModel):
    """Request for real-time validation"""

    model_changes: Dict[str, Any] = Field(..., description="Model changes to validate")
    model_state: Optional[Dict[str, Any]] = Field(
        None, description="Current model state"
    )


class ValidationResponse(BaseModel):
    """Response for validation"""

    validation_result: ValidationResult = Field(..., description="Validation result")
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")


class CodeReferenceRequest(BaseModel):
    """Request for code reference"""

    requirement: str = Field(..., description="Code requirement identifier")
    jurisdiction: Optional[str] = Field(None, description="Jurisdiction")


class CodeReferenceResponse(BaseModel):
    """Response for code reference"""

    code_reference: CodeReference = Field(..., description="Code reference")
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")


class MonitoringRequest(BaseModel):
    """Request for proactive monitoring"""

    model_state: Dict[str, Any] = Field(..., description="Current model state")


class MonitoringResponse(BaseModel):
    """Response for proactive monitoring"""

    alerts: List[Alert] = Field(..., description="List of alerts")
    conflicts: List[Conflict] = Field(..., description="List of conflicts")
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")


class ImprovementRequest(BaseModel):
    """Request for improvement suggestions"""

    model_state: Dict[str, Any] = Field(..., description="Current model state")


class ImprovementResponse(BaseModel):
    """Response for improvement suggestions"""

    improvements: List[Improvement] = Field(..., description="List of improvements")
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")


# Dependency injection
def get_intelligence_service() -> MCPIntelligenceService:
    """Get intelligence service instance"""
    return MCPIntelligenceService()


# API Routes
@router.post("/context", response_model=ContextResponse)
async def get_context(
    request: ContextRequest,
    intelligence_service: MCPIntelligenceService = Depends(get_intelligence_service),
):
    """
    Get comprehensive context for object placement

    Provides intelligent context including code requirements, suggestions,
    alerts, and validation for object placement.
    """
    try:
        logger.info(f"Getting context for {request.object_type}")

        context = await intelligence_service.provide_context(
            object_type=request.object_type,
            location=request.location,
            model_state=request.model_state,
        )

        return ContextResponse(
            context=context,
            success=True,
            message=f"Context provided for {request.object_type}",
        )

    except Exception as e:
        logger.error(f"Error getting context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")


@router.post("/suggestions", response_model=SuggestionResponse)
async def get_suggestions(
    request: SuggestionRequest,
    intelligence_service: MCPIntelligenceService = Depends(get_intelligence_service),
):
    """
    Get intelligent suggestions based on user action and model state

    Provides context-aware suggestions for object placement, code compliance,
    safety improvements, and best practices.
    """
    try:
        logger.info(f"Getting suggestions for action: {request.action}")

        suggestions = await intelligence_service.generate_suggestions(
            action=request.action,
            model_state=request.model_state,
            object_type=request.object_type,
        )

        return SuggestionResponse(
            suggestions=suggestions,
            success=True,
            message=f"Generated {len(suggestions)} suggestions",
        )

    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get suggestions: {str(e)}"
        )


@router.post("/validate-realtime", response_model=ValidationResponse)
async def validate_realtime(
    request: ValidationRequest,
    intelligence_service: MCPIntelligenceService = Depends(get_intelligence_service),
):
    """
    Provide real-time validation feedback for model changes

    Validates model changes against building codes and provides
    immediate feedback with suggestions for any issues.
    """
    try:
        logger.info("Performing real-time validation")

        validation_result = await intelligence_service.validate_realtime(
            model_changes=request.model_changes, model_state=request.model_state
        )

        return ValidationResponse(
            validation_result=validation_result,
            success=True,
            message=f"Real-time validation completed: {validation_result.status}",
        )

    except Exception as e:
        logger.error(f"Error in real-time validation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate: {str(e)}")


@router.get("/code-reference/{requirement}", response_model=CodeReferenceResponse)
async def get_code_reference(
    requirement: str,
    jurisdiction: Optional[str] = None,
    intelligence_service: MCPIntelligenceService = Depends(get_intelligence_service),
):
    """
    Get specific code reference for a requirement

    Retrieves detailed information about building code requirements
    including specific sections, requirements, and exceptions.
    """
    try:
        logger.info(f"Getting code reference for: {requirement}")

        code_reference = await intelligence_service.get_code_reference(
            requirement=requirement, jurisdiction=jurisdiction
        )

        return CodeReferenceResponse(
            code_reference=code_reference,
            success=True,
            message=f"Retrieved code reference: {code_reference.code} {code_reference.section}",
        )

    except Exception as e:
        logger.error(f"Error getting code reference: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get code reference: {str(e)}"
        )


@router.post("/monitor", response_model=MonitoringResponse)
async def monitor_proactive(
    request: MonitoringRequest,
    intelligence_service: MCPIntelligenceService = Depends(get_intelligence_service),
):
    """
    Proactively monitor model for potential issues

    Monitors the model for potential conflicts, safety issues, and
    compliance problems before they become violations.
    """
    try:
        logger.info("Performing proactive monitoring")

        alerts = await intelligence_service.monitor_proactive(
            model_state=request.model_state
        )

        # Get conflicts (this would be a separate method in the service)
        conflicts = []  # Placeholder for now

        return MonitoringResponse(
            alerts=alerts,
            conflicts=conflicts,
            success=True,
            message=f"Generated {len(alerts)} alerts and {len(conflicts)} conflicts",
        )

    except Exception as e:
        logger.error(f"Error in proactive monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to monitor: {str(e)}")


@router.post("/improvements", response_model=ImprovementResponse)
async def get_improvements(
    request: ImprovementRequest,
    intelligence_service: MCPIntelligenceService = Depends(get_intelligence_service),
):
    """
    Get model improvement suggestions

    Provides suggestions for improving the building model including
    safety enhancements, efficiency improvements, and best practices.
    """
    try:
        logger.info("Getting improvement suggestions")

        improvements = await intelligence_service.suggest_improvements(
            model_state=request.model_state
        )

        return ImprovementResponse(
            improvements=improvements,
            success=True,
            message=f"Generated {len(improvements)} improvement suggestions",
        )

    except Exception as e:
        logger.error(f"Error getting improvements: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get improvements: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for intelligence layer"""
    return {
        "status": "healthy",
        "service": "intelligence",
        "message": "Intelligence layer is operational",
    }


@router.get("/status")
async def get_status():
    """Get intelligence layer status"""
    return {
        "service": "intelligence",
        "version": "1.0.0",
        "components": ["context_analyzer", "suggestion_engine", "proactive_monitor"],
        "capabilities": [
            "context_analysis",
            "intelligent_suggestions",
            "real_time_validation",
            "proactive_monitoring",
            "code_references",
            "improvement_suggestions",
        ],
    }
