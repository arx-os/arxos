"""
Infrastructure Layer Error Handling

Provides infrastructure-specific error handling and integration with external services.
Follows clean architecture principles by not depending on application or domain layers directly.
"""

import logging
import traceback
from typing import Dict, Any, Optional, Type, Callable
from datetime import datetime
from contextlib import contextmanager
from functools import wraps

# Import domain exceptions for mapping
from domain.exceptions import (
    DomainException, RepositoryError, DatabaseError, 
    BuildingNotFoundError, FloorNotFoundError, RoomNotFoundError,
    DeviceNotFoundError, UserNotFoundError, ProjectNotFoundError
)

# Import application exceptions for mapping
from application.exceptions import (
    ApplicationError, ValidationError, BusinessRuleError,
    ResourceNotFoundError, ServiceUnavailableError, TransactionError
)


class InfrastructureError(Exception):
    """Base exception for infrastructure layer errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None, 
                 original_error: Exception = None):
        """Initialize infrastructure error.
        
        Args:
            message: Error message
            error_code: Error code for categorization
            details: Additional error details
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "INFRASTRUCTURE_ERROR"
        self.details = details or {}
        self.original_error = original_error
        self.timestamp = datetime.utcnow()
        
        # Log the error
        self._log_error()
    
    def _log_error(self):
        """Log the error with structured information."""
        logger = logging.getLogger(__name__)
        logger.error(
            f"Infrastructure Error: {self.error_code} - {self.message}",
            extra={
                "error_code": self.error_code,
                "details": self.details,
                "timestamp": self.timestamp.isoformat(),
                "original_error": str(self.original_error) if self.original_error else None
            },
            exc_info=self.original_error is not None
        )


class DatabaseConnectionError(InfrastructureError):
    """Exception raised when database connection fails."""
    
    def __init__(self, connection_string: str = None, message: str = None, original_error: Exception = None):
        if not message:
            message = "Database connection failed"
        
        super().__init__(
            message=message,
            error_code="DATABASE_CONNECTION_ERROR",
            details={"connection_string": connection_string},
            original_error=original_error
        )


class CacheConnectionError(InfrastructureError):
    """Exception raised when cache connection fails."""
    
    def __init__(self, cache_type: str, message: str = None, original_error: Exception = None):
        if not message:
            message = f"Cache connection failed: {cache_type}"
        
        super().__init__(
            message=message,
            error_code="CACHE_CONNECTION_ERROR",
            details={"cache_type": cache_type},
            original_error=original_error
        )


class MessageQueueError(InfrastructureError):
    """Exception raised when message queue operations fail."""
    
    def __init__(self, operation: str, queue_name: str = None, message: str = None, original_error: Exception = None):
        if not message:
            message = f"Message queue operation '{operation}' failed"
        
        super().__init__(
            message=message,
            error_code="MESSAGE_QUEUE_ERROR",
            details={"operation": operation, "queue_name": queue_name},
            original_error=original_error
        )


class ExternalServiceError(InfrastructureError):
    """Exception raised when external service calls fail."""
    
    def __init__(self, service_name: str, operation: str = None, status_code: int = None, 
                 message: str = None, original_error: Exception = None):
        if not message:
            message = f"External service '{service_name}' error"
        
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={
                "service_name": service_name,
                "operation": operation,
                "status_code": status_code
            },
            original_error=original_error
        )


class FileSystemError(InfrastructureError):
    """Exception raised when file system operations fail."""
    
    def __init__(self, operation: str, file_path: str = None, message: str = None, original_error: Exception = None):
        if not message:
            message = f"File system operation '{operation}' failed"
        
        super().__init__(
            message=message,
            error_code="FILESYSTEM_ERROR",
            details={"operation": operation, "file_path": file_path},
            original_error=original_error
        )


class ErrorMapper:
    """Maps between different types of errors across architectural layers."""
    
    # Domain -> Application mappings
    DOMAIN_TO_APPLICATION_MAP = {
        BuildingNotFoundError: lambda e: ResourceNotFoundError("Building", str(e.details.get('building_id', ''))),
        FloorNotFoundError: lambda e: ResourceNotFoundError("Floor", str(e.details.get('floor_id', ''))),
        RoomNotFoundError: lambda e: ResourceNotFoundError("Room", str(e.details.get('room_id', ''))),
        DeviceNotFoundError: lambda e: ResourceNotFoundError("Device", str(e.details.get('device_id', ''))),
        UserNotFoundError: lambda e: ResourceNotFoundError("User", str(e.details.get('user_id', ''))),
        ProjectNotFoundError: lambda e: ResourceNotFoundError("Project", str(e.details.get('project_id', ''))),
    }
    
    # Infrastructure -> Application mappings
    INFRASTRUCTURE_TO_APPLICATION_MAP = {
        DatabaseConnectionError: lambda e: ServiceUnavailableError("Database", e.message),
        CacheConnectionError: lambda e: ServiceUnavailableError("Cache", e.message),
        MessageQueueError: lambda e: ServiceUnavailableError("MessageQueue", e.message),
        ExternalServiceError: lambda e: ServiceUnavailableError(e.details.get('service_name', 'External'), e.message),
    }
    
    @classmethod
    def map_domain_to_application(cls, domain_error: DomainException) -> ApplicationError:
        """Map domain error to application error."""
        mapper = cls.DOMAIN_TO_APPLICATION_MAP.get(type(domain_error))
        if mapper:
            return mapper(domain_error)
        
        # Default mapping
        return ApplicationError(
            message=domain_error.message,
            error_code="DOMAIN_ERROR",
            details=getattr(domain_error, 'details', {})
        )
    
    @classmethod
    def map_infrastructure_to_application(cls, infra_error: InfrastructureError) -> ApplicationError:
        """Map infrastructure error to application error."""
        mapper = cls.INFRASTRUCTURE_TO_APPLICATION_MAP.get(type(infra_error))
        if mapper:
            return mapper(infra_error)
        
        # Default mapping
        return ApplicationError(
            message=infra_error.message,
            error_code="INFRASTRUCTURE_ERROR",
            details=infra_error.details
        )


class ErrorHandler:
    """Centralized error handler with retry logic and circuit breaker patterns."""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.5):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.logger = logging.getLogger(__name__)
    
    def handle_with_retry(self, operation: Callable, *args, **kwargs):
        """Execute operation with retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return operation(*args, **kwargs)
            except (DatabaseConnectionError, CacheConnectionError, ExternalServiceError) as e:
                last_error = e
                if attempt < self.max_retries:
                    wait_time = self.backoff_factor ** attempt
                    self.logger.warning(
                        f"Operation failed, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries}): {e}"
                    )
                    import time
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Operation failed after {self.max_retries} retries: {e}")
            except Exception as e:
                # Don't retry for non-infrastructure errors
                raise e
        
        if last_error:
            raise last_error


@contextmanager
def handle_infrastructure_errors(operation_name: str = "unknown"):
    """Context manager for handling infrastructure errors."""
    try:
        yield
    except DatabaseError as e:
        raise DatabaseConnectionError(
            message=f"Database error during {operation_name}",
            original_error=e
        )
    except ConnectionError as e:
        raise DatabaseConnectionError(
            message=f"Connection error during {operation_name}",
            original_error=e
        )
    except FileNotFoundError as e:
        raise FileSystemError(
            operation=operation_name,
            file_path=str(e.filename) if hasattr(e, 'filename') else None,
            original_error=e
        )
    except PermissionError as e:
        raise FileSystemError(
            operation=operation_name,
            message=f"Permission denied during {operation_name}",
            original_error=e
        )
    except Exception as e:
        raise InfrastructureError(
            message=f"Unexpected error during {operation_name}",
            error_code="UNEXPECTED_INFRASTRUCTURE_ERROR",
            details={"operation": operation_name},
            original_error=e
        )


def infrastructure_error_handler(operation_name: str = None):
    """Decorator for handling infrastructure errors in methods."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            with handle_infrastructure_errors(op_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def log_error_context(error: Exception, context: Dict[str, Any] = None):
    """Log error with additional context information."""
    logger = logging.getLogger(__name__)
    
    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat(),
        "traceback": traceback.format_exc() if isinstance(error, Exception) else None
    }
    
    if context:
        error_info.update(context)
    
    # Add structured logging fields
    if hasattr(error, 'error_code'):
        error_info['error_code'] = error.error_code
    if hasattr(error, 'details'):
        error_info['details'] = error.details
    
    logger.error("Error occurred", extra=error_info)


class ErrorReportingService:
    """Service for reporting errors to external monitoring systems."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.logger = logging.getLogger(__name__)
    
    def report_error(self, error: Exception, context: Dict[str, Any] = None, severity: str = "error"):
        """Report error to external monitoring system."""
        if not self.enabled:
            return
        
        try:
            # Log to structured logger
            log_error_context(error, context)
            
            # Here you could integrate with external services like:
            # - Sentry
            # - DataDog
            # - New Relic
            # - Custom monitoring endpoints
            
            self.logger.info(f"Error reported to monitoring system: {type(error).__name__}")
            
        except Exception as e:
            self.logger.error(f"Failed to report error to monitoring system: {e}")


# Global error handler instance
error_handler = ErrorHandler()
error_reporting = ErrorReportingService()


# Utility functions for consistent error handling
def handle_database_operation(operation: Callable, *args, **kwargs):
    """Handle database operations with proper error handling."""
    try:
        return error_handler.handle_with_retry(operation, *args, **kwargs)
    except InfrastructureError as e:
        error_reporting.report_error(e, {"operation": "database"})
        raise ErrorMapper.map_infrastructure_to_application(e)


def handle_cache_operation(operation: Callable, *args, **kwargs):
    """Handle cache operations with proper error handling."""
    try:
        return operation(*args, **kwargs)
    except Exception as e:
        # Cache errors should not break the application
        cache_error = CacheConnectionError(
            cache_type="redis",
            message="Cache operation failed",
            original_error=e
        )
        error_reporting.report_error(cache_error, {"operation": "cache"}, severity="warning")
        logging.getLogger(__name__).warning(f"Cache operation failed, continuing without cache: {e}")
        return None


def handle_external_service_call(service_name: str, operation: Callable, *args, **kwargs):
    """Handle external service calls with proper error handling."""
    try:
        return error_handler.handle_with_retry(operation, *args, **kwargs)
    except InfrastructureError as e:
        error_reporting.report_error(e, {"service": service_name, "operation": "external_service"})
        raise ErrorMapper.map_infrastructure_to_application(e)