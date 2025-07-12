"""
App module for Arxos SVG-BIM integration system.

This module provides the FastAPI application instance for external use.
"""

from api.main import app

# Export the FastAPI app instance
__all__ = ['app'] 