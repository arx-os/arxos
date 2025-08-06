"""
Unified Error Handler for Arxos Platform

This module provides centralized error handling with FastAPI integration
and comprehensive error logging capabilities.
"""

import logging
import traceback
from typing import Dict, Any, Optional, Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from ..models.error_response import (
    ErrorResponse,
    ValidationErrorResponse,
    AuthenticationErrorResponse,
    AuthorizationErrorResponse,
    NotFoundErrorResponse,
    ConflictErrorResponse,
    RateLimitErrorResponse,
    create_validation_error_response,
    create_authentication_error_response,
    create_authorization_error_response,
    create_not_found_error_response,
    create_conflict_error_response,
    create_rate_limit_error_response,
    create_general_error_response,
    error_response_to_json_response,
    ErrorCategory,
    ErrorSeverity,
)
from .errors import (
    SVGXError,
    ValidationError as SVGXValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    SecurityError,
    ConfigurationError,
    PipelineError,
    ExportError,
    ImportError,
    PerformanceError,
    DatabaseError,
    NetworkError,
    CacheError,
)

# Configure logging
logger = logging.getLogger(__name__)


class UnifiedErrorHandler:
    """Centralized error handler for the Arxos Platform."""

    def __init__(self):
        self.logger = logger

    def handle_exception(
        self,
        exc: Exception,
        request: Optional[Request] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ErrorResponse:
        """Handle an exception and return a standardized error response."""

        # Extract request ID if available
        request_id = None
        if request and hasattr(request, "state"):
            request_id = getattr(request.state, "request_id", None)

        # Handle SVGX-specific exceptions
        if isinstance(exc, SVGXValidationError):
            return self._handle_validation_error(exc, request_id, context)
        elif isinstance(exc, AuthenticationError):
            return self._handle_authentication_error(exc, request_id, context)
        elif isinstance(exc, AuthorizationError):
            return self._handle_authorization_error(exc, request_id, context)
        elif isinstance(exc, ResourceNotFoundError):
            return self._handle_not_found_error(exc, request_id, context)
        elif isinstance(exc, SecurityError):
            return self._handle_security_error(exc, request_id, context)
        elif isinstance(exc, ConfigurationError):
            return self._handle_configuration_error(exc, request_id, context)
        elif isinstance(exc, PipelineError):
            return self._handle_pipeline_error(exc, request_id, context)
        elif isinstance(exc, ExportError):
            return self._handle_export_error(exc, request_id, context)
        elif isinstance(exc, ImportError):
            return self._handle_import_error(exc, request_id, context)
        elif isinstance(exc, PerformanceError):
            return self._handle_performance_error(exc, request_id, context)
        elif isinstance(exc, DatabaseError):
            return self._handle_database_error(exc, request_id, context)
        elif isinstance(exc, NetworkError):
            return self._handle_network_error(exc, request_id, context)
        elif isinstance(exc, CacheError):
            return self._handle_cache_error(exc, request_id, context)
        elif isinstance(exc, SVGXError):
            return self._handle_svgx_error(exc, request_id, context)

        # Handle FastAPI exceptions
        elif isinstance(exc, HTTPException):
            return self._handle_http_exception(exc, request_id, context)
        elif isinstance(exc, RequestValidationError):
            return self._handle_validation_error(exc, request_id, context)

        # Handle generic exceptions
        else:
            return self._handle_generic_error(exc, request_id, context)

    def _handle_validation_error(
        self,
        exc: Union[SVGXValidationError, RequestValidationError],
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> ValidationErrorResponse:
        """Handle validation errors."""

        if isinstance(exc, RequestValidationError):
            # FastAPI validation error
            validation_errors = []
            field_errors = {}

            for error in exc.errors():
                field = error.get("loc", ["unknown"])[-1]
                message = error.get("msg", "Validation error")
                validation_errors.append(f"{field}: {message}")

                if field not in field_errors:
                    field_errors[field] = []
                field_errors[field].append(message)

            error_message = "Request validation failed"
        else:
            # SVGX validation error
            validation_errors = [exc.message]
            field_errors = {exc.field: [exc.message]} if exc.field else {}
            error_message = exc.message

        error_response = create_validation_error_response(
            error=error_message,
            validation_errors=validation_errors,
            field_errors=field_errors,
            request_id=request_id,
            details=context,
        )

        self._log_error(error_response, exc)
        return error_response

    def _handle_authentication_error(
        self,
        exc: AuthenticationError,
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> AuthenticationErrorResponse:
        """Handle authentication errors."""

        error_response = create_authentication_error_response(
            error=exc.message,
            auth_type=exc.auth_context,
            request_id=request_id,
            details=context,
        )

        self._log_error(error_response, exc)
        return error_response

    def _handle_authorization_error(
        self,
        exc: AuthorizationError,
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> AuthorizationErrorResponse:
        """Handle authorization errors."""

        error_response = create_authorization_error_response(
            error=exc.message, request_id=request_id, details=context
        )

        self._log_error(error_response, exc)
        return error_response

    def _handle_not_found_error(
        self,
        exc: ResourceNotFoundError,
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> NotFoundErrorResponse:
        """Handle not found errors."""

        error_response = create_not_found_error_response(
            error=exc.message,
            resource_type=exc.resource_type,
            resource_id=exc.resource_id,
            request_id=request_id,
            details=context,
        )

        self._log_error(error_response, exc)
        return error_response

    def _handle_security_error(
        self,
        exc: SecurityError,
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> ErrorResponse:
        """Handle security errors."""

        error_response = create_general_error_response(
            error=exc.message,
            code="SECURITY_ERROR",
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH,
            request_id=request_id,
            details=context,
        )

        self._log_error(error_response, exc)
        return error_response

    def _handle_configuration_error(
        self,
        exc: ConfigurationError,
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> ErrorResponse:
        """Handle configuration errors."""

        error_response = create_general_error_response(
            error=exc.message,
            code="CONFIGURATION_ERROR",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.HIGH,
            request_id=request_id,
            details=context,
        )

        self._log_error(error_response, exc)
        return error_response

    def _handle_pipeline_error(
        self,
        exc: PipelineError,
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> ErrorResponse:
        """Handle pipeline errors."""

        error_response = create_general_error_response(
            error=exc.message,
            code="PIPELINE_ERROR",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.MEDIUM,
            request_id=request_id,
            details=context,
        )

        self._log_error(error_response, exc)
        return error_response

    def _handle_export_error(
        self,
        exc: ExportError,
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> ErrorResponse:
        """Handle export errors."""

        error_response = create_general_error_response(
            error=exc.message,
            code="EXPORT_ERROR",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.MEDIUM,
            request_id=request_id,
            details=context,
        )

        self._log_error(error_response, exc)
        return error_response

    def _handle_import_error(
        self,
        exc: ImportError,
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> ErrorResponse:
        """Handle import errors."""

        error_response = create_general_error_response(
            error=exc.message,
            code="IMPORT_ERROR",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.MEDIUM,
            request_id=request_id,
            details=context,
        )

        self._log_error(error_response, exc)
        return error_response

    def _handle_performance_error(
        self,
        exc: PerformanceError,
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> ErrorResponse:
        """Handle performance errors."""

        error_response = create_general_error_response(
            error=exc.message,
            code="PERFORMANCE_ERROR",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.MEDIUM,
            request_id=request_id,
            details=context,
        )

        self._log_error(error_response, exc)
        return error_response

    def _handle_database_error(
        self,
        exc: DatabaseError,
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> ErrorResponse:
        """Handle database errors."""

        error_response = create_general_error_response(
            error=exc.message,
            code="DATABASE_ERROR",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            request_id=request_id,
            details=context,
        )

        self._log_error(error_response, exc)
        return error_response

    def _handle_network_error(
        self,
        exc: NetworkError,
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> ErrorResponse:
        """Handle network errors."""

        error_response = create_general_error_response(
            error=exc.message,
            code="NETWORK_ERROR",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            request_id=request_id,
            details=context,
        )

        self._log_error(error_response, exc)
        return error_response

    def _handle_cache_error(
        self,
        exc: CacheError,
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> ErrorResponse:
        """Handle cache errors."""

        error_response = create_general_error_response(
            error=exc.message,
            code="CACHE_ERROR",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.LOW,
            request_id=request_id,
            details=context,
        )

        self._log_error(error_response, exc)
        return error_response

    def _handle_svgx_error(
        self,
        exc: SVGXError,
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> ErrorResponse:
        """Handle generic SVGX errors."""

        error_response = create_general_error_response(
            error=exc.message,
            code="SVGX_ERROR",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.MEDIUM,
            request_id=request_id,
            details=context,
        )

        self._log_error(error_response, exc)
        return error_response

    def _handle_http_exception(
        self,
        exc: HTTPException,
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> ErrorResponse:
        """Handle HTTP exceptions."""

        # Map HTTP status codes to error categories
        status_to_category = {
            400: ErrorCategory.VALIDATION,
            401: ErrorCategory.AUTHENTICATION,
            403: ErrorCategory.AUTHORIZATION,
            404: ErrorCategory.NOT_FOUND,
            409: ErrorCategory.CONFLICT,
            429: ErrorCategory.RATE_LIMIT,
            500: ErrorCategory.INTERNAL,
            502: ErrorCategory.EXTERNAL,
            503: ErrorCategory.EXTERNAL,
            504: ErrorCategory.TIMEOUT,
        }

        category = status_to_category.get(exc.status_code, ErrorCategory.INTERNAL)
        severity = (
            ErrorSeverity.HIGH if exc.status_code >= 500 else ErrorSeverity.MEDIUM
        )

        error_response = create_general_error_response(
            error=exc.detail,
            code=f"HTTP_{exc.status_code}",
            category=category,
            severity=severity,
            request_id=request_id,
            details=context,
        )

        self._log_error(error_response, exc)
        return error_response

    def _handle_generic_error(
        self,
        exc: Exception,
        request_id: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> ErrorResponse:
        """Handle generic exceptions."""

        error_response = create_general_error_response(
            error=str(exc),
            code="INTERNAL_ERROR",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.CRITICAL,
            request_id=request_id,
            details=context,
        )

        self._log_error(error_response, exc)
        return error_response

    def _log_error(self, error_response: ErrorResponse, exc: Exception):
        """Log error with appropriate level based on severity."""

        log_level = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }.get(error_response.severity, logging.ERROR)

        self.logger.log(
            log_level,
            f"Error {error_response.error_id}: {error_response.error}",
            extra={
                "error_id": error_response.error_id,
                "request_id": error_response.request_id,
                "category": error_response.category,
                "severity": error_response.severity,
                "code": error_response.code,
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            },
        )


# Global error handler instance
error_handler = UnifiedErrorHandler()


# FastAPI exception handlers
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    error_response = error_handler.handle_exception(exc, request)
    response_data = error_response_to_json_response(error_response, exc.status_code)
    return JSONResponse(content=response_data, status_code=exc.status_code)


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation exceptions."""
    error_response = error_handler.handle_exception(exc, request)
    response_data = error_response_to_json_response(error_response, 422)
    return JSONResponse(content=response_data, status_code=422)


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    error_response = error_handler.handle_exception(exc, request)
    response_data = error_response_to_json_response(error_response, 500)
    return JSONResponse(content=response_data, status_code=500)


# Convenience function for handling exceptions in route handlers
def handle_exception(
    exc: Exception,
    request: Optional[Request] = None,
    context: Optional[Dict[str, Any]] = None,
) -> ErrorResponse:
    """Handle an exception and return a standardized error response."""
    return error_handler.handle_exception(exc, request, context)
