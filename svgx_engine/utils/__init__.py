"""
Utility Modules - Common Utilities and Helpers

This module contains utility functions, classes, and helpers that
are used across the SVGX Engine for common operations.
"""

from svgx_engine.utils.errors import (
    SVGXError,
    ValidationError,
    BehaviorError,
    StateError,
    OptimizationError,
    MemoryError,
    LogicError,
    ConditionError,
    CacheError,
    TransitionError,
)

# Version and metadata
__version__ = "1.0.0"
__description__ = "Utility modules for SVGX Engine"

# Export all utility components
__all__ = [
    "SVGXError",
    "ValidationError",
    "BehaviorError",
    "StateError",
    "OptimizationError",
    "MemoryError",
    "LogicError",
    "ConditionError",
    "CacheError",
    "TransitionError",
]
