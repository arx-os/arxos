"""
SVGX Engine Utilities

This package contains utility functions and error handling for the SVGX Engine.
"""

from .errors import PersistenceError, ValidationError, DatabaseError, SVGXError

__all__ = [
    'PersistenceError',
    'ValidationError', 
    'DatabaseError',
    'SVGXError'
] 