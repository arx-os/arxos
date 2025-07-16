"""
Error handling utilities for SVGX Engine.

This module defines custom exception classes for the SVGX Engine.
"""

from typing import Dict, Any


class SVGXError(Exception):
    """Base exception for SVGX Engine."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"SVGXError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'SVGXError',
            'message': self.message,
            'details': self.details
        }


class PersistenceError(SVGXError):
    """Exception for persistence-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"PersistenceError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'PersistenceError',
            'message': self.message,
            'details': self.details
        }


class ValidationError(SVGXError):
    """Exception for validation-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"ValidationError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'ValidationError',
            'message': self.message,
            'details': self.details
        }


class DatabaseError(SVGXError):
    """Exception for database-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"DatabaseError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'DatabaseError',
            'message': self.message,
            'details': self.details
        }


class AccessControlError(SVGXError):
    """Exception for access control-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"AccessControlError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'AccessControlError',
            'message': self.message,
            'details': self.details
        }


class ParserError(SVGXError):
    """Exception for parser-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"ParserError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'ParserError',
            'message': self.message,
            'details': self.details
        }


class CompilerError(SVGXError):
    """Exception for compiler-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"CompilerError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'CompilerError',
            'message': self.message,
            'details': self.details
        }


class RuntimeError(SVGXError):
    """Exception for runtime-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"RuntimeError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'RuntimeError',
            'message': self.message,
            'details': self.details
        }


class BIMError(SVGXError):
    """Exception for BIM-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"BIMError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'BIMError',
            'message': self.message,
            'details': self.details
        }


class ExportError(SVGXError):
    """Exception for export-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"ExportError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'ExportError',
            'message': self.message,
            'details': self.details
        }


class ImportError(SVGXError):
    """Exception for import-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"ImportError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'ImportError',
            'message': self.message,
            'details': self.details
        }


class SymbolError(SVGXError):
    """Exception for symbol-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"SymbolError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'SymbolError',
            'message': self.message,
            'details': self.details
        }


class RecognitionError(SVGXError):
    """Exception for recognition-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"RecognitionError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'RecognitionError',
            'message': self.message,
            'details': self.details
        }


class SecurityError(Exception):
    """Exception for security-related errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"SecurityError: {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            'error': 'SecurityError',
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details
        }


class CacheError(Exception):
    """Exception for cache-related errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"CacheError: {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            'error': 'CacheError',
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details
        }


class TelemetryError(Exception):
    """Exception for telemetry-related errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"TelemetryError: {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            'error': 'TelemetryError',
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details
        }


class PerformanceError(Exception):
    """Exception for performance-related errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"PerformanceError: {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary."""
        return {
            'error': 'PerformanceError',
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details
        }


class BIMAssemblyError(SVGXError):
    """Exception for BIM assembly-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"BIMAssemblyError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'BIMAssemblyError',
            'message': self.message,
            'details': self.details
        }


class GeometryError(SVGXError):
    """Exception for geometry-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"GeometryError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'GeometryError',
            'message': self.message,
            'details': self.details
        }


class RelationshipError(SVGXError):
    """Exception for relationship-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"RelationshipError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'RelationshipError',
            'message': self.message,
            'details': self.details
        }


class PersistenceExportError(SVGXError):
    """Exception for persistence export-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"PersistenceExportError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'PersistenceExportError',
            'message': self.message,
            'details': self.details
        }


class JobError(SVGXError):
    """Exception for job-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"JobError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'JobError',
            'message': self.message,
            'details': self.details
        } 


class BIMHealthError(SVGXError):
    """Exception for BIM health-related errors."""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    def __str__(self):
        return f"BIMHealthError: {self.message}"
    def to_dict(self):
        return {
            'error': 'BIMHealthError',
            'message': self.message,
            'details': self.details
        } 


class AdvancedSymbolError(SVGXError):
    """Exception for advanced symbol-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"AdvancedSymbolError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'AdvancedSymbolError',
            'message': self.message,
            'details': self.details
        }


class VersionControlError(SVGXError):
    """Exception for version control-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"VersionControlError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'VersionControlError',
            'message': self.message,
            'details': self.details
        }


class CollaborationError(SVGXError):
    """Exception for collaboration-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"CollaborationError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'CollaborationError',
            'message': self.message,
            'details': self.details
        }


class SearchError(SVGXError):
    """Exception for search-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"SearchError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'SearchError',
            'message': self.message,
            'details': self.details
        }


class DependencyError(SVGXError):
    """Exception for dependency-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"DependencyError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'DependencyError',
            'message': self.message,
            'details': self.details
        }


class AnalyticsError(SVGXError):
    """Exception for analytics-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"AnalyticsError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'AnalyticsError',
            'message': self.message,
            'details': self.details
        }


class MarketplaceError(SVGXError):
    """Exception for marketplace-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"MarketplaceError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'MarketplaceError',
            'message': self.message,
            'details': self.details
        }


class RenderingError(SVGXError):
    """Exception for rendering-related errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message, self.details)
    
    def __str__(self):
        return f"RenderingError: {self.message}"
    
    def to_dict(self):
        """Convert error to dictionary."""
        return {
            'error': 'RenderingError',
            'message': self.message,
            'details': self.details
        }