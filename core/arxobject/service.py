"""
ArxObject Service - Business Logic Layer

This module provides high-level business operations for ArxObjects,
orchestrating between the engine, repository, and other services.
"""

import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import json

from core.spatial.arxobject_core import (
    ArxObject, ArxObjectType, ArxObjectGeometry, ArxObjectPrecision
)
from core.arxobject.engine import (
    ArxObjectEngine, ArxObjectRelationship, ArxObjectConstraint, RelationshipType
)
from core.arxobject.repository import ArxObjectRepository
from core.constraints.integrated_validator import IntegratedValidator

logger = logging.getLogger(__name__)


@dataclass
class ArxObjectQuery:
    """Query specification for ArxObjects"""
    object_types: Optional[List[ArxObjectType]] = None
    property_filters: Optional[Dict[str, Any]] = None
    spatial_bounds: Optional[Tuple[float, float, float, float, float, float]] = None
    near_point: Optional[Tuple[float, float, float]] = None
    radius: Optional[float] = None
    relationships: Optional[List[RelationshipType]] = None
    tags: Optional[List[str]] = None
    limit: int = 100
    offset: int = 0


@dataclass
class ArxObjectUpdate:
    """Update specification for ArxObjects"""
    object_id: str
    properties: Optional[Dict[str, Any]] = None
    geometry: Optional[ArxObjectGeometry] = None
    add_tags: Optional[List[str]] = None
    remove_tags: Optional[List[str]] = None
    validate_constraints: bool = True


@dataclass
class BulkOperation:
    """Specification for bulk operations"""
    operation_type: str  # create, update, delete
    objects: List[Union[ArxObject, ArxObjectUpdate]]
    transaction_mode: bool = True
    continue_on_error: bool = False


class ArxObjectService:
    """
    High-level service for ArxObject operations.
    
    This service provides:
    - Complex business operations
    - Query orchestration
    - Bulk operations
    - Workflow management
    - Integration with other services
    - Caching and optimization
    """
    
    def __init__(
        self,
        engine: ArxObjectEngine,
        repository: ArxObjectRepository,
        validator: Optional[IntegratedValidator] = None
    ):
        """
        Initialize ArxObject service.
        
        Args:
            engine: ArxObject engine
            repository: ArxObject repository
            validator: Optional integrated validator
        """
        self.engine = engine
        self.repository = repository
        self.validator = validator or IntegratedValidator()
        
        # Caching
        self.cache: Dict[str, ArxObject] = {}
        self.cache_ttl = 300  # 5 minutes
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Statistics
        self.stats = {
            'operations_performed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_failures': 0
        }
        
        logger.info("Initialized ArxObjectService")
    
    # ==========================================
    # Object Creation
    # ==========================================
    
    async def create_object(
        self,
        object_type: ArxObjectType,
        properties: Dict[str, Any],
        geometry: Optional[ArxObjectGeometry] = None,
        relationships: Optional[List[Dict[str, Any]]] = None,
        constraints: Optional[List[Dict[str, Any]]] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> ArxObject:
        """
        Create a new ArxObject with full validation and persistence.
        
        Args:
            object_type: Type of object
            properties: Object properties
            geometry: Optional geometry
            relationships: Optional relationships to create
            constraints: Optional constraints to apply
            tags: Optional tags
            user_id: User performing the operation
            
        Returns:
            Created ArxObject
            
        Raises:
            ValidationError: If object fails validation
            PermissionError: If user lacks permission
        """
        try:
            # Create object in engine
            obj = await self.engine.create_object(
                object_type=object_type,
                properties=properties,
                geometry=geometry,
                relationships=relationships,
                constraints=constraints
            )
            
            # Add tags if provided
            if tags:
                obj.tags = tags
            
            # Persist to database
            await self.repository.create_object(obj, user_id)
            
            # Cache the object
            self._cache_object(obj)
            
            # Update statistics
            self.stats['operations_performed'] += 1
            
            logger.info(f"Created object {obj.id} of type {object_type.value}")
            return obj
            
        except Exception as e:
            logger.error(f"Error creating object: {e}")
            raise
    
    async def create_from_template(
        self,
        template_name: str,
        overrides: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> ArxObject:
        """
        Create an ArxObject from a predefined template.
        
        Args:
            template_name: Name of template to use
            overrides: Optional property overrides
            user_id: User performing the operation
            
        Returns:
            Created ArxObject
        """
        # Load template
        template = await self._load_template(template_name)
        
        # Apply overrides
        if overrides:
            template['properties'].update(overrides.get('properties', {}))
            if 'geometry' in overrides:
                template['geometry'] = overrides['geometry']
        
        # Create object
        return await self.create_object(
            object_type=ArxObjectType(template['object_type']),
            properties=template['properties'],
            geometry=ArxObjectGeometry(**template.get('geometry', {})),
            relationships=template.get('relationships'),
            constraints=template.get('constraints'),
            tags=template.get('tags'),
            user_id=user_id
        )
    
    # ==========================================
    # Object Retrieval
    # ==========================================
    
    async def get_object(
        self,
        object_id: str,
        include_relationships: bool = False,
        include_constraints: bool = False,
        use_cache: bool = True
    ) -> Optional[ArxObject]:
        """
        Retrieve an ArxObject with optional related data.
        
        Args:
            object_id: Object identifier
            include_relationships: Whether to include relationships
            include_constraints: Whether to include constraints
            use_cache: Whether to use cache
            
        Returns:
            ArxObject or None if not found
        """
        # Check cache
        if use_cache and object_id in self.cache:
            if self._is_cache_valid(object_id):
                self.stats['cache_hits'] += 1
                return self.cache[object_id]
        
        self.stats['cache_misses'] += 1
        
        # Get from engine or repository
        obj = await self.engine.get_object(object_id)
        if not obj:
            obj = await self.repository.get_object(object_id)
        
        if obj:
            # Load additional data if requested
            if include_relationships:
                obj.relationships = await self.get_object_relationships(object_id)
            
            if include_constraints:
                obj.constraints = await self.get_object_constraints(object_id)
            
            # Cache the object
            self._cache_object(obj)
        
        return obj
    
    async def query_objects(self, query: ArxObjectQuery) -> List[ArxObject]:
        """
        Query ArxObjects based on multiple criteria.
        
        Args:
            query: Query specification
            
        Returns:
            List of matching ArxObjects
        """
        results = []
        
        # Spatial query takes precedence
        if query.spatial_bounds:
            results = await self.repository.find_in_region(
                *query.spatial_bounds,
                object_types=query.object_types
            )
        elif query.near_point and query.radius:
            result_tuples = await self.repository.find_nearest(
                *query.near_point,
                radius=query.radius,
                limit=query.limit,
                object_types=query.object_types
            )
            results = [obj for obj, _ in result_tuples]
        elif query.object_types:
            # Query by type
            for obj_type in query.object_types:
                type_results = await self.repository.find_by_type(
                    obj_type, 
                    limit=query.limit,
                    offset=query.offset
                )
                results.extend(type_results)
        elif query.property_filters:
            # Query by properties
            results = await self.repository.find_by_properties(
                query.property_filters,
                limit=query.limit
            )
        
        # Apply additional filters
        if query.tags:
            results = [obj for obj in results if any(tag in obj.tags for tag in query.tags)]
        
        # Apply relationship filters if specified
        if query.relationships:
            filtered_results = []
            for obj in results:
                relationships = await self.get_object_relationships(obj.id)
                if any(rel.relationship_type in query.relationships for rel in relationships):
                    filtered_results.append(obj)
            results = filtered_results
        
        # Apply limit and offset
        if query.offset:
            results = results[query.offset:]
        if query.limit:
            results = results[:query.limit]
        
        self.stats['operations_performed'] += 1
        return results
    
    # ==========================================
    # Object Updates
    # ==========================================
    
    async def update_object(
        self,
        update: ArxObjectUpdate,
        user_id: Optional[str] = None
    ) -> ArxObject:
        """
        Update an ArxObject with validation.
        
        Args:
            update: Update specification
            user_id: User performing the operation
            
        Returns:
            Updated ArxObject
            
        Raises:
            ValidationError: If update fails validation
        """
        # Get current object
        obj = await self.get_object(update.object_id, use_cache=False)
        if not obj:
            raise KeyError(f"Object not found: {update.object_id}")
        
        # Apply updates
        if update.properties:
            obj.properties.update(update.properties)
        
        if update.geometry:
            obj.geometry = update.geometry
        
        if update.add_tags:
            obj.tags = list(set(obj.tags + update.add_tags))
        
        if update.remove_tags:
            obj.tags = [tag for tag in obj.tags if tag not in update.remove_tags]
        
        # Validate if requested
        if update.validate_constraints:
            validation_result = await self.engine.validate_constraints(obj.id)
            if not validation_result['valid']:
                self.stats['validation_failures'] += 1
                raise ValueError(f"Validation failed: {validation_result['violations']}")
        
        # Update in engine
        await self.engine.update_object(
            obj.id,
            properties=update.properties,
            geometry=update.geometry,
            validate=update.validate_constraints
        )
        
        # Persist to database
        await self.repository.update_object(obj, user_id)
        
        # Invalidate cache
        self._invalidate_cache(obj.id)
        
        self.stats['operations_performed'] += 1
        return obj
    
    async def update_property(
        self,
        object_id: str,
        property_key: str,
        property_value: Any,
        validate: bool = True,
        user_id: Optional[str] = None
    ) -> ArxObject:
        """
        Update a single property of an ArxObject.
        
        Args:
            object_id: Object identifier
            property_key: Property key to update
            property_value: New property value
            validate: Whether to validate constraints
            user_id: User performing the operation
            
        Returns:
            Updated ArxObject
        """
        update = ArxObjectUpdate(
            object_id=object_id,
            properties={property_key: property_value},
            validate_constraints=validate
        )
        return await self.update_object(update, user_id)
    
    # ==========================================
    # Object Deletion
    # ==========================================
    
    async def delete_object(
        self,
        object_id: str,
        cascade: bool = False,
        soft_delete: bool = True,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Delete an ArxObject.
        
        Args:
            object_id: Object identifier
            cascade: Whether to cascade delete dependencies
            soft_delete: Whether to soft delete (mark inactive)
            user_id: User performing the operation
            
        Returns:
            True if deleted successfully
        """
        # Check dependencies
        if not cascade:
            dependencies = await self.engine.get_object_dependencies(object_id)
            if dependencies:
                raise ValueError(f"Cannot delete: object has {len(dependencies)} dependencies")
        
        # Delete from engine
        await self.engine.delete_object(object_id, cascade=cascade, force=True)
        
        # Delete from repository
        await self.repository.delete_object(object_id, soft_delete=soft_delete, user_id=user_id)
        
        # Invalidate cache
        self._invalidate_cache(object_id)
        
        self.stats['operations_performed'] += 1
        return True
    
    # ==========================================
    # Relationship Operations
    # ==========================================
    
    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: RelationshipType,
        properties: Optional[Dict[str, Any]] = None,
        validate: bool = True
    ) -> ArxObjectRelationship:
        """
        Create a relationship between ArxObjects.
        
        Args:
            source_id: Source object ID
            target_id: Target object ID
            relationship_type: Type of relationship
            properties: Optional relationship properties
            validate: Whether to validate the relationship
            
        Returns:
            Created relationship
        """
        # Validate objects exist
        source = await self.get_object(source_id)
        target = await self.get_object(target_id)
        
        if not source or not target:
            raise KeyError("Source or target object not found")
        
        # Validate relationship if requested
        if validate:
            if not await self._validate_relationship(source, target, relationship_type):
                raise ValueError(f"Invalid relationship: {source_id} {relationship_type.value} {target_id}")
        
        # Create in engine
        relationship = await self.engine.create_relationship(
            source_id, target_id, relationship_type, properties
        )
        
        # Persist to database
        await self.repository.create_relationship(relationship)
        
        # Invalidate cache for both objects
        self._invalidate_cache(source_id)
        self._invalidate_cache(target_id)
        
        return relationship
    
    async def get_object_relationships(
        self,
        object_id: str,
        relationship_type: Optional[RelationshipType] = None,
        direction: str = "both"
    ) -> List[ArxObjectRelationship]:
        """
        Get relationships for an object.
        
        Args:
            object_id: Object identifier
            relationship_type: Optional filter by type
            direction: Filter by direction (both, outgoing, incoming)
            
        Returns:
            List of relationships
        """
        # Try engine first
        relationships = await self.engine.get_object_relationships(
            object_id, relationship_type, direction
        )
        
        # Fall back to repository if needed
        if not relationships:
            relationships = await self.repository.get_relationships(
                object_id, relationship_type
            )
        
        return relationships
    
    async def get_connected_objects(
        self,
        object_id: str,
        relationship_type: Optional[RelationshipType] = None,
        depth: int = 1,
        include_objects: bool = True
    ) -> Union[Set[str], List[ArxObject]]:
        """
        Get objects connected through relationships.
        
        Args:
            object_id: Starting object ID
            relationship_type: Optional filter by relationship type
            depth: How many levels to traverse
            include_objects: If True, return objects; if False, return IDs
            
        Returns:
            Set of object IDs or list of ArxObjects
        """
        connected_ids = await self.engine.get_connected_objects(
            object_id, relationship_type, depth
        )
        
        if not include_objects:
            return connected_ids
        
        # Fetch the actual objects
        objects = []
        for obj_id in connected_ids:
            obj = await self.get_object(obj_id)
            if obj:
                objects.append(obj)
        
        return objects
    
    # ==========================================
    # Constraint Operations
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
        Add a constraint to an ArxObject.
        
        Args:
            object_id: Object identifier
            constraint_type: Type of constraint
            expression: Constraint expression
            parameters: Optional parameters
            severity: Constraint severity
            
        Returns:
            Created constraint
        """
        # Add to engine
        constraint = await self.engine.add_constraint(
            object_id, constraint_type, expression, parameters, severity
        )
        
        # Persist to database
        await self.repository.create_constraint(constraint)
        
        # Invalidate cache
        self._invalidate_cache(object_id)
        
        return constraint
    
    async def get_object_constraints(
        self,
        object_id: str,
        active_only: bool = True
    ) -> List[ArxObjectConstraint]:
        """
        Get constraints for an object.
        
        Args:
            object_id: Object identifier
            active_only: Whether to return only active constraints
            
        Returns:
            List of constraints
        """
        return await self.repository.get_constraints(object_id, active_only)
    
    async def validate_object(
        self,
        object_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate an ArxObject against all constraints.
        
        Args:
            object_id: Object identifier
            context: Optional validation context
            
        Returns:
            Validation result
        """
        result = await self.engine.validate_constraints(object_id, context)
        
        if not result['valid']:
            self.stats['validation_failures'] += 1
        
        return result
    
    # ==========================================
    # Bulk Operations
    # ==========================================
    
    async def bulk_operation(
        self,
        operation: BulkOperation,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform bulk operations on multiple ArxObjects.
        
        Args:
            operation: Bulk operation specification
            user_id: User performing the operation
            
        Returns:
            Operation result summary
        """
        results = {
            'total': len(operation.objects),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        if operation.transaction_mode:
            # Start transaction
            transaction_id = await self.engine.begin_transaction()
        
        try:
            for i, obj_spec in enumerate(operation.objects):
                try:
                    if operation.operation_type == "create":
                        await self.create_object(
                            object_type=obj_spec.object_type,
                            properties=obj_spec.properties,
                            geometry=obj_spec.geometry,
                            user_id=user_id
                        )
                    elif operation.operation_type == "update":
                        await self.update_object(obj_spec, user_id)
                    elif operation.operation_type == "delete":
                        await self.delete_object(obj_spec.id, user_id=user_id)
                    
                    results['successful'] += 1
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'index': i,
                        'error': str(e)
                    })
                    
                    if not operation.continue_on_error:
                        raise
            
            if operation.transaction_mode:
                # Commit transaction
                await self.engine.commit_transaction(transaction_id)
            
        except Exception as e:
            if operation.transaction_mode:
                # Rollback transaction
                await self.engine.rollback_transaction(transaction_id)
            raise
        
        return results
    
    # ==========================================
    # Spatial Operations
    # ==========================================
    
    async def find_spatial_conflicts(
        self,
        object_id: str,
        clearance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Find spatial conflicts for an ArxObject.
        
        Args:
            object_id: Object identifier
            clearance: Required clearance distance
            
        Returns:
            List of conflicts
        """
        return await self.engine.check_spatial_conflicts(object_id, clearance)
    
    async def find_objects_within_distance(
        self,
        object_id: str,
        distance: float,
        object_types: Optional[List[ArxObjectType]] = None
    ) -> List[Tuple[ArxObject, float]]:
        """
        Find objects within a distance from another object.
        
        Args:
            object_id: Reference object ID
            distance: Maximum distance
            object_types: Optional filter by types
            
        Returns:
            List of (object, distance) tuples
        """
        obj = await self.get_object(object_id)
        if not obj:
            return []
        
        return await self.repository.find_nearest(
            obj.geometry.x,
            obj.geometry.y,
            obj.geometry.z,
            radius=distance,
            object_types=object_types
        )
    
    # ==========================================
    # Helper Methods
    # ==========================================
    
    def _cache_object(self, obj: ArxObject) -> None:
        """Cache an ArxObject"""
        self.cache[obj.id] = obj
        self.cache_timestamps[obj.id] = datetime.now(timezone.utc)
    
    def _invalidate_cache(self, object_id: str) -> None:
        """Invalidate cache for an object"""
        if object_id in self.cache:
            del self.cache[object_id]
        if object_id in self.cache_timestamps:
            del self.cache_timestamps[object_id]
    
    def _is_cache_valid(self, object_id: str) -> bool:
        """Check if cached object is still valid"""
        if object_id not in self.cache_timestamps:
            return False
        
        age = (datetime.now(timezone.utc) - self.cache_timestamps[object_id]).total_seconds()
        return age < self.cache_ttl
    
    async def _validate_relationship(
        self,
        source: ArxObject,
        target: ArxObject,
        relationship_type: RelationshipType
    ) -> bool:
        """Validate if a relationship is allowed"""
        # Implement relationship validation rules
        # For example, electrical outlets can only connect to circuits
        if relationship_type == RelationshipType.CONNECTED_TO:
            if source.object_type == ArxObjectType.ELECTRICAL_OUTLET:
                return target.object_type in [
                    ArxObjectType.ELECTRICAL_PANEL,
                    ArxObjectType.ELECTRICAL_CONDUIT
                ]
        
        # Default to allowing the relationship
        return True
    
    async def _load_template(self, template_name: str) -> Dict[str, Any]:
        """Load an object template"""
        # This would load from a template library
        # For now, return a sample template
        templates = {
            "standard-outlet": {
                "object_type": "electrical_outlet",
                "properties": {
                    "voltage": 120,
                    "amperage": 20,
                    "gfci": False,
                    "weatherproof": False
                },
                "geometry": {
                    "length": 0.25,
                    "width": 0.25,
                    "height": 0.1
                },
                "constraints": [
                    {
                        "type": "electrical_load",
                        "expression": "load <= amperage * voltage"
                    }
                ]
            }
        }
        
        if template_name not in templates:
            raise KeyError(f"Template not found: {template_name}")
        
        return templates[template_name]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        engine_stats = self.engine.get_statistics()
        return {
            'service_stats': self.stats,
            'engine_stats': engine_stats,
            'cache_size': len(self.cache)
        }