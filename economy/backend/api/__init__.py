"""
BILT Token System API Package

This package contains the API routes and endpoints for the BILT token system.
"""

__version__ = "1.0.0"

# Import key API components
try:
    from .bilt_routes_mock import MockBiltAPIRouter
except ImportError:
    # Allow package to be imported even if components aren't available
    pass

__all__ = ["MockBiltAPIRouter"]
