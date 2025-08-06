"""
Utilities Package

This package provides utility functions for NLP processing including
context management and other helper functions.
"""

from .context_manager import ContextManager, resolve_context

__all__ = ["ContextManager", "resolve_context"]
