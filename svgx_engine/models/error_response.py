"""
Unified Error Response Models for Arxos Platform

This module provides standardized error response models for consistent
error handling across the Arxos Platform.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import uuid


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"           # Informational errors
    MEDIUM = "medium"     # Standard errors
    HIGH = "high"         # Important errors
    CRITICAL = "critical" # Critical system errors


class ErrorCategory(str, Enum):
    """Error categories for classification."""
    VALIDATION = "validation"         # Input validation errors
    AUTHENTICATION = "authentication" # Authentication failures
    AUTHORIZATION = "authorization"   # Permission issues
    NOT_FOUND = "not_found"          # Resource not found
    CONFLICT = "conflict"            # Resource conflicts
    TIMEOUT = "timeout"              # Timeout errors
    RATE_LIMIT = "rate_limit"        # Rate limiting
    INTERNAL = "internal"            # Internal server errors
    EXTERNAL = "external"            # External service errors
    NETWORK = "network"              # Network issues
    DATABASE = "database"            # Database errors
    FILE_SYSTEM = "file_system"      # File system errors
    THIRD_PARTY = "third_party"      # Third-party service errors


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    
    error: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Application-specific error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    severity: ErrorSeverity = Field(ErrorSeverity.MEDIUM, description="Error severity level")
    category: ErrorCategory = Field(ErrorCategory.INTERNAL, description="Error category")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the error occurred")
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    error_id: Optional[str] = Field(None, description="Unique error identifier")
    suggestions: Optional[List[str]] = Field(None, description="Resolution suggestions")
    retry_after: Optional[int] = Field(None, description="Retry delay in seconds")
    
    def __init__(self, **data):
    """
    Perform __init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        if 'error_id' not in data:
            data['error_id'] = f"err_{uuid.uuid4().hex[:16]}"
        super().__init__(**data)


class ValidationErrorResponse(ErrorResponse):
    """Specialized error response for validation errors."""
    
    validation_errors: Optional[List[str]] = Field(None, description="List of validation errors")
    field_errors: Optional[Dict[str, List[str]]] = Field(None, description="Field-specific errors")
    
    def __init__(self, **data):
        data.setdefault('category', ErrorCategory.VALIDATION)
        data.setdefault('code', 'VALIDATION_ERROR')
        super().__init__(**data)


class AuthenticationErrorResponse(ErrorResponse):
    """Specialized error response for authentication failures."""
    
    auth_type: Optional[str] = Field(None, description="Authentication type")
    required_scopes: Optional[List[str]] = Field(None, description="Required scopes")
    
    def __init__(self, **data):
        data.setdefault('category', ErrorCategory.AUTHENTICATION)
        data.setdefault('code', 'AUTHENTICATION_ERROR')
        data.setdefault('severity', ErrorSeverity.HIGH)
        super().__init__(**data)


class AuthorizationErrorResponse(ErrorResponse):
    """Specialized error response for authorization issues."""
    
    required_permissions: Optional[List[str]] = Field(None, description="Required permissions")
    user_permissions: Optional[List[str]] = Field(None, description="User permissions")
    
    def __init__(self, **data):
        data.setdefault('category', ErrorCategory.AUTHORIZATION)
        data.setdefault('code', 'AUTHORIZATION_ERROR')
        data.setdefault('severity', ErrorSeverity.HIGH)
        super().__init__(**data)


class NotFoundErrorResponse(ErrorResponse):
    """Specialized error response for resource not found errors."""
    
    resource_type: Optional[str] = Field(None, description="Type of resource not found")
    resource_id: Optional[str] = Field(None, description="ID of resource not found")
    search_criteria: Optional[Dict[str, Any]] = Field(None, description="Search criteria used")
    
    def __init__(self, **data):
        data.setdefault('category', ErrorCategory.NOT_FOUND)
        data.setdefault('code', 'NOT_FOUND_ERROR')
        super().__init__(**data)


class ConflictErrorResponse(ErrorResponse):
    """Specialized error response for resource conflicts."""
    
    conflicting_resource: Optional[str] = Field(None, description="Conflicting resource")
    conflict_reason: Optional[str] = Field(None, description="Reason for conflict")
    
    def __init__(self, **data):
        data.setdefault('category', ErrorCategory.CONFLICT)
        data.setdefault('code', 'CONFLICT_ERROR')
        super().__init__(**data)


class RateLimitErrorResponse(ErrorResponse):
    """Specialized error response for rate limiting errors."""
    
    limit: Optional[int] = Field(None, description="Rate limit")
    remaining: Optional[int] = Field(None, description="Remaining requests")
    reset_time: Optional[datetime] = Field(None, description="When rate limit resets")
    
    def __init__(self, **data):
        data.setdefault('category', ErrorCategory.RATE_LIMIT)
        data.setdefault('code', 'RATE_LIMIT_ERROR')
        super().__init__(**data)


# Factory functions for creating error responses
def create_validation_error_response(
    error: str,
    validation_errors: Optional[List[str]] = None,
    field_errors: Optional[Dict[str, List[str]]] = None,
    request_id: Optional[str] = None,
    **kwargs
) -> ValidationErrorResponse:
    """Create a validation error response."""
    return ValidationErrorResponse(
        error=error,
        validation_errors=validation_errors,
        field_errors=field_errors,
        request_id=request_id,
        **kwargs
    )


def create_authentication_error_response(
    error: str,
    auth_type: Optional[str] = None,
    required_scopes: Optional[List[str]] = None,
    request_id: Optional[str] = None,
    **kwargs
) -> AuthenticationErrorResponse:
    """Create an authentication error response."""
    return AuthenticationErrorResponse(
        error=error,
        auth_type=auth_type,
        required_scopes=required_scopes,
        request_id=request_id,
        **kwargs
    )


def create_authorization_error_response(
    error: str,
    required_permissions: Optional[List[str]] = None,
    user_permissions: Optional[List[str]] = None,
    request_id: Optional[str] = None,
    **kwargs
) -> AuthorizationErrorResponse:
    """Create an authorization error response."""
    return AuthorizationErrorResponse(
        error=error,
        required_permissions=required_permissions,
        user_permissions=user_permissions,
        request_id=request_id,
        **kwargs
    )


def create_not_found_error_response(
    error: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    search_criteria: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    **kwargs
) -> NotFoundErrorResponse:
    """Create a not found error response."""
    return NotFoundErrorResponse(
        error=error,
        resource_type=resource_type,
        resource_id=resource_id,
        search_criteria=search_criteria,
        request_id=request_id,
        **kwargs
    )


def create_conflict_error_response(
    error: str,
    conflicting_resource: Optional[str] = None,
    conflict_reason: Optional[str] = None,
    request_id: Optional[str] = None,
    **kwargs
) -> ConflictErrorResponse:
    """Create a conflict error response."""
    return ConflictErrorResponse(
        error=error,
        conflicting_resource=conflicting_resource,
        conflict_reason=conflict_reason,
        request_id=request_id,
        **kwargs
    )


def create_rate_limit_error_response(
    error: str,
    limit: Optional[int] = None,
    remaining: Optional[int] = None,
    reset_time: Optional[datetime] = None,
    retry_after: Optional[int] = None,
    request_id: Optional[str] = None,
    **kwargs
) -> RateLimitErrorResponse:
    """Create a rate limit error response."""
    return RateLimitErrorResponse(
        error=error,
        limit=limit,
        remaining=remaining,
        reset_time=reset_time,
        retry_after=retry_after,
        request_id=request_id,
        **kwargs
    )


def create_general_error_response(
    error: str,
    code: str,
    category: ErrorCategory = ErrorCategory.INTERNAL,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    request_id: Optional[str] = None,
    **kwargs
) -> ErrorResponse:
    """Create a general error response."""
    return ErrorResponse(
        error=error,
        code=code,
        category=category,
        severity=severity,
        request_id=request_id,
        **kwargs
    )


def error_response_to_json_response(error_response: ErrorResponse, status_code: int = 400) -> Dict[str, Any]:
    """Convert ErrorResponse to JSON response format."""
    response_data = error_response.dict()
    
    # Add HTTP status code
    response_data['status_code'] = status_code
    
    return response_data 