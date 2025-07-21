"""
API Endpoints Module

This module contains all API endpoints for the Clean Architecture.
"""

from .building_api import BuildingAPI
from .health_api import HealthAPI

__all__ = [
    'BuildingAPI',
    'HealthAPI'
] 