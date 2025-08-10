"""
Constraint Engine for Real-Time Evaluation.

High-performance constraint evaluation system that integrates with Phase 1
spatial indexing for intelligent Building-Infrastructure-as-Code validation.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Set, Union, Callable, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import weakref

# Import Phase 1 foundation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.spatial import SpatialConflictEngine, ArxObject, ArxObjectType, BoundingBox3D
from .constraint_core import (
    Constraint, ConstraintType, ConstraintSeverity, ConstraintScope,
    ConstraintResult, ConstraintViolation
)

logger = logging.getLogger(__name__)


@dataclass
class ConstraintEvaluationContext:
    """
    Context for constraint evaluation with access to spatial data and services.
    
    Provides constraints with access to the spatial engine, related objects,
    building codes, and evaluation parameters.
    """
    
    # Core services
    spatial_engine: SpatialConflictEngine
    
    # Evaluation parameters
    evaluation_scope: ConstraintScope = ConstraintScope.OBJECT
    target_systems: Optional[Set[ArxObjectType]] = None
    spatial_bounds: Optional[BoundingBox3D] = None
    
    # Performance settings
    max_objects_per_batch: int = 1000
    enable_parallel_evaluation: bool = True
    evaluation_timeout_seconds: float = 30.0
    
    # Building context
    building_codes: Dict[str, Any] = field(default_factory=dict)
    project_requirements: Dict[str, Any] = field(default_factory=dict)
    design_standards: Dict[str, Any] = field(default_factory=dict)
    
    # Caching and optimization
    enable_result_caching: bool = True
    cache_ttl_seconds: float = 300.0  # 5 minutes
    
    # User context
    user_role: str = "architect"
    evaluation_timestamp: float = field(default_factory=time.time)
    
    def get_related_objects(self, 
                           target_object: ArxObject,
                           relationship_type: str = "spatial",
                           search_radius: float = 50.0) -> List[ArxObject]:
        """
        Get objects related to target object.
        
        Args:
            target_object: Object to find relationships for
            relationship_type: Type of relationship ('spatial', 'system', 'functional')
            search_radius: Search radius in feet
            
        Returns:
            List of related ArxObjects
        """
        if relationship_type == "spatial":
            # Use spatial engine to find nearby objects
            search_bounds = BoundingBox3D(
                target_object.geometry.x - search_radius, target_object.geometry.x + search_radius,
                target_object.geometry.y - search_radius, target_object.geometry.y + search_radius,
                target_object.geometry.z - search_radius/2, target_object.geometry.z + search_radius/2
            )
            nearby_objects = self.spatial_engine.octree.query_range(search_bounds)
            return [obj for obj in nearby_objects if obj.id != target_object.id]
        
        elif relationship_type == "system":
            # Find objects of same system type
            return [
                obj for obj in self.spatial_engine.objects.values()
                if (obj.type == target_object.type and 
                    obj.id != target_object.id)
            ]
        
        elif relationship_type == "functional":
            # Find functionally related objects (e.g., outlets connected to same panel)
            related = []
            if hasattr(target_object, 'metadata') and target_object.metadata:
                # Check for functional relationships in metadata
                connected_to = target_object.metadata.connected_to
                depends_on = target_object.metadata.depends_on
                
                all_related_ids = set(connected_to + depends_on)
                for obj_id in all_related_ids:
                    if obj_id in self.spatial_engine.objects:
                        related.append(self.spatial_engine.objects[obj_id])
            
            return related
        
        return []
    
    def get_building_code_requirement(self, code_section: str, default: Any = None) -> Any:
        """Get building code requirement value."""
        return self.building_codes.get(code_section, default)
    
    def get_project_requirement(self, requirement_key: str, default: Any = None) -> Any:
        """Get project-specific requirement value."""
        return self.project_requirements.get(requirement_key, default)


class ConstraintEngine:
    """
    High-performance constraint evaluation engine.
    
    Integrates with Phase 1 spatial indexing for real-time constraint validation
    across large building models with intelligent batching and caching.
    """
    
    def __init__(self, 
                 spatial_engine: SpatialConflictEngine,
                 max_workers: int = 4,
                 enable_caching: bool = True):
        """
        Initialize constraint engine.
        
        Args:
            spatial_engine: Phase 1 spatial conflict engine
            max_workers: Maximum parallel evaluation workers
            enable_caching: Enable result caching
        """
        self.spatial_engine = spatial_engine
        self.max_workers = max_workers
        self.enable_caching = enable_caching
        
        # Constraint registry
        self.constraints: Dict[str, Constraint] = {}
        self.constraints_by_type: Dict[ConstraintType, List[Constraint]] = defaultdict(list)
        self.constraints_by_scope: Dict[ConstraintScope, List[Constraint]] = defaultdict(list)
        
        # Performance optimization
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._evaluation_cache: Dict[str, Tuple[ConstraintResult, float]] = {}
        self._cache_lock = threading.RLock()
        
        # Performance metrics
        self.metrics = {
            'constraints_registered': 0,
            'evaluations_performed': 0,
            'total_evaluation_time_ms': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'violations_detected': 0,
            'average_batch_size': 0.0
        }
        
        # Event system for real-time updates
        self.violation_callbacks: List[Callable[[ConstraintViolation], None]] = []
        
        logger.info(f"Initialized ConstraintEngine with {max_workers} workers, caching: {enable_caching}")
    
    def register_constraint(self, constraint: Constraint) -> None:
        """
        Register constraint for evaluation.
        
        Args:
            constraint: Constraint to register
        """
        self.constraints[constraint.constraint_id] = constraint
        self.constraints_by_type[constraint.constraint_type].append(constraint)
        self.constraints_by_scope[constraint.scope].append(constraint)
        
        self.metrics['constraints_registered'] += 1
        
        logger.debug(f"Registered constraint: {constraint.name} ({constraint.constraint_type.value})")
    
    def unregister_constraint(self, constraint_id: str) -> bool:
        """
        Unregister constraint.
        
        Args:
            constraint_id: ID of constraint to unregister
            
        Returns:
            True if constraint was removed
        """
        if constraint_id not in self.constraints:
            return False
        
        constraint = self.constraints[constraint_id]
        
        # Remove from all registries
        del self.constraints[constraint_id]
        self.constraints_by_type[constraint.constraint_type].remove(constraint)
        self.constraints_by_scope[constraint.scope].remove(constraint)
        
        # Clear cache entries for this constraint
        with self._cache_lock:
            keys_to_remove = [k for k in self._evaluation_cache.keys() if k.startswith(constraint_id)]
            for key in keys_to_remove:
                del self._evaluation_cache[key]
        
        logger.debug(f"Unregistered constraint: {constraint.name}")
        return True
    
    def evaluate_object_constraints(self, 
                                   arxobject: ArxObject,
                                   constraint_types: Optional[Set[ConstraintType]] = None,
                                   context: Optional[ConstraintEvaluationContext] = None) -> List[ConstraintResult]:
        """
        Evaluate all applicable constraints for a single object.
        
        Args:
            arxobject: Object to evaluate constraints against
            constraint_types: Specific constraint types to evaluate (None for all)
            context: Evaluation context
            
        Returns:
            List of constraint results
        """
        start_time = time.time()
        
        # Create default context if not provided
        if context is None:
            context = ConstraintEvaluationContext(
                spatial_engine=self.spatial_engine,
                evaluation_scope=ConstraintScope.OBJECT
            )
        
        # Find applicable constraints
        applicable_constraints = self._find_applicable_constraints(
            arxobject, constraint_types, ConstraintScope.OBJECT
        )
        
        results = []
        
        for constraint in applicable_constraints:
            if not constraint.enabled:
                continue
            
            # Check cache first
            cache_key = f"{constraint.constraint_id}_{arxobject.id}"
            cached_result = self._get_cached_result(cache_key)
            
            if cached_result:
                results.append(cached_result)
                self.metrics['cache_hits'] += 1
                continue
            
            # Evaluate constraint
            try:
                result = constraint.evaluate(context, [arxobject])
                
                # Cache result
                if self.enable_caching:
                    self._cache_result(cache_key, result)
                
                results.append(result)
                self.metrics['cache_misses'] += 1
                
                # Update constraint performance metrics
                evaluation_time = (time.time() - start_time) * 1000
                constraint.update_performance_metrics(evaluation_time, len(result.violations))
                
                # Fire violation callbacks
                for violation in result.violations:
                    self._fire_violation_callbacks(violation)
                
            except Exception as e:
                logger.error(f"Error evaluating constraint {constraint.name} on object {arxobject.id}: {e}")
                continue
        
        # Update engine metrics
        total_time = (time.time() - start_time) * 1000
        self.metrics['evaluations_performed'] += len(results)
        self.metrics['total_evaluation_time_ms'] += total_time
        self.metrics['violations_detected'] += sum(len(r.violations) for r in results)
        
        logger.debug(f"Evaluated {len(results)} constraints for object {arxobject.id} in {total_time:.1f}ms")
        
        return results
    
    def evaluate_spatial_constraints(self,
                                    spatial_bounds: BoundingBox3D,
                                    constraint_types: Optional[Set[ConstraintType]] = None,
                                    context: Optional[ConstraintEvaluationContext] = None) -> List[ConstraintResult]:
        """
        Evaluate spatial constraints within given bounds.
        
        Args:
            spatial_bounds: Spatial area to evaluate
            constraint_types: Specific constraint types to evaluate
            context: Evaluation context
            
        Returns:
            List of constraint results
        """
        start_time = time.time()
        
        # Get objects within bounds
        objects_in_bounds = self.spatial_engine.octree.query_range(spatial_bounds)
        
        if not objects_in_bounds:
            return []
        
        # Create context with spatial bounds
        if context is None:
            context = ConstraintEvaluationContext(
                spatial_engine=self.spatial_engine,
                evaluation_scope=ConstraintScope.ZONE,
                spatial_bounds=spatial_bounds
            )
        
        # Find spatial constraints
        spatial_constraint_types = {
            ConstraintType.SPATIAL_DISTANCE,
            ConstraintType.SPATIAL_CLEARANCE,
            ConstraintType.SPATIAL_ALIGNMENT,
            ConstraintType.SPATIAL_CONTAINMENT,
            ConstraintType.SPATIAL_ADJACENCY
        }
        
        if constraint_types:
            spatial_constraint_types &= constraint_types
        
        applicable_constraints = []
        for constraint_type in spatial_constraint_types:
            applicable_constraints.extend(self.constraints_by_type.get(constraint_type, []))
        
        results = []
        
        # Evaluate constraints with batch processing
        batch_size = min(context.max_objects_per_batch, len(objects_in_bounds))
        
        for i in range(0, len(objects_in_bounds), batch_size):
            batch_objects = objects_in_bounds[i:i + batch_size]
            
            for constraint in applicable_constraints:
                if not constraint.enabled:
                    continue
                
                try:
                    result = constraint.evaluate(context, batch_objects)
                    results.append(result)
                    
                    # Fire violation callbacks
                    for violation in result.violations:
                        self._fire_violation_callbacks(violation)
                        
                except Exception as e:
                    logger.error(f"Error evaluating spatial constraint {constraint.name}: {e}")
                    continue
        
        total_time = (time.time() - start_time) * 1000
        self.metrics['evaluations_performed'] += len(results)
        self.metrics['total_evaluation_time_ms'] += total_time
        
        logger.info(f"Evaluated {len(results)} spatial constraints for {len(objects_in_bounds)} objects in {total_time:.1f}ms")
        
        return results
    
    async def evaluate_constraints_async(self,
                                       target_objects: List[ArxObject],
                                       constraint_types: Optional[Set[ConstraintType]] = None,
                                       context: Optional[ConstraintEvaluationContext] = None) -> List[ConstraintResult]:
        """
        Asynchronously evaluate constraints with parallel processing.
        
        Args:
            target_objects: Objects to evaluate
            constraint_types: Specific constraint types
            context: Evaluation context
            
        Returns:
            List of constraint results
        """
        if context is None:
            context = ConstraintEvaluationContext(
                spatial_engine=self.spatial_engine,
                evaluation_scope=ConstraintScope.OBJECT
            )
        
        # Create evaluation tasks
        loop = asyncio.get_event_loop()
        tasks = []
        
        for arxobject in target_objects:
            task = loop.run_in_executor(
                self.thread_pool,
                self.evaluate_object_constraints,
                arxobject, constraint_types, context
            )
            tasks.append(task)
        
        # Wait for all evaluations to complete
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results and handle exceptions
        all_results = []
        for results in results_lists:
            if isinstance(results, Exception):
                logger.error(f"Async constraint evaluation error: {results}")
                continue
            all_results.extend(results)
        
        return all_results
    
    def evaluate_system_constraints(self,
                                   system_type: ArxObjectType,
                                   constraint_types: Optional[Set[ConstraintType]] = None,
                                   context: Optional[ConstraintEvaluationContext] = None) -> List[ConstraintResult]:
        """
        Evaluate constraints for entire building system.
        
        Args:
            system_type: Building system to evaluate
            constraint_types: Specific constraint types
            context: Evaluation context
            
        Returns:
            List of constraint results
        """
        # Get all objects of system type
        system_objects = [
            obj for obj in self.spatial_engine.objects.values()
            if obj.type == system_type
        ]
        
        if not system_objects:
            return []
        
        # Create system-scoped context
        if context is None:
            context = ConstraintEvaluationContext(
                spatial_engine=self.spatial_engine,
                evaluation_scope=ConstraintScope.SYSTEM,
                target_systems={system_type}
            )
        
        # Find system constraints
        system_constraint_types = {
            ConstraintType.SYSTEM_CAPACITY,
            ConstraintType.SYSTEM_INTERDEPENDENCY,
            ConstraintType.SYSTEM_SEQUENCE,
            ConstraintType.SYSTEM_COMPATIBILITY
        }
        
        if constraint_types:
            system_constraint_types &= constraint_types
        
        results = []
        
        for constraint_type in system_constraint_types:
            constraints = self.constraints_by_type.get(constraint_type, [])
            
            for constraint in constraints:
                if not constraint.enabled:
                    continue
                
                # Check if constraint applies to this system
                affected_systems = constraint.get_affected_systems()
                if affected_systems and system_type not in affected_systems:
                    continue
                
                try:
                    result = constraint.evaluate(context, system_objects)
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error evaluating system constraint {constraint.name}: {e}")
                    continue
        
        logger.info(f"Evaluated {len(results)} system constraints for {system_type.value}")
        
        return results
    
    def _find_applicable_constraints(self,
                                   arxobject: ArxObject,
                                   constraint_types: Optional[Set[ConstraintType]],
                                   scope: ConstraintScope) -> List[Constraint]:
        """Find constraints applicable to object."""
        applicable = []
        
        # Get constraints by scope
        scope_constraints = self.constraints_by_scope.get(scope, [])
        
        for constraint in scope_constraints:
            # Filter by constraint type if specified
            if constraint_types and constraint.constraint_type not in constraint_types:
                continue
            
            # Check if constraint applies to this object
            if constraint.is_applicable(arxobject):
                applicable.append(constraint)
        
        return applicable
    
    def _get_cached_result(self, cache_key: str) -> Optional[ConstraintResult]:
        """Get cached constraint result if valid."""
        if not self.enable_caching:
            return None
        
        with self._cache_lock:
            if cache_key in self._evaluation_cache:
                result, timestamp = self._evaluation_cache[cache_key]
                
                # Check if cache entry is still valid
                if time.time() - timestamp < 300.0:  # 5 minute TTL
                    return result
                else:
                    # Remove expired entry
                    del self._evaluation_cache[cache_key]
        
        return None
    
    def _cache_result(self, cache_key: str, result: ConstraintResult) -> None:
        """Cache constraint evaluation result."""
        if not self.enable_caching:
            return
        
        with self._cache_lock:
            self._evaluation_cache[cache_key] = (result, time.time())
            
            # Limit cache size (simple LRU)
            if len(self._evaluation_cache) > 10000:
                # Remove oldest 1000 entries
                sorted_items = sorted(self._evaluation_cache.items(), key=lambda x: x[1][1])
                for i in range(1000):
                    if i < len(sorted_items):
                        del self._evaluation_cache[sorted_items[i][0]]
    
    def _fire_violation_callbacks(self, violation: ConstraintViolation) -> None:
        """Fire violation callbacks for real-time updates."""
        for callback in self.violation_callbacks:
            try:
                callback(violation)
            except Exception as e:
                logger.error(f"Error in violation callback: {e}")
    
    def add_violation_callback(self, callback: Callable[[ConstraintViolation], None]) -> None:
        """Add callback for real-time violation notifications."""
        self.violation_callbacks.append(callback)
    
    def remove_violation_callback(self, callback: Callable[[ConstraintViolation], None]) -> None:
        """Remove violation callback."""
        if callback in self.violation_callbacks:
            self.violation_callbacks.remove(callback)
    
    def get_constraint_summary(self) -> Dict[str, Any]:
        """Get summary of registered constraints."""
        type_counts = defaultdict(int)
        scope_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for constraint in self.constraints.values():
            type_counts[constraint.constraint_type.value] += 1
            scope_counts[constraint.scope.value] += 1
            severity_counts[constraint.severity.value] += 1
        
        return {
            'total_constraints': len(self.constraints),
            'enabled_constraints': sum(1 for c in self.constraints.values() if c.enabled),
            'by_type': dict(type_counts),
            'by_scope': dict(scope_counts),
            'by_severity': dict(severity_counts),
            'performance_metrics': self.metrics.copy()
        }
    
    def clear_cache(self) -> int:
        """Clear evaluation cache and return number of entries cleared."""
        with self._cache_lock:
            count = len(self._evaluation_cache)
            self._evaluation_cache.clear()
            return count
    
    def shutdown(self) -> None:
        """Shutdown constraint engine and cleanup resources."""
        logger.info("Shutting down ConstraintEngine...")
        
        self.thread_pool.shutdown(wait=True)
        self.clear_cache()
        self.violation_callbacks.clear()
        
        logger.info("ConstraintEngine shutdown complete")