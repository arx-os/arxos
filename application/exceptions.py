"""
Application Layer Exceptions

This module contains application-specific exceptions that provide
clean error handling and logging for the application layer.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime


class ApplicationError(Exception):
    """Base exception for all application layer errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "APPLICATION_ERROR"
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        
        # Log the error
        self._log_error()
    
    def _log_error(self):
        """Log the error with structured information."""
        logger = logging.getLogger(__name__)
        logger.error(
            f"Application Error: {self.error_code} - {self.message}",
            extra={
                "error_code": self.error_code,
                "details": self.details,
                "timestamp": self.timestamp.isoformat()
            }
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class ValidationError(ApplicationError):
    """Exception raised when input validation fails."""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field, "value": str(value) if value is not None else None}
        )


class BusinessRuleError(ApplicationError):
    """Exception raised when business rules are violated."""
    
    def __init__(self, message: str, rule: str = None, context: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code="BUSINESS_RULE_ERROR",
            details={"rule": rule, "context": context or {}}
        )


class ResourceNotFoundError(ApplicationError):
    """Exception raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str, message: str = None):
        if not message:
            message = f"{resource_type} with ID '{resource_id}' not found"
        
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class DuplicateResourceError(ApplicationError):
    """Exception raised when attempting to create a duplicate resource."""
    
    def __init__(self, resource_type: str, identifier: str, message: str = None):
        if not message:
            message = f"{resource_type} with identifier '{identifier}' already exists"
        
        super().__init__(
            message=message,
            error_code="DUPLICATE_RESOURCE",
            details={"resource_type": resource_type, "identifier": identifier}
        )


class PermissionError(ApplicationError):
    """Exception raised when user lacks required permissions."""
    
    def __init__(self, required_permission: str, user_id: str = None, message: str = None):
        if not message:
            message = f"Permission '{required_permission}' required"
        
        super().__init__(
            message=message,
            error_code="PERMISSION_ERROR",
            details={"required_permission": required_permission, "user_id": user_id}
        )


class ServiceUnavailableError(ApplicationError):
    """Exception raised when a required service is unavailable."""
    
    def __init__(self, service_name: str, message: str = None):
        if not message:
            message = f"Service '{service_name}' is unavailable"
        
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details={"service_name": service_name}
        )


class ConfigurationError(ApplicationError):
    """Exception raised when there's a configuration issue."""
    
    def __init__(self, config_key: str, message: str = None):
        if not message:
            message = f"Configuration error for key '{config_key}'"
        
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={"config_key": config_key}
        )


class TransactionError(ApplicationError):
    """Exception raised when a database transaction fails."""
    
    def __init__(self, operation: str, message: str = None):
        if not message:
            message = f"Transaction failed for operation '{operation}'"
        
        super().__init__(
            message=message,
            error_code="TRANSACTION_ERROR",
            details={"operation": operation}
        )


class CacheError(ApplicationError):
    """Exception raised when cache operations fail."""
    
    def __init__(self, operation: str, key: str = None, message: str = None):
        if not message:
            message = f"Cache operation '{operation}' failed"
        
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details={"operation": operation, "key": key}
        )


class EventProcessingError(ApplicationError):
    """Exception raised when event processing fails."""
    
    def __init__(self, event_type: str, event_id: str = None, message: str = None):
        if not message:
            message = f"Event processing failed for event type '{event_type}'"
        
        super().__init__(
            message=message,
            error_code="EVENT_PROCESSING_ERROR",
            details={"event_type": event_type, "event_id": event_id}
        )


class RateLimitError(ApplicationError):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(self, limit_type: str, retry_after: int = None, message: str = None):
        if not message:
            message = f"Rate limit exceeded for '{limit_type}'"
        
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details={"limit_type": limit_type, "retry_after": retry_after}
        )


class DataIntegrityError(ApplicationError):
    """Exception raised when data integrity constraints are violated."""
    
    def __init__(self, constraint: str, message: str = None):
        if not message:
            message = f"Data integrity constraint '{constraint}' violated"
        
        super().__init__(
            message=message,
            error_code="DATA_INTEGRITY_ERROR",
            details={"constraint": constraint}
        )


# Error handling utilities
def handle_application_error(func):
    """Decorator to handle application errors and provide consistent error responses."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ApplicationError as e:
            # Re-raise application errors as-is
            raise
        except Exception as e:
            # Convert unexpected errors to application errors
            logger = logging.getLogger(__name__)
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            
            raise ApplicationError(
                message="An unexpected error occurred",
                error_code="INTERNAL_ERROR",
                details={"original_error": str(e), "function": func.__name__}
            )
    return wrapper


def create_error_response(error: ApplicationError) -> Dict[str, Any]:
    """Create a standardized error response from an application error."""
    return {
        "success": False,
        "error": error.to_dict()
    }


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """Validate that required fields are present in the data."""
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None or str(data[field]).strip() == "":
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(
            message=f"Missing required fields: {', '.join(missing_fields)}",
            details={"missing_fields": missing_fields}
        )


def validate_field_type(value: Any, expected_type: type, field_name: str) -> None:
    """Validate that a field has the expected type."""
    if not isinstance(value, expected_type):
        raise ValidationError(
            message=f"Field '{field_name}' must be of type {expected_type.__name__}",
            field=field_name,
            value=value
        )


def validate_string_length(value: str, field_name: str, min_length: int = 0, max_length: int = None) -> None:
    """Validate string length constraints."""
    if not isinstance(value, str):
        raise ValidationError(
            message=f"Field '{field_name}' must be a string",
            field=field_name,
            value=value
        )
    
    if len(value) < min_length:
        raise ValidationError(
            message=f"Field '{field_name}' must be at least {min_length} characters long",
            field=field_name,
            value=value
        )
    
    if max_length and len(value) > max_length:
        raise ValidationError(
            message=f"Field '{field_name}' must be no more than {max_length} characters long",
            field=field_name,
            value=value
        ) 