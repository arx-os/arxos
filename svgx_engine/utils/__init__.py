"""
Utils Module

This module contains utility classes and functions for the SVGX Engine.
"""

from .errors import (
    SVGXError,
    SymbolError,
    ValidationError,
    PipelineError,
    ConfigurationError,
    SecurityError
)

__all__ = [
    'SVGXError',
    'SymbolError',
    'ValidationError',
    'PipelineError',
    'ConfigurationError',
    'SecurityError'
] 