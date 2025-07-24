"""
Domain Value Objects - Immutable Domain Concepts

This module contains value objects that represent immutable domain concepts
such as addresses, coordinates, dimensions, identifiers, money, and status.
These objects encapsulate business rules and validation logic.
"""

from svgx_engine.domain.value_objects.address import Address
from svgx_engine.domain.value_objects.coordinates import Coordinates
from svgx_engine.domain.value_objects.dimensions import Dimensions
from svgx_engine.domain.value_objects.identifier import Identifier
from svgx_engine.domain.value_objects.money import Money
from svgx_engine.domain.value_objects.status import Status

# Version and metadata
__version__ = "1.0.0"
__description__ = "Domain value objects for SVGX Engine"

# Export all value objects
__all__ = [
    "Address",
    "Coordinates", 
    "Dimensions",
    "Identifier",
    "Money",
    "Status"
] 