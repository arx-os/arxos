"""
Utilities Package

This package provides utility functions for NLP processing including
context management and other helper functions.
"""

from services.context_manager import services.context_manager
__all__ = [
    "ContextManager",
    "resolve_context"
]
