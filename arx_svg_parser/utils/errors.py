"""
Error handling utilities for Arxos SVG-BIM Integration System.

This module provides custom exception classes for different types of errors
that can occur in the SVG-BIM system, with proper error categorization
and detailed error messages.
"""

from typing import Optional, Dict, Any, List


class ArxosError(Exception):
    """Base exception class for all Arxos errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class SVGParseError(ArxosError):
    """Error raised when SVG parsing fails."""
    pass


class BIMAssemblyError(ArxosError):
    """Error raised when BIM assembly fails."""
    pass


class UnknownBIMTypeError(ArxosError):
    """Error raised when an unknown BIM type is encountered."""
    pass


class GeometryError(ArxosError):
    """Error raised when geometric operations fail."""
    pass


class RelationshipError(ArxosError):
    """Error raised when relationship operations fail."""
    pass


class EnrichmentError(ArxosError):
    """Error raised when data enrichment fails."""
    pass


class ValidationError(ArxosError):
    """Error raised when validation fails."""
    pass


class ExportError(ArxosError):
    """Error raised when export operations fail."""
    pass


class PersistenceError(ArxosError):
    """Error raised when persistence operations fail."""
    pass


class DatabaseError(ArxosError):
    """Error raised when database operations fail."""
    pass


class APIError(ArxosError):
    """Error raised when API operations fail."""
    pass


class AuthenticationError(ArxosError):
    """Error raised when authentication fails."""
    pass


class AuthorizationError(ArxosError):
    """Error raised when authorization fails."""
    pass


class ConfigurationError(ArxosError):
    """Error raised when configuration is invalid."""
    pass


class NetworkError(ArxosError):
    """Error raised when network operations fail."""
    pass


class FileError(ArxosError):
    """Error raised when file operations fail."""
    pass


class SymbolError(ArxosError):
    """Error raised when symbol operations fail."""
    pass


class JobError(ArxosError):
    """Error raised when background job operations fail."""
    pass


class BackupError(ArxosError):
    """Error raised when backup operations fail."""
    pass


class MigrationError(ArxosError):
    """Error raised when database migration fails."""
    pass


def create_error_response(error: ArxosError, status_code: int = 500) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "error": True,
        "error_type": error.__class__.__name__,
        "message": error.message,
        "details": error.details,
        "status_code": status_code
    }


def handle_database_error(error: Exception, operation: str) -> ArxosError:
    """Handle database errors and convert to appropriate ArxosError."""
    error_message = str(error)
    
    if "UNIQUE constraint failed" in error_message:
        return PersistenceError(f"Duplicate entry in {operation}", {"operation": operation})
    elif "FOREIGN KEY constraint failed" in error_message:
        return ValidationError(f"Referenced record not found in {operation}", {"operation": operation})
    elif "NOT NULL constraint failed" in error_message:
        return ValidationError(f"Required field missing in {operation}", {"operation": operation})
    elif "database is locked" in error_message.lower():
        return DatabaseError(f"Database is locked during {operation}", {"operation": operation})
    elif "no such table" in error_message.lower():
        return DatabaseError(f"Database table not found during {operation}", {"operation": operation})
    elif "disk full" in error_message.lower():
        return DatabaseError(f"Database disk full during {operation}", {"operation": operation})
    else:
        return DatabaseError(f"Database error during {operation}: {error_message}", {"operation": operation})


def handle_validation_error(error: Exception, context: str) -> ValidationError:
    """Handle validation errors and convert to ValidationError."""
    error_message = str(error)
    
    if "jsonschema" in error_message.lower():
        return ValidationError(f"JSON schema validation failed in {context}", {"context": context, "details": error_message})
    elif "required" in error_message.lower():
        return ValidationError(f"Required field missing in {context}", {"context": context, "details": error_message})
    elif "invalid" in error_message.lower():
        return ValidationError(f"Invalid data in {context}", {"context": context, "details": error_message})
    else:
        return ValidationError(f"Validation error in {context}: {error_message}", {"context": context})


def handle_file_error(error: Exception, operation: str, file_path: str) -> FileError:
    """Handle file operation errors and convert to FileError."""
    error_message = str(error)
    
    if "no such file" in error_message.lower() or "file not found" in error_message.lower():
        return FileError(f"File not found: {file_path}", {"operation": operation, "file_path": file_path})
    elif "permission denied" in error_message.lower():
        return FileError(f"Permission denied for file: {file_path}", {"operation": operation, "file_path": file_path})
    elif "disk full" in error_message.lower():
        return FileError(f"Disk full while {operation}: {file_path}", {"operation": operation, "file_path": file_path})
    else:
        return FileError(f"File error during {operation}: {error_message}", {"operation": operation, "file_path": file_path})


def log_error(error: ArxosError, logger, context: str = ""):
    """Log an error with proper formatting."""
    error_dict = error.to_dict()
    if context:
        error_dict["context"] = context
    
    logger.error(f"Error in {context}: {error.message}", extra=error_dict) 