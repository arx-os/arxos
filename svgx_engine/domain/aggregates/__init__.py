"""
Domain Aggregates - Business Logic Encapsulation

This module contains domain aggregates that encapsulate business logic
and coordinate between entities and value objects.
"""

from svgx_engine.domain.aggregates.building_aggregate import BuildingAggregate

# Version and metadata
__version__ = "1.0.0"
__description__ = "Domain aggregates for SVGX Engine"

# Export all aggregates
__all__ = ["BuildingAggregate"]
