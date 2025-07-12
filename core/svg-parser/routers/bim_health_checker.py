"""
BIM Health Checker API Router

This router provides RESTful API endpoints for BIM health checking and validation
operations, including floorplan validation, fix application, history tracking,
and performance monitoring.

Endpoints:
- POST /bim-health/validate - Validate a floorplan
- POST /bim-health/apply-fixes - Apply fixes to validation results
- GET /bim-health/history/{floorplan_id} - Get validation history
- GET /bim-health/metrics - Get performance metrics
- GET /bim-health/profiles - Get behavior profiles
- POST /bim-health/profiles - Add behavior profile
- GET /bim-health/health - Health check
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from pydantic import BaseModel, Field

from services.bim_health_checker import (
    BIMHealthCheckerService,
    IssueType,
    ValidationStatus,
    FixType,
    BehaviorProfile
)

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/bim-health", tags=["BIM Health Checker"])

# Initialize service
bim_health_service = BIMHealthCheckerService()


# Pydantic models for request/response
class ValidationRequest(BaseModel):
    """Request model for floorplan validation."""
    floorplan_id: str = Field(..., description="Unique floorplan identifier")
    floorplan_data: Dict[str, Any] = Field(..., description="Floorplan data to validate")
    auto_apply_fixes: bool = Field(False, description="Automatically apply safe fixes")


class ValidationResponse(BaseModel):
    """Response model for validation operation."""
    validation_id: str = Field(..., description="Unique validation identifier")
    floorplan_id: str = Field(..., description="Floorplan identifier")
    status: str = Field(..., description="Validation status")
    total_objects: int = Field(..., description="Total objects validated")
    issues_found: int = Field(..., description="Number of issues found")
    auto_fixes_applied: int = Field(..., description="Number of auto fixes applied")
    suggested_fixes: int = Field(..., description="Number of suggested fixes")
    manual_fixes_required: int = Field(..., description="Number of manual fixes required")
    validation_time: float = Field(..., description="Validation time in seconds")
    timestamp: str = Field(..., description="Validation timestamp")
    summary: Dict[str, Any] = Field(..., description="Validation summary")


class IssueResponse(BaseModel):
    """Response model for validation issues."""
    issue_id: str = Field(..., description="Unique issue identifier")
    issue_type: str = Field(..., description="Type of issue")
    object_id: str = Field(..., description="Object identifier")
    severity: str = Field(..., description="Issue severity")
    description: str = Field(..., description="Issue description")
    location: Dict[str, Any] = Field(..., description="Issue location")
    current_value: Any = Field(None, description="Current value")
    suggested_value: Any = Field(None, description="Suggested value")
    fix_type: str = Field(..., description="Fix type")
    confidence: float = Field(..., description="Fix confidence (0.0 to 1.0)")
    timestamp: str = Field(..., description="Issue timestamp")
    context: Dict[str, Any] = Field(..., description="Issue context")


class ValidationWithIssuesResponse(BaseModel):
    """Response model for validation with detailed issues."""
    validation: ValidationResponse = Field(..., description="Validation result")
    issues: List[IssueResponse] = Field(..., description="List of validation issues")


class ApplyFixesRequest(BaseModel):
    """Request model for applying fixes."""
    validation_id: str = Field(..., description="Validation result identifier")
    fix_selections: Dict[str, str] = Field(..., description="Issue ID to fix action mapping")


class ApplyFixesResponse(BaseModel):
    """Response model for fix application."""
    validation_id: str = Field(..., description="Validation result identifier")
    applied_fixes: int = Field(..., description="Number of fixes applied")
    failed_fixes: int = Field(..., description="Number of failed fixes")
    total_issues: int = Field(..., description="Total number of issues")
    status: str = Field(..., description="Fix application status")


class ValidationHistoryResponse(BaseModel):
    """Response model for validation history."""
    floorplan_id: str = Field(..., description="Floorplan identifier")
    validations: List[Dict[str, Any]] = Field(..., description="List of validation results")
    total_validations: int = Field(..., description="Total number of validations")


class MetricsResponse(BaseModel):
    """Response model for performance metrics."""
    metrics: Dict[str, Any] = Field(..., description="Performance metrics")
    behavior_profiles: int = Field(..., description="Number of behavior profiles")
    database_size: int = Field(..., description="Database size in bytes")


class BehaviorProfileRequest(BaseModel):
    """Request model for adding behavior profile."""
    profile_id: str = Field(..., description="Unique profile identifier")
    object_type: str = Field(..., description="Object type")
    category: str = Field(..., description="Object category")
    properties: Dict[str, Any] = Field(..., description="Profile properties")
    validation_rules: Dict[str, Any] = Field(..., description="Validation rules")
    fix_suggestions: Dict[str, Any] = Field(..., description="Fix suggestions")


class BehaviorProfileResponse(BaseModel):
    """Response model for behavior profile."""
    profile_id: str = Field(..., description="Profile identifier")
    object_type: str = Field(..., description="Object type")
    category: str = Field(..., description="Object category")
    properties: Dict[str, Any] = Field(..., description="Profile properties")
    validation_rules: Dict[str, Any] = Field(..., description="Validation rules")
    fix_suggestions: Dict[str, Any] = Field(..., description="Fix suggestions")


@router.post("/validate", response_model=ValidationWithIssuesResponse)
async def validate_floorplan(request: ValidationRequest):
    """
    Validate a floorplan for BIM health issues.
    
    This endpoint performs comprehensive BIM validation including:
    - Missing behavior profile detection
    - Invalid coordinate validation and correction
    - Unlinked symbol detection and linking
    - Stale object metadata identification
    - Context-aware fix suggestions
    
    Args:
        request: Validation request with floorplan data
        
    Returns:
        Validation result with detailed issues and fix suggestions
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        logger.info(f"Starting BIM validation for floorplan {request.floorplan_id}")
        
        # Validate request data
        if not request.floorplan_id:
            raise HTTPException(status_code=400, detail="Floorplan ID is required")
        
        if not request.floorplan_data:
            raise HTTPException(status_code=400, detail="Floorplan data is required")
        
        # Perform validation
        result = bim_health_service.validate_floorplan(
            floorplan_id=request.floorplan_id,
            floorplan_data=request.floorplan_data
        )
        
        # Convert issues to response format
        issues_response = []
        for issue in result.issues:
            issues_response.append(IssueResponse(
                issue_id=issue.issue_id,
                issue_type=issue.issue_type.value,
                object_id=issue.object_id,
                severity=issue.severity,
                description=issue.description,
                location=issue.location,
                current_value=issue.current_value,
                suggested_value=issue.suggested_value,
                fix_type=issue.fix_type.value,
                confidence=issue.confidence,
                timestamp=issue.timestamp.isoformat(),
                context=issue.context
            ))
        
        # Create validation response
        validation_response = ValidationResponse(
            validation_id=result.validation_id,
            floorplan_id=result.floorplan_id,
            status=result.status.value,
            total_objects=result.total_objects,
            issues_found=result.issues_found,
            auto_fixes_applied=result.auto_fixes_applied,
            suggested_fixes=result.suggested_fixes,
            manual_fixes_required=result.manual_fixes_required,
            validation_time=result.validation_time,
            timestamp=result.timestamp.isoformat(),
            summary=result.summary
        )
        
        logger.info(f"BIM validation completed for {request.floorplan_id}: {result.issues_found} issues found")
        
        return ValidationWithIssuesResponse(
            validation=validation_response,
            issues=issues_response
        )
        
    except Exception as e:
        logger.error(f"BIM validation failed for floorplan {request.floorplan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.post("/apply-fixes", response_model=ApplyFixesResponse)
async def apply_fixes(request: ApplyFixesRequest):
    """
    Apply selected fixes to a validation result.
    
    This endpoint allows applying fixes to validation issues including:
    - Auto fixes (applied automatically during validation)
    - Suggested fixes (user-approved fixes)
    - Manual fixes (requiring user intervention)
    
    Args:
        request: Fix application request with selections
        
    Returns:
        Fix application result with statistics
        
    Raises:
        HTTPException: If fix application fails
    """
    try:
        logger.info(f"Applying fixes for validation {request.validation_id}")
        
        # Validate request data
        if not request.validation_id:
            raise HTTPException(status_code=400, detail="Validation ID is required")
        
        if not request.fix_selections:
            raise HTTPException(status_code=400, detail="Fix selections are required")
        
        # Apply fixes
        result = bim_health_service.apply_fixes(
            validation_id=request.validation_id,
            fix_selections=request.fix_selections
        )
        
        logger.info(f"Fix application completed for {request.validation_id}: {result['applied_fixes']} fixes applied")
        
        return ApplyFixesResponse(**result)
        
    except ValueError as e:
        logger.error(f"Fix application failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Fix application failed for {request.validation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Fix application failed: {str(e)}")


@router.get("/history/{floorplan_id}", response_model=ValidationHistoryResponse)
async def get_validation_history(floorplan_id: str, limit: int = 50):
    """
    Get validation history for a floorplan.
    
    This endpoint provides detailed history of BIM validations including:
    - Validation timestamps and status
    - Issue counts and fix statistics
    - Performance metrics and validation scores
    
    Args:
        floorplan_id: Floorplan identifier
        limit: Maximum number of results to return (default: 50)
        
    Returns:
        Validation history for the floorplan
        
    Raises:
        HTTPException: If history retrieval fails
    """
    try:
        logger.info(f"Getting validation history for floorplan {floorplan_id}")
        
        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")
        
        history = bim_health_service.get_validation_history(floorplan_id, limit)
        
        return ValidationHistoryResponse(
            floorplan_id=floorplan_id,
            validations=history,
            total_validations=len(history)
        )
        
    except Exception as e:
        logger.error(f"Failed to get validation history for {floorplan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get BIM health checker performance metrics.
    
    This endpoint provides comprehensive performance metrics including:
    - Total validations and success rates
    - Issues detected and fix application statistics
    - Average validation times and system resource usage
    - Behavior profile statistics
    
    Returns:
        Performance metrics and system statistics
        
    Raises:
        HTTPException: If metrics retrieval fails
    """
    try:
        logger.info("Getting BIM health checker metrics")
        
        metrics = bim_health_service.get_metrics()
        
        return MetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")


@router.get("/profiles", response_model=List[BehaviorProfileResponse])
async def get_behavior_profiles():
    """
    Get all behavior profiles.
    
    This endpoint provides access to all behavior profiles used for
    BIM validation including validation rules and fix suggestions.
    
    Returns:
        List of behavior profiles
        
    Raises:
        HTTPException: If profile retrieval fails
    """
    try:
        logger.info("Getting behavior profiles")
        
        profiles = bim_health_service.get_behavior_profiles()
        
        return [BehaviorProfileResponse(**profile) for profile in profiles]
        
    except Exception as e:
        logger.error(f"Failed to get behavior profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Profile retrieval failed: {str(e)}")


@router.post("/profiles", response_model=BehaviorProfileResponse)
async def add_behavior_profile(request: BehaviorProfileRequest):
    """
    Add a new behavior profile.
    
    This endpoint allows adding custom behavior profiles for BIM validation
    including validation rules and fix suggestions.
    
    Args:
        request: Behavior profile to add
        
    Returns:
        Added behavior profile
        
    Raises:
        HTTPException: If profile addition fails
    """
    try:
        logger.info(f"Adding behavior profile {request.profile_id}")
        
        # Validate request data
        if not request.profile_id:
            raise HTTPException(status_code=400, detail="Profile ID is required")
        
        if not request.object_type:
            raise HTTPException(status_code=400, detail="Object type is required")
        
        # Create behavior profile
        profile = BehaviorProfile(
            profile_id=request.profile_id,
            object_type=request.object_type,
            category=request.category,
            properties=request.properties,
            validation_rules=request.validation_rules,
            fix_suggestions=request.fix_suggestions
        )
        
        # Add profile
        bim_health_service.add_behavior_profile(profile)
        
        logger.info(f"Behavior profile {request.profile_id} added successfully")
        
        return BehaviorProfileResponse(**request.dict())
        
    except Exception as e:
        logger.error(f"Failed to add behavior profile {request.profile_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Profile addition failed: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the BIM health checker service.
    
    Returns:
        Service health status
    """
    try:
        # Basic health check
        metrics = bim_health_service.get_metrics()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "bim_health_checker",
            "database_accessible": True,
            "metrics_available": bool(metrics),
            "behavior_profiles": metrics.get('behavior_profiles', 0)
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "service": "bim_health_checker",
                "error": str(e)
            }
        )


@router.get("/issues/types")
async def get_issue_types():
    """
    Get all available issue types.
    
    Returns:
        List of issue types with descriptions
    """
    issue_types = [
        {
            "type": IssueType.MISSING_BEHAVIOR_PROFILE.value,
            "name": "Missing Behavior Profile",
            "description": "Object missing required behavior profile",
            "severity": "medium",
            "auto_fixable": True
        },
        {
            "type": IssueType.INVALID_COORDINATES.value,
            "name": "Invalid Coordinates",
            "description": "Object coordinates are invalid or out of bounds",
            "severity": "high",
            "auto_fixable": True
        },
        {
            "type": IssueType.UNLINKED_SYMBOL.value,
            "name": "Unlinked Symbol",
            "description": "Object missing required symbol link",
            "severity": "medium",
            "auto_fixable": False
        },
        {
            "type": IssueType.STALE_METADATA.value,
            "name": "Stale Metadata",
            "description": "Object metadata is outdated",
            "severity": "low",
            "auto_fixable": False
        },
        {
            "type": IssueType.DUPLICATE_OBJECT.value,
            "name": "Duplicate Object",
            "description": "Duplicate object detected",
            "severity": "high",
            "auto_fixable": False
        },
        {
            "type": IssueType.INVALID_SYMBOL.value,
            "name": "Invalid Symbol",
            "description": "Object has invalid or missing symbol",
            "severity": "medium",
            "auto_fixable": False
        },
        {
            "type": IssueType.MISSING_REQUIRED_FIELDS.value,
            "name": "Missing Required Fields",
            "description": "Object missing required fields",
            "severity": "high",
            "auto_fixable": False
        },
        {
            "type": IssueType.COORDINATE_OUT_OF_BOUNDS.value,
            "name": "Coordinate Out of Bounds",
            "description": "Object coordinates are outside valid bounds",
            "severity": "high",
            "auto_fixable": True
        }
    ]
    
    return {"issue_types": issue_types}


@router.get("/fixes/types")
async def get_fix_types():
    """
    Get all available fix types.
    
    Returns:
        List of fix types with descriptions
    """
    fix_types = [
        {
            "type": FixType.AUTO_FIX.value,
            "name": "Auto Fix",
            "description": "Automatically applied during validation",
            "requires_user_approval": False
        },
        {
            "type": FixType.SUGGESTED_FIX.value,
            "name": "Suggested Fix",
            "description": "Suggested fix requiring user approval",
            "requires_user_approval": True
        },
        {
            "type": FixType.MANUAL_FIX.value,
            "name": "Manual Fix",
            "description": "Requires manual user intervention",
            "requires_user_approval": True
        },
        {
            "type": FixType.IGNORE.value,
            "name": "Ignore",
            "description": "Ignore the issue",
            "requires_user_approval": True
        }
    ]
    
    return {"fix_types": fix_types}


# Error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with detailed error information."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )


@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with logging."""
    logger.error(f"Unhandled exception in BIM health API: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    ) 