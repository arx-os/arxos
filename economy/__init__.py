"""
BILT Token System Package

This package contains the complete BILT (Building Infrastructure Link Token)
currency system implementation for the arxos economy.
"""

__version__ = "1.0.0"
__author__ = "Arxos Development Team"
__description__ = "BILT Token System for Building Infrastructure Economy"

# Import key components for easy access
try:
    from .backend.services.bilt_token.minting_engine_mock import MockBiltMintingEngine
    from .backend.services.bilt_token.dividend_calculator_mock import (
        MockBiltDividendCalculator,
    )
    from .backend.api.bilt_routes_mock import MockBiltAPIRouter
except ImportError:
    # Allow package to be imported even if components aren't available
    pass

__all__ = ["MockBiltMintingEngine", "MockBiltDividendCalculator", "MockBiltAPIRouter"]
