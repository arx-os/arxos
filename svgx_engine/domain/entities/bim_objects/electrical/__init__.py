"""
SVGX Engine - Electrical BIM Objects

Electrical system BIM objects with embedded engineering logic.
Each object has its own engineering analysis capabilities.
"""

from .electrical_objects import (
    ElectricalObjectType,
    ElectricalBIMObject,
    ElectricalOutlet,
    ElectricalPanel,
    ElectricalSwitch,
    ElectricalTransformer,
    ElectricalBreaker,
    ElectricalLight,
)

__all__ = [
    "ElectricalObjectType",
    "ElectricalBIMObject",
    "ElectricalOutlet",
    "ElectricalPanel",
    "ElectricalSwitch",
    "ElectricalTransformer",
    "ElectricalBreaker",
    "ElectricalLight",
]
