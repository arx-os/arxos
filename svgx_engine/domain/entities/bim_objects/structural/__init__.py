"""
SVGX Engine - Structural BIM Objects

Structural system BIM objects with embedded engineering logic.
Each object has its own engineering analysis capabilities.
"""

from .structural_objects import (
    StructuralObjectType,
    StructuralBIMObject,
    StructuralBeam,
    StructuralColumn,
    StructuralWall,
    StructuralSlab,
    StructuralFoundation,
)

__all__ = [
    "StructuralObjectType",
    "StructuralBIMObject",
    "StructuralBeam",
    "StructuralColumn",
    "StructuralWall",
    "StructuralSlab",
    "StructuralFoundation",
]
