"""
SVGX Engine - Utilities Package

Provides utility functions and classes for SVGX Engine including:
- Error handling
- Performance monitoring
- Telemetry
- Validation utilities
"""

from svgx_engine.utils.errors import PersistenceError, ValidationError, DatabaseError, SVGXError

__all__ = [
    'PersistenceError',
    'ValidationError', 
    'DatabaseError',
    'SVGXError'
] 