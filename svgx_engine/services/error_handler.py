"""
SVGX Engine - Error Handler Service

This module provides centralized error handling for SVGX Engine services.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from structlog import get_logger

try:
    from ..utils.errors import SVGXError, ExportError, ImportError, ValidationError
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import SVGXError, ExportError, ImportError, ValidationError

logger = get_logger()


class SVGXErrorHandler:
    """Centralized error handler for SVGX Engine services."""
    
    def __init__(self):
        """Initialize the error handler."""
        self.error_log = []
        self.error_counts = {}
    
    def handle_export_error(self, error_message: str, format_type: str, details: Dict[str, Any] = None):
        """Handle export-related errors."""
        error = ExportError(f"Export failed for {format_type}: {error_message}", details or {})
        self._log_error(error, "export", format_type)
        return error
    
    def handle_import_error(self, error_message: str, format_type: str, details: Dict[str, Any] = None):
        """Handle import-related errors."""
        error = ImportError(f"Import failed for {format_type}: {error_message}", details or {})
        self._log_error(error, "import", format_type)
        return error
    
    def handle_validation_error(self, error_message: str, component: str, details: Dict[str, Any] = None):
        """Handle validation-related errors."""
        error = ValidationError(f"Validation failed for {component}: {error_message}", details or {})
        self._log_error(error, "validation", component)
        return error
    
    def handle_general_error(self, error_message: str, service: str, details: Dict[str, Any] = None):
        """Handle general SVGX errors."""
        error = SVGXError(f"Error in {service}: {error_message}", details or {})
        self._log_error(error, "general", service)
        return error
    
    def _log_error(self, error: SVGXError, error_type: str, component: str):
        """Log an error with metadata."""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'component': component,
            'message': str(error),
            'details': error.details
        }
        
        self.error_log.append(error_entry)
        
        # Update error counts
        key = f"{error_type}_{component}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        
        # Log to structured logger
        logger.error(
            "SVGX Error",
            error_type=error_type,
            component=component,
            message=str(error),
            details=error.details
        )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            'total_errors': len(self.error_log),
            'error_counts': self.error_counts,
            'recent_errors': self.error_log[-10:] if self.error_log else []
        }
    
    def clear_error_log(self):
        """Clear the error log."""
        self.error_log.clear()
        self.error_counts.clear()
    
    def get_errors_by_type(self, error_type: str) -> list:
        """Get all errors of a specific type."""
        return [error for error in self.error_log if error['error_type'] == error_type]
    
    def get_errors_by_component(self, component: str) -> list:
        """Get all errors for a specific component."""
        return [error for error in self.error_log if error['component'] == component]


# Convenience function for creating error handler
def create_error_handler() -> SVGXErrorHandler:
    """Create and return a configured SVGX error handler."""
    return SVGXErrorHandler() 