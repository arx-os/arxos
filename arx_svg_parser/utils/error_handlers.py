"""
Centralized Error Handlers for Arxos Platform
Provides standardized error handling, logging, and error response generation
"""

import logging
import traceback
from typing import Any, Dict, Optional, Type, List
from datetime import datetime
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import uuid

from .response_helpers import ResponseHelper

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handler for consistent error processing"""
    
    def __init__(self):
        self.error_mapping: Dict[Type[Exception], Dict[str, Any]] = {
            ValueError: {
                "status_code": 400,
                "error_code": "INVALID_VALUE",
                "log_level": logging.WARNING
            },
            ValidationError: {
                "status_code": 422,
                "error_code": "VALIDATION_ERROR",
                "log_level": logging.WARNING
            },
            KeyError: {
                "status_code": 400,
                "error_code": "MISSING_KEY",
                "log_level": logging.WARNING
            },
            FileNotFoundError: {
                "status_code": 404,
                "error_code": "FILE_NOT_FOUND",
                "log_level": logging.WARNING
            },
            PermissionError: {
                "status_code": 403,
                "error_code": "PERMISSION_DENIED",
                "log_level": logging.WARNING
            },
            TimeoutError: {
                "status_code": 408,
                "error_code": "TIMEOUT",
                "log_level": logging.WARNING
            },
            ConnectionError: {
                "status_code": 503,
                "error_code": "SERVICE_UNAVAILABLE",
                "log_level": logging.ERROR
            }
        }
    
    def handle_exception(
        self,
        exc: Exception,
        request: Optional[Request] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """
        Handle an exception and return appropriate response
        
        Args:
            exc: The exception to handle
            request: FastAPI request object (optional)
            context: Additional context information (optional)
            
        Returns:
            JSONResponse with appropriate error details
        """
        # Generate unique error ID for tracking
        error_id = str(uuid.uuid4())
        
        # Get error configuration
        error_config = self._get_error_config(exc)
        
        # Log the error
        self._log_error(exc, error_id, request, context, error_config["log_level"])
        
        # Create error response
        return self._create_error_response(exc, error_id, error_config, context)
    
    def _get_error_config(self, exc: Exception) -> Dict[str, Any]:
        """Get error configuration for exception type"""
        exc_type = type(exc)
        
        # Check for exact match
        if exc_type in self.error_mapping:
            return self.error_mapping[exc_type]
        
        # Check for base class matches
        for base_type, config in self.error_mapping.items():
            if isinstance(exc, base_type):
                return config
        
        # Default configuration
        return {
            "status_code": 500,
            "error_code": "INTERNAL_ERROR",
            "log_level": logging.ERROR
        }
    
    def _log_error(
        self,
        exc: Exception,
        error_id: str,
        request: Optional[Request],
        context: Optional[Dict[str, Any]],
        log_level: int
    ):
        """Log error with context"""
        log_data = {
            "error_id": error_id,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if request:
            log_data.update({
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            })
        
        if context:
            log_data["context"] = context
        
        # Log with appropriate level
        if log_level == logging.ERROR:
            logger.error(f"Error {error_id}: {str(exc)}", extra=log_data, exc_info=True)
        elif log_level == logging.WARNING:
            logger.warning(f"Warning {error_id}: {str(exc)}", extra=log_data)
        else:
            logger.info(f"Info {error_id}: {str(exc)}", extra=log_data)
    
    def _create_error_response(
        self,
        exc: Exception,
        error_id: str,
        error_config: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> JSONResponse:
        """Create standardized error response"""
        details = {
            "error_id": error_id,
            "exception_type": type(exc).__name__
        }
        
        if context:
            details["context"] = context
        
        # Add validation errors for Pydantic validation errors
        if isinstance(exc, ValidationError):
            details["validation_errors"] = self._format_validation_errors(exc)
        
        return ResponseHelper.error_response(
            message=str(exc),
            error_code=error_config["error_code"],
            status_code=error_config["status_code"],
            details=details
        )
    
    def _format_validation_errors(self, exc: ValidationError) -> List[str]:
        """Format Pydantic validation errors"""
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            errors.append(f"{field}: {message}")
        return errors

# Global error handler instance
error_handler = ErrorHandler()

def handle_exception(
    exc: Exception,
    request: Optional[Request] = None,
    context: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Convenience function to handle exceptions
    
    Args:
        exc: The exception to handle
        request: FastAPI request object (optional)
        context: Additional context information (optional)
        
    Returns:
        JSONResponse with appropriate error details
    """
    return error_handler.handle_exception(exc, request, context)

def log_error(
    message: str,
    exc: Optional[Exception] = None,
    context: Optional[Dict[str, Any]] = None,
    level: int = logging.ERROR
):
    """
    Convenience function to log errors with context
    
    Args:
        message: Error message
        exc: Exception object (optional)
        context: Additional context (optional)
        level: Logging level
    """
    log_data = {
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if exc:
        log_data.update({
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)
        })
    
    if context:
        log_data["context"] = context
    
    if level == logging.ERROR:
        logger.error(message, extra=log_data, exc_info=bool(exc))
    elif level == logging.WARNING:
        logger.warning(message, extra=log_data)
    elif level == logging.INFO:
        logger.info(message, extra=log_data)
    else:
        logger.debug(message, extra=log_data)

# FastAPI exception handlers
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException"""
    return ResponseHelper.error_response(
        message=exc.detail,
        error_code="HTTP_ERROR",
        status_code=exc.status_code
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI RequestValidationError"""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")
    
    return ResponseHelper.error_response(
        message="Request validation failed",
        error_code="VALIDATION_ERROR",
        status_code=422,
        validation_errors=errors
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions"""
    return handle_exception(exc, request)

# Error response convenience functions
def validation_error_response(
    message: str = "Validation failed",
    validation_errors: Optional[List[str]] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create validation error response"""
    return ResponseHelper.error_response(
        message=message,
        error_code="VALIDATION_ERROR",
        status_code=422,
        validation_errors=validation_errors,
        details=details
    )

def not_found_response(
    message: str = "Resource not found",
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None
) -> JSONResponse:
    """Create not found response"""
    details = {}
    if resource_type:
        details["resource_type"] = resource_type
    if resource_id:
        details["resource_id"] = resource_id
        
    return ResponseHelper.error_response(
        message=message,
        error_code="NOT_FOUND",
        status_code=404,
        details=details
    )

def unauthorized_response(
    message: str = "Authentication required",
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create unauthorized response"""
    return ResponseHelper.error_response(
        message=message,
        error_code="UNAUTHORIZED",
        status_code=401,
        details=details
    )

def forbidden_response(
    message: str = "Access denied",
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create forbidden response"""
    return ResponseHelper.error_response(
        message=message,
        error_code="FORBIDDEN",
        status_code=403,
        details=details
    )

def server_error_response(
    message: str = "Internal server error",
    error_id: Optional[str] = None
) -> JSONResponse:
    """Create server error response"""
    details = {"error_id": error_id} if error_id else None
    
    return ResponseHelper.error_response(
        message=message,
        error_code="INTERNAL_ERROR",
        status_code=500,
        details=details
    ) 