"""
Aggregates Module

This module contains all aggregates used in the domain layer.
Aggregates are clusters of domain objects that can be treated as a single unit
for data changes and consistency boundaries.
"""

from .building_aggregate import BuildingAggregate

__all__ = [
    'BuildingAggregate'
] 