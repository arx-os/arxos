"""
Spatial Indexing System for Arxos BIM.

This module provides high-performance spatial indexing capabilities for ArxObjects,
supporting both 3D (Octree) and 2D (R-tree) spatial queries for conflict detection
and geometric operations on building components.
"""

__version__ = "1.0.0"
__author__ = "Arxos BIM Team"

from .octree_index import OctreeIndex, BoundingBox3D
from .rtree_index import RTreeIndex, BoundingBox2D
from .spatial_conflict_engine import SpatialConflictEngine
from .arxobject_core import ArxObject, ArxObjectType, ArxObjectPrecision, ArxObjectGeometry, ArxObjectMetadata

__all__ = [
    'OctreeIndex',
    'RTreeIndex', 
    'SpatialConflictEngine',
    'ArxObject',
    'ArxObjectType',
    'ArxObjectPrecision',
    'ArxObjectGeometry',
    'ArxObjectMetadata',
    'BoundingBox3D',
    'BoundingBox2D'
]