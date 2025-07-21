"""
Domain Services Module

This module contains all domain services used in the domain layer.
Domain services contain business logic that doesn't belong to any specific entity
or aggregate, following the Domain Service pattern.
"""

from .building_service import BuildingService

__all__ = [
    'BuildingService'
] 