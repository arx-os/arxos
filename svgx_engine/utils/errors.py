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


class SecurityError(Exception):
    """Exception raised for security-related errors in SVGX operations"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "SECURITY_ERROR"
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"{self.error_code}: {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format"""
        return {
            "error_type": "SecurityError",
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        } 


class CacheError(Exception):
    """Exception raised for cache-related errors in SVGX operations"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "CACHE_ERROR"
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"{self.error_code}: {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format"""
        return {
            "error_type": "CacheError",
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class TelemetryError(Exception):
    """Exception raised for telemetry-related errors in SVGX operations"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "TELEMETRY_ERROR"
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"{self.error_code}: {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format"""
        return {
            "error_type": "TelemetryError",
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class PerformanceError(Exception):
    """Exception raised for performance-related errors in SVGX operations"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "PERFORMANCE_ERROR"
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"{self.error_code}: {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format"""
        return {
            "error_type": "PerformanceError",
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        } 