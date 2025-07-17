"""
SVGX Engine - Error Handling System

Comprehensive error handling with proper exception classes,
error codes, and structured error responses.
"""

import traceback
import logging
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Error codes for SVGX Engine."""
    # General errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    
    # Parser errors
    PARSE_ERROR = "PARSE_ERROR"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    MALFORMED_SVGX = "MALFORMED_SVGX"
    UNSUPPORTED_ELEMENT = "UNSUPPORTED_ELEMENT"
    
    # Runtime errors
    RUNTIME_ERROR = "RUNTIME_ERROR"
    EVALUATION_ERROR = "EVALUATION_ERROR"
    BEHAVIOR_ERROR = "BEHAVIOR_ERROR"
    PHYSICS_ERROR = "PHYSICS_ERROR"
    
    # Compiler errors
    COMPILATION_ERROR = "COMPILATION_ERROR"
    EXPORT_ERROR = "EXPORT_ERROR"
    FORMAT_ERROR = "FORMAT_ERROR"
    
    # Performance errors
    PERFORMANCE_ERROR = "PERFORMANCE_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    MEMORY_ERROR = "MEMORY_ERROR"
    
    # Security errors
    SECURITY_ERROR = "SECURITY_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    AUTHORIZATION_ERROR = "AUTHORIZATION_ERROR"
    INPUT_VALIDATION_ERROR = "INPUT_VALIDATION_ERROR"
    
    # Database errors
    DATABASE_ERROR = "DATABASE_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    QUERY_ERROR = "QUERY_ERROR"
    
    # Service errors
    SERVICE_ERROR = "SERVICE_ERROR"
    INTEGRATION_ERROR = "INTEGRATION_ERROR"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Context information for errors."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class SVGXError(Exception):
    """Base exception for SVGX Engine."""
    
    def __init__(self, message: str, error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 context: Optional[ErrorContext] = None,
                 cause: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.context = context or ErrorContext()
        self.cause = cause
        self.timestamp = datetime.now()
        
        # Log the error
        self._log_error()
    
    def _log_error(self):
        """Log the error with appropriate level."""
        log_data = {
            'error_code': self.error_code.value,
            'severity': self.severity.value,
            'message': self.message,
            'context': self.context.__dict__ if self.context else None,
            'cause': str(self.cause) if self.cause else None
        }
        
        if self.severity == ErrorSeverity.CRITICAL:
            logger.critical("SVGX Critical Error", **log_data)
        elif self.severity == ErrorSeverity.HIGH:
            logger.error("SVGX High Severity Error", **log_data)
        elif self.severity == ErrorSeverity.MEDIUM:
            logger.warning("SVGX Medium Severity Error", **log_data)
        else:
            logger.info("SVGX Low Severity Error", **log_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            'error_code': self.error_code.value,
            'message': self.message,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context.__dict__ if self.context else None,
            'cause': str(self.cause) if self.cause else None
        }


class ValidationError(SVGXError):
    """Validation error."""
    
    def __init__(self, message: str, field: Optional[str] = None,
                 value: Optional[Any] = None, context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        self.field = field
        self.value = value


class ParseError(SVGXError):
    """SVGX parsing error."""
    
    def __init__(self, message: str, line: Optional[int] = None, column: Optional[int] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.PARSE_ERROR,
            severity=ErrorSeverity.HIGH,
            context=context
        )
        self.line = line
        self.column = column


class RuntimeError(SVGXError):
    """Runtime execution error."""
    
    def __init__(self, message: str, operation: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.RUNTIME_ERROR,
            severity=ErrorSeverity.HIGH,
            context=context
        )
        self.operation = operation


class PerformanceError(SVGXError):
    """Performance-related error."""
    
    def __init__(self, message: str, duration_ms: Optional[float] = None,
                 threshold_ms: Optional[float] = None, context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.PERFORMANCE_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        self.duration_ms = duration_ms
        self.threshold_ms = threshold_ms


class SecurityError(SVGXError):
    """Security-related error."""
    
    def __init__(self, message: str, security_event: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.SECURITY_ERROR,
            severity=ErrorSeverity.HIGH,
            context=context
        )
        self.security_event = security_event


class CompilationError(SVGXError):
    """Compilation error."""
    
    def __init__(self, message: str, target_format: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.COMPILATION_ERROR,
            severity=ErrorSeverity.HIGH,
            context=context
        )
        self.target_format = target_format


class DatabaseError(SVGXError):
    """Database-related error."""
    
    def __init__(self, message: str, operation: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            severity=ErrorSeverity.HIGH,
            context=context
        )
        self.operation = operation


class PersistenceError(SVGXError):
    """Persistence-related error."""
    
    def __init__(self, message: str, operation: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            severity=ErrorSeverity.HIGH,
            context=context
        )
        self.operation = operation


class PersistenceExportError(SVGXError):
    """Persistence export-related error."""
    
    def __init__(self, message: str, export_type: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.EXPORT_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        self.export_type = export_type


class ServiceError(SVGXError):
    """Service-related error."""
    
    def __init__(self, message: str, service_name: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.SERVICE_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        self.service_name = service_name


class JobError(SVGXError):
    """Job-related error."""
    
    def __init__(self, message: str, job_id: Optional[str] = None,
                 job_type: Optional[str] = None, context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.SERVICE_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        self.job_id = job_id
        self.job_type = job_type


class ExportError(SVGXError):
    """Export-related error."""
    
    def __init__(self, message: str, format: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.EXPORT_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        self.format = format


class AdvancedExportError(SVGXError):
    """Advanced export-related error."""
    
    def __init__(self, message: str, export_type: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.EXPORT_ERROR,
            severity=ErrorSeverity.HIGH,
            context=context
        )
        self.export_type = export_type


class ImportError(SVGXError):
    """Import-related error."""
    
    def __init__(self, message: str, format: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.INTEGRATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        self.format = format


class CacheError(SVGXError):
    """Cache-related error."""
    
    def __init__(self, message: str, cache_operation: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.SERVICE_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        self.cache_operation = cache_operation


class MetadataError(SVGXError):
    """Metadata-related error."""
    
    def __init__(self, message: str, metadata_type: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        self.metadata_type = metadata_type


class SymbolError(SVGXError):
    """Symbol-related error."""
    
    def __init__(self, message: str, symbol_id: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        self.symbol_id = symbol_id


class GenerationError(SVGXError):
    """Code generation error."""
    
    def __init__(self, message: str, generation_type: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.COMPILATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        self.generation_type = generation_type


class RenderingError(SVGXError):
    """Rendering-related error."""
    
    def __init__(self, message: str, render_type: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.SERVICE_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        self.render_type = render_type


class SchemaError(SVGXError):
    """Schema validation error."""
    
    def __init__(self, message: str, schema_type: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        self.schema_type = schema_type


class TelemetryError(SVGXError):
    """Telemetry-related error."""
    
    def __init__(self, message: str, telemetry_type: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.SERVICE_ERROR,
            severity=ErrorSeverity.LOW,
            context=context
        )
        self.telemetry_type = telemetry_type


class BIMError(SVGXError):
    """BIM-related error."""
    
    def __init__(self, message: str, bim_operation: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.SERVICE_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        self.bim_operation = bim_operation


class ParserError(SVGXError):
    """Parser-related error."""
    
    def __init__(self, message: str, parser_type: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.PARSE_ERROR,
            severity=ErrorSeverity.HIGH,
            context=context
        )
        self.parser_type = parser_type


class RecognitionError(SVGXError):
    """Recognition-related error."""
    
    def __init__(self, message: str, recognition_type: Optional[str] = None,
                 context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        self.recognition_type = recognition_type


class ErrorHandler:
    """Centralized error handler for SVGX Engine."""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.recent_errors: List[SVGXError] = []
        self.max_recent_errors = 100
    
    def handle_error(self, error: SVGXError) -> Dict[str, Any]:
        """Handle an error and return structured response."""
        # Update error counts
        error_code = error.error_code.value
        self.error_counts[error_code] = self.error_counts.get(error_code, 0) + 1
        
        # Add to recent errors
        self.recent_errors.append(error)
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)
        
        # Return structured error response
        return {
            'success': False,
            'error': error.to_dict(),
            'error_code': error_code,
            'severity': error.severity.value
        }
    
    def handle_exception(self, exc: Exception, context: Optional[ErrorContext] = None) -> Dict[str, Any]:
        """Handle any exception and convert to SVGXError."""
        if isinstance(exc, SVGXError):
            return self.handle_error(exc)
        
        # Convert to SVGXError
        svgx_error = SVGXError(
            message=str(exc),
            error_code=ErrorCode.UNKNOWN_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            cause=exc
        )
        return self.handle_error(svgx_error)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_counts': self.error_counts,
            'recent_error_count': len(self.recent_errors),
            'severity_distribution': self._get_severity_distribution()
        }
    
    def _get_severity_distribution(self) -> Dict[str, int]:
        """Get distribution of errors by severity."""
        distribution = {}
        for error in self.recent_errors:
            severity = error.severity.value
            distribution[severity] = distribution.get(severity, 0) + 1
        return distribution
    
    def clear_statistics(self):
        """Clear error statistics."""
        self.error_counts.clear()
        self.recent_errors.clear()


# Global error handler instance
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get the global error handler."""
    return _error_handler


def handle_error(error: SVGXError) -> Dict[str, Any]:
    """Handle an error using the global handler."""
    return _error_handler.handle_error(error)


def handle_exception(exc: Exception, context: Optional[ErrorContext] = None) -> Dict[str, Any]:
    """Handle an exception using the global handler."""
    return _error_handler.handle_exception(exc, context)


def create_error_context(user_id: Optional[str] = None, session_id: Optional[str] = None,
                        request_id: Optional[str] = None, component: Optional[str] = None,
                        operation: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> ErrorContext:
    """Create an error context."""
    return ErrorContext(
        user_id=user_id,
        session_id=session_id,
        request_id=request_id,
        component=component,
        operation=operation,
        timestamp=datetime.now(),
        metadata=metadata
    )


def validate_input(data: Any, required_fields: List[str] = None, 
                  optional_fields: List[str] = None) -> None:
    """Validate input data."""
    if data is None:
        raise ValidationError("Input data cannot be None")
    
    if not isinstance(data, dict):
        raise ValidationError("Input data must be a dictionary")
    
    if required_fields:
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Required field '{field}' is missing", field=field)
    
    if optional_fields:
        for field in data:
            if field not in optional_fields and field not in (required_fields or []):
                raise ValidationError(f"Unexpected field '{field}'", field=field)


def safe_execute(func: callable, *args, context: Optional[ErrorContext] = None, **kwargs) -> Any:
    """Safely execute a function with error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as exc:
        error_response = handle_exception(exc, context)
        logger.error(f"Function execution failed: {func.__name__}", error=error_response)
        raise SVGXError(
            message=f"Function '{func.__name__}' failed: {str(exc)}",
            error_code=ErrorCode.RUNTIME_ERROR,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            cause=exc
        )