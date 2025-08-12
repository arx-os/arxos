"""
ArxObject Engine - Core Backend Implementation

This module provides the central engine for managing ArxObjects in the Arxos system.
It handles object lifecycle, relationships, constraints, and spatial operations.
"""

import uuid
import time
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
from enum import Enum

from core.spatial.arxobject_core import (
    ArxObject, ArxObjectType, ArxObjectGeometry, ArxObjectPrecision
)
from core.spatial.octree_index import OctreeIndex, BoundingBox3D
from core.spatial.rtree_index import RTreeIndex, BoundingBox2D
from core.constraints.constraint_engine import ConstraintEngine
from core.constraints.integrated_validator import IntegratedValidator

logger = logging.getLogger(__name__)


class RelationshipType(Enum):
    """Types of relationships between ArxObjects"""
    CONNECTED_TO = "connected_to"  # Electrical/mechanical connection
    MOUNTED_ON = "mounted_on"  # Physical mounting
    CONTAINED_IN = "contained_in"  # Spatial containment
    ADJACENT_TO = "adjacent_to"  # Spatial adjacency
    SUPPORTS = "supports"  # Structural support
    DEPENDS_ON = "depends_on"  # Functional dependency
    FEEDS = "feeds"  # Power/water/air feed
    CONTROLS = "controls"  # Control relationship
    PART_OF = "part_of"  # Part of assembly
    INTERSECTS = "intersects"  # Geometric intersection


@dataclass
class ArxObjectRelationship:
    """Represents a relationship between two ArxObjects"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    relationship_type: RelationshipType = RelationshipType.CONNECTED_TO
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'type': self.relationship_type.value,
            'properties': self.properties,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class ArxObjectConstraint:
    """Represents a constraint on an ArxObject"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    object_id: str = ""
    constraint_type: str = ""  # electrical_load, structural_capacity, etc.
    expression: str = ""  # Constraint expression
    parameters: Dict[str, Any] = field(default_factory=dict)
    severity: str = "error"  # error, warning, info
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def evaluate(self, obj: ArxObject, context: Dict[str, Any]) -> bool:
        """Evaluate constraint against object"""
        # This would integrate with the constraint engine
        return True  # Simplified for now


class ArxObjectEngine:
    """
    Central engine for managing ArxObjects.
    
    This engine provides:
    - Object lifecycle management (create, read, update, delete)
    - Relationship management
    - Constraint validation
    - Spatial indexing and queries
    - Transaction support
    - Event notifications
    """
    
    def __init__(self):
        """Initialize ArxObject Engine"""
        # Object storage
        self.objects: Dict[str, ArxObject] = {}
        self.relationships: Dict[str, ArxObjectRelationship] = {}
        self.constraints: Dict[str, List[ArxObjectConstraint]] = {}
        
        # Spatial indices
        self.octree_index = OctreeIndex(
            min_bounds=(-1000, -1000, -1000),
            max_bounds=(1000, 1000, 1000),
            max_depth=8,
            max_objects_per_node=10
        )
        self.rtree_index = RTreeIndex()
        
        # Constraint and validation engines
        self.constraint_engine = ConstraintEngine()
        self.validator = IntegratedValidator()
        
        # Transaction support
        self.transaction_stack: List[Dict[str, Any]] = []
        self.in_transaction = False
        
        # Event listeners
        self.event_listeners: Dict[str, List[callable]] = {
            'object_created': [],
            'object_updated': [],
            'object_deleted': [],
            'relationship_created': [],
            'relationship_deleted': [],
            'constraint_violated': []
        }
        
        # Performance metrics
        self.metrics = {
            'objects_created': 0,
            'objects_updated': 0,
            'objects_deleted': 0,
            'queries_executed': 0,
            'constraints_checked': 0
        }
        
        logger.info("ArxObject Engine initialized")
    
    # ==========================================
    # Object Lifecycle Management
    # ==========================================
    
    async def create_object(
        self,
        object_type: ArxObjectType,
        properties: Dict[str, Any],
        geometry: Optional[ArxObjectGeometry] = None,
        relationships: Optional[List[Dict[str, Any]]] = None,
        constraints: Optional[List[Dict[str, Any]]] = None
    ) -> ArxObject:
        """
        Create a new ArxObject.
        
        Args:
            object_type: Type of object to create
            properties: Object properties
            geometry: Optional geometry specification
            relationships: Optional initial relationships
            constraints: Optional constraints to apply
            
        Returns:
            Created ArxObject
            
        Raises:
            ValidationError: If object fails validation
        """
        # Create object
        obj = ArxObject(
            object_type=object_type,
            properties=properties,
            geometry=geometry or ArxObjectGeometry()
        )
        
        # Validate object
        validation_result = await self._validate_object(obj)
        if not validation_result['valid']:
            raise ValueError(f"Object validation failed: {validation_result['errors']}")
        
        # Store object
        self.objects[obj.id] = obj
        
        # Add to spatial indices
        self._index_object(obj)
        
        # Create relationships if specified
        if relationships:
            for rel_spec in relationships:
                await self.create_relationship(
                    source_id=obj.id,
                    target_id=rel_spec['target_id'],
                    relationship_type=RelationshipType(rel_spec['type']),
                    properties=rel_spec.get('properties', {})
                )
        
        # Add constraints if specified
        if constraints:
            for const_spec in constraints:
                await self.add_constraint(
                    object_id=obj.id,
                    constraint_type=const_spec['type'],
                    expression=const_spec['expression'],
                    parameters=const_spec.get('parameters', {})
                )
        
        # Emit event
        await self._emit_event('object_created', obj)
        
        # Update metrics
        self.metrics['objects_created'] += 1
        
        logger.info(f"Created ArxObject: {obj.id} of type {object_type.value}")
        return obj
    
    async def get_object(self, object_id: str) -> Optional[ArxObject]:
        """
        Retrieve an ArxObject by ID.
        
        Args:
            object_id: Object identifier
            
        Returns:
            ArxObject or None if not found
        """
        self.metrics['queries_executed'] += 1
        return self.objects.get(object_id)
    
    async def update_object(
        self,
        object_id: str,
        properties: Optional[Dict[str, Any]] = None,
        geometry: Optional[ArxObjectGeometry] = None,
        validate: bool = True
    ) -> ArxObject:
        """
        Update an ArxObject.
        
        Args:
            object_id: Object identifier
            properties: Properties to update
            geometry: New geometry (if changing)
            validate: Whether to validate changes
            
        Returns:
            Updated ArxObject
            
        Raises:
            KeyError: If object not found
            ValidationError: If update fails validation
        """
        if object_id not in self.objects:
            raise KeyError(f"Object not found: {object_id}")
        
        obj = self.objects[object_id]
        
        # Store original state for rollback
        original_state = {
            'properties': obj.properties.copy(),
            'geometry': obj.geometry
        }
        
        # Apply updates
        if properties:
            obj.properties.update(properties)
        if geometry:
            # Remove from spatial indices
            self._unindex_object(obj)
            obj.geometry = geometry
            # Re-add to spatial indices
            self._index_object(obj)
        
        # Validate if requested
        if validate:
            validation_result = await self._validate_object(obj)
            if not validation_result['valid']:
                # Rollback changes
                obj.properties = original_state['properties']
                obj.geometry = original_state['geometry']
                if geometry:
                    self._unindex_object(obj)
                    self._index_object(obj)
                raise ValueError(f"Update validation failed: {validation_result['errors']}")
        
        # Update timestamp
        obj.updated_at = datetime.now(timezone.utc)
        
        # Emit event
        await self._emit_event('object_updated', obj)
        
        # Update metrics
        self.metrics['objects_updated'] += 1
        
        logger.info(f"Updated ArxObject: {object_id}")
        return obj
    
    async def delete_object(
        self,
        object_id: str,
        cascade: bool = False,
        force: bool = False
    ) -> bool:
        """
        Delete an ArxObject.
        
        Args:
            object_id: Object identifier
            cascade: Whether to cascade delete related objects
            force: Whether to force delete despite dependencies
            
        Returns:
            True if deleted successfully
            
        Raises:
            KeyError: If object not found
            DependencyError: If object has dependencies and force=False
        """
        if object_id not in self.objects:
            raise KeyError(f"Object not found: {object_id}")
        
        obj = self.objects[object_id]
        
        # Check dependencies
        if not force:
            dependencies = await self.get_object_dependencies(object_id)
            if dependencies:
                raise ValueError(f"Object has {len(dependencies)} dependencies")
        
        # Remove from spatial indices
        self._unindex_object(obj)
        
        # Delete relationships
        relationships = await self.get_object_relationships(object_id)
        for rel in relationships:
            await self.delete_relationship(rel.id)
        
        # Delete constraints
        if object_id in self.constraints:
            del self.constraints[object_id]
        
        # Cascade delete if requested
        if cascade:
            dependencies = await self.get_object_dependencies(object_id)
            for dep_id in dependencies:
                await self.delete_object(dep_id, cascade=True, force=True)
        
        # Delete object
        del self.objects[object_id]
        
        # Emit event
        await self._emit_event('object_deleted', {'id': object_id})
        
        # Update metrics
        self.metrics['objects_deleted'] += 1
        
        logger.info(f"Deleted ArxObject: {object_id}")
        return True
    
    # ==========================================
    # Relationship Management
    # ==========================================
    
    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: RelationshipType,
        properties: Optional[Dict[str, Any]] = None
    ) -> ArxObjectRelationship:
        """
        Create a relationship between two ArxObjects.
        
        Args:
            source_id: Source object ID
            target_id: Target object ID
            relationship_type: Type of relationship
            properties: Optional relationship properties
            
        Returns:
            Created relationship
            
        Raises:
            KeyError: If source or target object not found
        """
        # Verify objects exist
        if source_id not in self.objects:
            raise KeyError(f"Source object not found: {source_id}")
        if target_id not in self.objects:
            raise KeyError(f"Target object not found: {target_id}")
        
        # Create relationship
        relationship = ArxObjectRelationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            properties=properties or {}
        )
        
        # Store relationship
        self.relationships[relationship.id] = relationship
        
        # Update object relationship caches
        self.objects[source_id].relationships.append(relationship.id)
        self.objects[target_id].relationships.append(relationship.id)
        
        # Emit event
        await self._emit_event('relationship_created', relationship)
        
        logger.info(f"Created relationship: {source_id} {relationship_type.value} {target_id}")
        return relationship
    
    async def get_object_relationships(
        self,
        object_id: str,
        relationship_type: Optional[RelationshipType] = None,
        direction: str = "both"  # both, outgoing, incoming
    ) -> List[ArxObjectRelationship]:
        """
        Get relationships for an object.
        
        Args:
            object_id: Object identifier
            relationship_type: Optional filter by type
            direction: Filter by direction
            
        Returns:
            List of relationships
        """
        if object_id not in self.objects:
            return []
        
        obj = self.objects[object_id]
        relationships = []
        
        for rel_id in obj.relationships:
            if rel_id in self.relationships:
                rel = self.relationships[rel_id]
                
                # Filter by direction
                if direction == "outgoing" and rel.source_id != object_id:
                    continue
                if direction == "incoming" and rel.target_id != object_id:
                    continue
                
                # Filter by type
                if relationship_type and rel.relationship_type != relationship_type:
                    continue
                
                relationships.append(rel)
        
        return relationships
    
    async def delete_relationship(self, relationship_id: str) -> bool:
        """
        Delete a relationship.
        
        Args:
            relationship_id: Relationship identifier
            
        Returns:
            True if deleted successfully
        """
        if relationship_id not in self.relationships:
            return False
        
        rel = self.relationships[relationship_id]
        
        # Remove from object caches
        if rel.source_id in self.objects:
            self.objects[rel.source_id].relationships.remove(relationship_id)
        if rel.target_id in self.objects:
            self.objects[rel.target_id].relationships.remove(relationship_id)
        
        # Delete relationship
        del self.relationships[relationship_id]
        
        # Emit event
        await self._emit_event('relationship_deleted', {'id': relationship_id})
        
        logger.info(f"Deleted relationship: {relationship_id}")
        return True
    
    async def get_connected_objects(
        self,
        object_id: str,
        relationship_type: Optional[RelationshipType] = None,
        depth: int = 1
    ) -> Set[str]:
        """
        Get objects connected through relationships.
        
        Args:
            object_id: Starting object ID
            relationship_type: Optional filter by relationship type
            depth: How many levels to traverse
            
        Returns:
            Set of connected object IDs
        """
        visited = set()
        to_visit = {object_id}
        
        for _ in range(depth):
            next_level = set()
            for current_id in to_visit:
                if current_id in visited:
                    continue
                visited.add(current_id)
                
                relationships = await self.get_object_relationships(
                    current_id, 
                    relationship_type
                )
                
                for rel in relationships:
                    if rel.source_id == current_id:
                        next_level.add(rel.target_id)
                    else:
                        next_level.add(rel.source_id)
            
            to_visit = next_level
        
        visited.discard(object_id)  # Remove starting object
        return visited
    
    async def get_object_dependencies(self, object_id: str) -> List[str]:
        """
        Get objects that depend on this object.
        
        Args:
            object_id: Object identifier
            
        Returns:
            List of dependent object IDs
        """
        dependencies = []
        
        for rel in self.relationships.values():
            if rel.target_id == object_id and rel.relationship_type in [
                RelationshipType.DEPENDS_ON,
                RelationshipType.MOUNTED_ON,
                RelationshipType.SUPPORTS
            ]:
                dependencies.append(rel.source_id)
        
        return dependencies
    
    # ==========================================
    # Constraint Management
    # ==========================================
    
    async def add_constraint(
        self,
        object_id: str,
        constraint_type: str,
        expression: str,
        parameters: Optional[Dict[str, Any]] = None,
        severity: str = "error"
    ) -> ArxObjectConstraint:
        """
        Add a constraint to an object.
        
        Args:
            object_id: Object identifier
            constraint_type: Type of constraint
            expression: Constraint expression
            parameters: Optional parameters
            severity: Constraint severity
            
        Returns:
            Created constraint
        """
        if object_id not in self.objects:
            raise KeyError(f"Object not found: {object_id}")
        
        constraint = ArxObjectConstraint(
            object_id=object_id,
            constraint_type=constraint_type,
            expression=expression,
            parameters=parameters or {},
            severity=severity
        )
        
        if object_id not in self.constraints:
            self.constraints[object_id] = []
        self.constraints[object_id].append(constraint)
        
        logger.info(f"Added constraint to object {object_id}: {constraint_type}")
        return constraint
    
    async def validate_constraints(
        self,
        object_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate all constraints for an object.
        
        Args:
            object_id: Object identifier
            context: Optional validation context
            
        Returns:
            Validation result with violations
        """
        if object_id not in self.objects:
            return {'valid': False, 'errors': ['Object not found']}
        
        obj = self.objects[object_id]
        violations = []
        warnings = []
        
        # Check object-specific constraints
        if object_id in self.constraints:
            for constraint in self.constraints[object_id]:
                if constraint.active:
                    if not constraint.evaluate(obj, context or {}):
                        if constraint.severity == "error":
                            violations.append({
                                'type': constraint.constraint_type,
                                'message': f"Constraint violated: {constraint.expression}",
                                'severity': constraint.severity
                            })
                        else:
                            warnings.append({
                                'type': constraint.constraint_type,
                                'message': f"Constraint warning: {constraint.expression}",
                                'severity': constraint.severity
                            })
        
        # Use integrated validator for comprehensive checks
        validation_result = self.validator.validate(obj)
        if not validation_result.is_valid:
            for violation in validation_result.violations:
                violations.append({
                    'type': violation.constraint_type,
                    'message': violation.message,
                    'severity': violation.severity
                })
        
        self.metrics['constraints_checked'] += 1
        
        return {
            'valid': len(violations) == 0,
            'violations': violations,
            'warnings': warnings
        }
    
    # ==========================================
    # Spatial Operations
    # ==========================================
    
    async def find_objects_in_region(
        self,
        bounds: BoundingBox3D,
        object_types: Optional[List[ArxObjectType]] = None
    ) -> List[ArxObject]:
        """
        Find objects within a 3D region.
        
        Args:
            bounds: 3D bounding box
            object_types: Optional filter by object types
            
        Returns:
            List of objects in region
        """
        object_ids = self.octree_index.query_region(bounds)
        objects = []
        
        for obj_id in object_ids:
            if obj_id in self.objects:
                obj = self.objects[obj_id]
                if not object_types or obj.object_type in object_types:
                    objects.append(obj)
        
        self.metrics['queries_executed'] += 1
        return objects
    
    async def find_nearest_objects(
        self,
        point: Tuple[float, float, float],
        radius: float,
        object_types: Optional[List[ArxObjectType]] = None,
        limit: int = 10
    ) -> List[Tuple[ArxObject, float]]:
        """
        Find nearest objects to a point.
        
        Args:
            point: 3D point (x, y, z)
            radius: Search radius
            object_types: Optional filter by object types
            limit: Maximum number of results
            
        Returns:
            List of (object, distance) tuples
        """
        bounds = BoundingBox3D(
            point[0] - radius, point[1] - radius, point[2] - radius,
            point[0] + radius, point[1] + radius, point[2] + radius
        )
        
        nearby_objects = await self.find_objects_in_region(bounds, object_types)
        
        # Calculate distances
        results = []
        for obj in nearby_objects:
            distance = self._calculate_distance(point, (
                obj.geometry.x,
                obj.geometry.y,
                obj.geometry.z
            ))
            if distance <= radius:
                results.append((obj, distance))
        
        # Sort by distance and limit
        results.sort(key=lambda x: x[1])
        return results[:limit]
    
    async def check_spatial_conflicts(
        self,
        object_id: str,
        clearance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Check for spatial conflicts with other objects.
        
        Args:
            object_id: Object identifier
            clearance: Required clearance distance
            
        Returns:
            List of conflicts
        """
        if object_id not in self.objects:
            return []
        
        obj = self.objects[object_id]
        conflicts = []
        
        # Get bounding box with clearance
        bbox = obj.geometry.get_bounding_box_3d()
        expanded_bbox = BoundingBox3D(
            bbox.min_x - clearance,
            bbox.min_y - clearance,
            bbox.min_z - clearance,
            bbox.max_x + clearance,
            bbox.max_y + clearance,
            bbox.max_z + clearance
        )
        
        # Find potentially conflicting objects
        nearby_objects = await self.find_objects_in_region(expanded_bbox)
        
        for other in nearby_objects:
            if other.id != object_id:
                # Check if objects actually conflict
                if self._objects_intersect(obj, other, clearance):
                    conflicts.append({
                        'object_id': other.id,
                        'object_type': other.object_type.value,
                        'conflict_type': 'spatial_overlap',
                        'severity': self._determine_conflict_severity(obj, other)
                    })
        
        return conflicts
    
    # ==========================================
    # Transaction Support
    # ==========================================
    
    async def begin_transaction(self) -> str:
        """
        Begin a new transaction.
        
        Returns:
            Transaction ID
        """
        transaction_id = str(uuid.uuid4())
        self.transaction_stack.append({
            'id': transaction_id,
            'operations': [],
            'timestamp': datetime.now(timezone.utc)
        })
        self.in_transaction = True
        
        logger.info(f"Started transaction: {transaction_id}")
        return transaction_id
    
    async def commit_transaction(self, transaction_id: str) -> bool:
        """
        Commit a transaction.
        
        Args:
            transaction_id: Transaction identifier
            
        Returns:
            True if committed successfully
        """
        if not self.transaction_stack:
            return False
        
        transaction = self.transaction_stack[-1]
        if transaction['id'] != transaction_id:
            return False
        
        # Validate all operations
        for operation in transaction['operations']:
            if operation['type'] == 'update':
                validation = await self.validate_constraints(operation['object_id'])
                if not validation['valid']:
                    # Rollback
                    await self.rollback_transaction(transaction_id)
                    return False
        
        # Commit successful
        self.transaction_stack.pop()
        self.in_transaction = len(self.transaction_stack) > 0
        
        logger.info(f"Committed transaction: {transaction_id}")
        return True
    
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """
        Rollback a transaction.
        
        Args:
            transaction_id: Transaction identifier
            
        Returns:
            True if rolled back successfully
        """
        if not self.transaction_stack:
            return False
        
        transaction = self.transaction_stack[-1]
        if transaction['id'] != transaction_id:
            return False
        
        # Rollback operations in reverse order
        for operation in reversed(transaction['operations']):
            if operation['type'] == 'create':
                await self.delete_object(operation['object_id'], force=True)
            elif operation['type'] == 'update':
                # Restore original state
                obj = self.objects[operation['object_id']]
                obj.properties = operation['original_state']['properties']
                obj.geometry = operation['original_state']['geometry']
            elif operation['type'] == 'delete':
                # Restore deleted object
                self.objects[operation['object_id']] = operation['original_state']
        
        self.transaction_stack.pop()
        self.in_transaction = len(self.transaction_stack) > 0
        
        logger.info(f"Rolled back transaction: {transaction_id}")
        return True
    
    # ==========================================
    # Helper Methods
    # ==========================================
    
    def _index_object(self, obj: ArxObject) -> None:
        """Add object to spatial indices"""
        bbox = obj.geometry.get_bounding_box_3d()
        self.octree_index.insert(obj.id, bbox)
        
        # Also add to 2D index for floor plan queries
        bbox_2d = BoundingBox2D(bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y)
        self.rtree_index.insert(obj.id, bbox_2d)
    
    def _unindex_object(self, obj: ArxObject) -> None:
        """Remove object from spatial indices"""
        bbox = obj.geometry.get_bounding_box_3d()
        self.octree_index.remove(obj.id, bbox)
        
        bbox_2d = BoundingBox2D(bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y)
        self.rtree_index.remove(obj.id, bbox_2d)
    
    async def _validate_object(self, obj: ArxObject) -> Dict[str, Any]:
        """Validate an object"""
        return await self.validate_constraints(obj.id)
    
    async def _emit_event(self, event_type: str, data: Any) -> None:
        """Emit an event to registered listeners"""
        if event_type in self.event_listeners:
            for listener in self.event_listeners[event_type]:
                try:
                    await listener(data)
                except Exception as e:
                    logger.error(f"Error in event listener: {e}")
    
    def _calculate_distance(
        self,
        point1: Tuple[float, float, float],
        point2: Tuple[float, float, float]
    ) -> float:
        """Calculate 3D distance between two points"""
        return ((point1[0] - point2[0]) ** 2 +
                (point1[1] - point2[1]) ** 2 +
                (point1[2] - point2[2]) ** 2) ** 0.5
    
    def _objects_intersect(
        self,
        obj1: ArxObject,
        obj2: ArxObject,
        clearance: float
    ) -> bool:
        """Check if two objects intersect with given clearance"""
        bbox1 = obj1.geometry.get_bounding_box_3d()
        bbox2 = obj2.geometry.get_bounding_box_3d()
        
        # Check if bounding boxes overlap with clearance
        return not (
            bbox1.max_x + clearance < bbox2.min_x or
            bbox1.min_x - clearance > bbox2.max_x or
            bbox1.max_y + clearance < bbox2.min_y or
            bbox1.min_y - clearance > bbox2.max_y or
            bbox1.max_z + clearance < bbox2.min_z or
            bbox1.min_z - clearance > bbox2.max_z
        )
    
    def _determine_conflict_severity(
        self,
        obj1: ArxObject,
        obj2: ArxObject
    ) -> str:
        """Determine severity of spatial conflict"""
        priority1 = obj1.object_type.get_system_priority()
        priority2 = obj2.object_type.get_system_priority()
        
        # Higher priority difference means more severe conflict
        if abs(priority1 - priority2) >= 2:
            return "critical"
        elif abs(priority1 - priority2) == 1:
            return "warning"
        else:
            return "info"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            'total_objects': len(self.objects),
            'total_relationships': len(self.relationships),
            'total_constraints': sum(len(c) for c in self.constraints.values()),
            'metrics': self.metrics,
            'spatial_index_stats': {
                'octree_depth': self.octree_index.max_depth,
                'rtree_size': len(self.rtree_index.index)
            }
        }