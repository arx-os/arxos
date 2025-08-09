"""
SVGX Engine - BIM Relationship Models

This module defines the data models for BIM relationships including:
- Spatial relationships
- System relationships
- Dependency relationships
- Relationship sets
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid

class SpatialRelationshipType(str, Enum):
    """
    Class for SpatialRelationshipType functionality

Attributes:
        None

Methods:
        None

Example:
        instance = SpatialRelationshipType()
        result = instance.method()
        print(result)
    """
    CONTAINS = "contains"
    ADJACENT = "adjacent"
    CONNECTED = "connected"
    OVERLAPS = "overlaps"
    WITHIN = "within"

class SystemRelationshipType(str, Enum):
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    FIRE_ALARM = "fire_alarm"
    SECURITY = "security"
    DATA = "data"
    GENERIC = "generic"

class DependencyType(str, Enum):
    PARENT = "parent"
    CHILD = "child"
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    REFERENCE = "reference"

@dataclass
class BIMRelationship:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    relationship_type: str = ""  # e.g., spatial, system, dependency
    subtype: Optional[str] = None  # e.g., contains, adjacent, mechanical, parent
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        pass
    """
    Perform __post_init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __post_init__(param)
        print(result)
    """
        if self.source_id == self.target_id:
            raise ValueError("Relationship cannot be self-referential (source == target)")

@dataclass
class BIMRelationshipSet:
    spatial: List[BIMRelationship] = field(default_factory=list)
    system: List[BIMRelationship] = field(default_factory=list)
    dependency: List[BIMRelationship] = field(default_factory=list)

    def add_relationship(self, rel: BIMRelationship):
        if rel.relationship_type == 'spatial':
            self.spatial.append(rel)
        elif rel.relationship_type == 'system':
            self.system.append(rel)
        elif rel.relationship_type == 'dependency':
            self.dependency.append(rel)
        else:
    """
    Validate the given input against rules

Args:
        valid_ids: Description of valid_ids

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = validate_relationships(param)
        print(result)
    """
            raise ValueError(f"Unknown relationship type: {rel.relationship_type}")

    def validate_relationships(self, valid_ids: List[str]) -> List[str]:
        errors = []
        all_rels = self.spatial + self.system + self.dependency
        seen = set()
        for rel in all_rels:
            if rel.source_id not in valid_ids:
                errors.append(f"Invalid source_id: {rel.source_id}")
            if rel.target_id not in valid_ids:
                errors.append(f"Invalid target_id: {rel.target_id}")
            # Check for duplicate relationships
            key = (rel.source_id, rel.target_id, rel.relationship_type, rel.subtype)
            if key in seen:
                errors.append(f"Duplicate relationship: {key}")
            seen.add(key)
            # Self-referential already checked in __post_init__
        # Check for cycles in dependency relationships
        dep_graph = {}
        for rel in self.dependency:
            dep_graph.setdefault(rel.source_id, []).append(rel.target_id)
def visit(node, stack):
            if node in stack:
                errors.append(f"Cycle detected in dependencies: {' -> '.join(stack + [node])}")
                return
            stack.append(node)
            for neighbor in dep_graph.get(node, []):
                visit(neighbor, stack)
            stack.pop()
        for node in dep_graph:
            visit(node, [])
        return errors
