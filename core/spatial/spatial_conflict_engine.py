"""
Spatial Conflict Resolution Engine.

Advanced conflict detection and resolution system for ArxObjects using both
3D Octree and 2D R-tree spatial indices with constraint propagation and
automated resolution strategies.
"""

import time
import math
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import defaultdict, deque
import json

from .octree_index import OctreeIndex, BoundingBox3D
from .rtree_index import RTreeIndex, BoundingBox2D
from .arxobject_core import ArxObject, ArxObjectType, ArxObjectPrecision

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of spatial conflicts between ArxObjects."""
    
    # Geometric conflicts
    OVERLAP = "overlap"                    # Objects physically overlap
    COLLISION = "collision"                # Objects intersect
    PROXIMITY = "proximity"                # Objects too close together
    CLEARANCE = "clearance"               # Insufficient clearance space
    
    # System-based conflicts  
    SAME_SYSTEM = "same_system"           # Same system type conflict
    CROSS_SYSTEM = "cross_system"         # Different system conflict
    PRIORITY_VIOLATION = "priority"       # Lower priority blocking higher priority
    
    # Code-based conflicts
    CODE_VIOLATION = "code_violation"     # Building code violation
    ACCESSIBILITY = "accessibility"       # ADA accessibility issue
    FIRE_SAFETY = "fire_safety"          # Fire safety code violation
    STRUCTURAL = "structural"             # Structural integrity issue
    
    # Installation conflicts
    INSTALL_ORDER = "install_order"       # Installation sequence conflict
    ACCESS_REQUIRED = "access_required"   # Access needed for installation/maintenance
    TOOL_CLEARANCE = "tool_clearance"    # Insufficient space for tools


@dataclass
class ConflictReport:
    """Detailed conflict analysis report."""
    
    object1_id: str
    object2_id: str
    conflict_type: ConflictType
    severity: str  # critical, high, medium, low
    description: str
    geometry_overlap: float = 0.0  # Volume/area of overlap
    distance: float = 0.0          # Distance between objects
    resolution_strategy: Optional[str] = None
    resolution_cost: float = 0.0
    resolution_time_hours: float = 0.0
    code_references: List[str] = None
    
    def __post_init__(self):
        if self.code_references is None:
            self.code_references = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'object1_id': self.object1_id,
            'object2_id': self.object2_id,
            'conflict_type': self.conflict_type.value,
            'severity': self.severity,
            'description': self.description,
            'geometry_overlap': self.geometry_overlap,
            'distance': self.distance,
            'resolution_strategy': self.resolution_strategy,
            'resolution_cost': self.resolution_cost,
            'resolution_time_hours': self.resolution_time_hours,
            'code_references': self.code_references
        }


class ConstraintEngine:
    """Constraint propagation engine for automated conflict resolution."""
    
    def __init__(self):
        self.constraints: Dict[str, Dict[str, Any]] = {}
        self.system_rules: Dict[str, List[Dict[str, Any]]] = {}
        self.code_rules: List[Dict[str, Any]] = []
        self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> None:
        """Initialize default system and code constraints."""
        
        # System priority rules
        self.system_rules = {
            'structural': [
                {'min_clearance_ft': 0.5, 'priority': 1, 'immovable': True}
            ],
            'life_safety': [
                {'min_clearance_ft': 2.0, 'priority': 2, 'access_required': True}
            ],
            'electrical': [
                {'min_clearance_ft': 0.25, 'priority': 3, 'code_spacing': True}
            ],
            'hvac': [
                {'min_clearance_ft': 1.0, 'priority': 3, 'maintenance_access': True}
            ],
            'plumbing': [
                {'min_clearance_ft': 0.5, 'priority': 3, 'slope_required': True}
            ],
            'telecommunications': [
                {'min_clearance_ft': 0.125, 'priority': 4, 'separation_from_power': True}
            ],
            'finishes': [
                {'min_clearance_ft': 0.0, 'priority': 5, 'cosmetic': True}
            ]
        }
        
        # Building code rules
        self.code_rules = [
            {
                'name': 'ADA_Clearance',
                'description': 'ADA accessibility clearance requirements',
                'min_clearance_ft': 2.5,
                'applies_to': ['emergency_exit', 'access_control'],
                'code_reference': 'ADA 2010 Section 404.2.3'
            },
            {
                'name': 'Fire_Sprinkler_Coverage',
                'description': 'Fire sprinkler coverage requirements',
                'max_spacing_ft': 15.0,
                'applies_to': ['fire_sprinkler'],
                'code_reference': 'NFPA 13 Section 8.6.2'
            },
            {
                'name': 'Electrical_Separation',
                'description': 'Electrical separation from other systems',
                'min_separation_ft': 0.25,
                'applies_to': ['electrical_conduit', 'electrical_panel'],
                'code_reference': 'NEC 300.3(C)(2)(c)'
            }
        ]
    
    def evaluate_constraint_violations(self, obj1: ArxObject, obj2: ArxObject) -> List[Dict[str, Any]]:
        """Evaluate constraint violations between two objects."""
        violations = []
        
        # System-based constraint evaluation
        system1_rules = self.system_rules.get(obj1.get_system_type(), [])
        system2_rules = self.system_rules.get(obj2.get_system_type(), [])
        
        # Check minimum clearance requirements
        distance = obj1.distance_to_point(*obj2.get_center())
        
        for rules in [system1_rules, system2_rules]:
            for rule in rules:
                min_clearance = rule.get('min_clearance_ft', 0.0)
                if distance < min_clearance:
                    violations.append({
                        'type': 'clearance_violation',
                        'required_clearance': min_clearance,
                        'actual_distance': distance,
                        'system_rule': rule,
                        'severity': 'high' if rule.get('priority', 5) <= 2 else 'medium'
                    })
        
        # Code-based constraint evaluation  
        for code_rule in self.code_rules:
            applies_to1 = obj1.type.value in code_rule.get('applies_to', [])
            applies_to2 = obj2.type.value in code_rule.get('applies_to', [])
            
            if applies_to1 or applies_to2:
                required_clearance = code_rule.get('min_clearance_ft', 0.0)
                required_separation = code_rule.get('min_separation_ft', 0.0)
                
                if distance < max(required_clearance, required_separation):
                    violations.append({
                        'type': 'code_violation',
                        'code_rule': code_rule['name'],
                        'description': code_rule['description'],
                        'code_reference': code_rule['code_reference'],
                        'required_distance': max(required_clearance, required_separation),
                        'actual_distance': distance,
                        'severity': 'critical'
                    })
        
        return violations
    
    def suggest_resolution(self, obj1: ArxObject, obj2: ArxObject, 
                          violations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Suggest resolution strategy for constraint violations."""
        if not violations:
            return None
        
        # Determine which object should be moved based on priority
        priority1 = obj1.get_system_priority()
        priority2 = obj2.get_system_priority()
        
        # Higher priority (lower number) objects stay in place
        if priority1 < priority2:
            move_object = obj2
            fixed_object = obj1
        elif priority2 < priority1:
            move_object = obj1
            fixed_object = obj2
        else:
            # Same priority - move the one installed later or with lower cost
            if obj1.metadata.installation_cost <= obj2.metadata.installation_cost:
                move_object = obj1
                fixed_object = obj2
            else:
                move_object = obj2
                fixed_object = obj1
        
        # Calculate required movement distance
        max_required_distance = max(v.get('required_distance', 0.0) for v in violations)
        current_distance = move_object.distance_to_point(*fixed_object.get_center())
        required_movement = max_required_distance - current_distance
        
        # Suggest movement direction (away from fixed object)
        fixed_center = fixed_object.get_center()
        move_center = move_object.get_center()
        
        dx = move_center[0] - fixed_center[0]
        dy = move_center[1] - fixed_center[1]
        dz = move_center[2] - fixed_center[2]
        
        # Normalize direction vector
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        if distance > 0:
            dx /= distance
            dy /= distance
            dz /= distance
        
        # Calculate new position
        new_x = move_center[0] + (dx * required_movement)
        new_y = move_center[1] + (dy * required_movement)
        new_z = move_center[2] + (dz * required_movement)
        
        # Estimate resolution cost and time
        move_cost = self._estimate_move_cost(move_object, required_movement)
        move_time_hours = self._estimate_move_time(move_object, required_movement)
        
        return {
            'strategy': 'relocate_object',
            'move_object_id': move_object.id,
            'new_position': [new_x, new_y, new_z],
            'movement_distance': required_movement,
            'estimated_cost': move_cost,
            'estimated_time_hours': move_time_hours,
            'violations_resolved': len(violations),
            'confidence': 0.8  # Resolution confidence score
        }
    
    def _estimate_move_cost(self, obj: ArxObject, distance: float) -> float:
        """Estimate cost to relocate an ArxObject."""
        base_cost = obj.metadata.installation_cost * 0.1  # 10% of installation cost
        distance_factor = min(distance / 10.0, 2.0)  # Cap at 2x for long moves
        system_factor = {
            'structural': 5.0,     # Very expensive to move
            'life_safety': 3.0,    # Expensive due to code requirements
            'electrical': 2.0,     # Moderate cost
            'hvac': 2.5,          # Higher due to ductwork
            'plumbing': 3.0,      # Higher due to pipe routing
            'telecommunications': 1.5,  # Lower cost
            'finishes': 1.0       # Lowest cost
        }.get(obj.get_system_type(), 2.0)
        
        return base_cost * distance_factor * system_factor
    
    def _estimate_move_time(self, obj: ArxObject, distance: float) -> float:
        """Estimate time in hours to relocate an ArxObject."""
        base_time = {
            'structural': 24.0,        # 1-3 days
            'life_safety': 8.0,        # 1 day
            'electrical': 4.0,         # Half day
            'hvac': 6.0,              # 3/4 day
            'plumbing': 8.0,          # 1 day
            'telecommunications': 2.0,  # Few hours
            'finishes': 1.0           # 1 hour
        }.get(obj.get_system_type(), 4.0)
        
        distance_factor = min(distance / 5.0, 3.0)  # Cap at 3x for long moves
        return base_time * distance_factor


class SpatialConflictEngine:
    """
    Advanced spatial conflict detection and resolution engine.
    
    Combines 3D Octree and 2D R-tree spatial indices with constraint
    propagation for comprehensive conflict analysis and automated resolution.
    """
    
    def __init__(self, world_bounds: BoundingBox3D, max_workers: int = 8):
        """
        Initialize spatial conflict engine.
        
        Args:
            world_bounds: 3D bounding box for the building space
            max_workers: Number of worker threads for parallel processing
        """
        self.world_bounds = world_bounds
        self.max_workers = max_workers
        
        # Spatial indices
        self.octree = OctreeIndex(world_bounds, max_objects=15, max_depth=12)
        self.rtree = RTreeIndex(max_entries=15)
        
        # Constraint engine
        self.constraint_engine = ConstraintEngine()
        
        # Object storage and tracking
        self.objects: Dict[str, ArxObject] = {}
        self.system_layers: Dict[str, Set[str]] = defaultdict(set)  # system -> object_ids
        self.floor_layers: Dict[str, Set[str]] = defaultdict(set)   # floor_id -> object_ids
        
        # Conflict tracking
        self.active_conflicts: Dict[str, ConflictReport] = {}  # conflict_key -> report
        self.resolved_conflicts: List[ConflictReport] = []
        self.conflict_cache: Dict[str, List[ConflictReport]] = {}
        
        # Performance tracking
        self.stats = {
            'total_objects': 0,
            'total_conflicts_detected': 0,
            'total_conflicts_resolved': 0,
            'average_detection_time': 0.0,
            'cache_hit_rate': 0.0,
            'parallel_efficiency': 0.0
        }
        
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.RLock()
        
        logger.info(f"Initialized SpatialConflictEngine with bounds {world_bounds}, "
                   f"max_workers={max_workers}")
    
    def add_arxobject(self, arxobject: ArxObject) -> bool:
        """
        Add ArxObject to spatial conflict engine.
        
        Args:
            arxobject: ArxObject to add
            
        Returns:
            bool: True if successfully added
        """
        start_time = time.time()
        
        try:
            with self._lock:
                # Check if object already exists
                if arxobject.id in self.objects:
                    logger.warning(f"ArxObject {arxobject.id} already exists")
                    return False
                
                # Add to spatial indices
                octree_success = self.octree.insert(arxobject)
                rtree_success = self.rtree.insert(arxobject)
                
                if not (octree_success and rtree_success):
                    # Rollback on partial failure
                    self.octree.remove(arxobject)
                    self.rtree.remove(arxobject)
                    return False
                
                # Store object and update tracking
                self.objects[arxobject.id] = arxobject
                self.system_layers[arxobject.get_system_type()].add(arxobject.id)
                
                if arxobject.floor_id:
                    self.floor_layers[arxobject.floor_id].add(arxobject.id)
                
                self.stats['total_objects'] += 1
                
                # Detect conflicts with newly added object
                conflicts = self.detect_conflicts(arxobject)
                if conflicts:
                    logger.info(f"Added ArxObject {arxobject.id}, detected {len(conflicts)} conflicts")
                else:
                    logger.debug(f"Added ArxObject {arxobject.id} without conflicts")
                
                elapsed = time.time() - start_time
                logger.debug(f"Added ArxObject {arxobject.id} in {elapsed:.4f}s")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to add ArxObject {arxobject.id}: {e}")
            return False
    
    def remove_arxobject(self, arxobject_id: str) -> bool:
        """
        Remove ArxObject from spatial conflict engine.
        
        Args:
            arxobject_id: ID of ArxObject to remove
            
        Returns:
            bool: True if successfully removed
        """
        try:
            with self._lock:
                if arxobject_id not in self.objects:
                    return False
                
                arxobject = self.objects[arxobject_id]
                
                # Remove from spatial indices
                self.octree.remove(arxobject)
                self.rtree.remove(arxobject)
                
                # Remove from tracking
                del self.objects[arxobject_id]
                self.system_layers[arxobject.get_system_type()].discard(arxobject_id)
                
                if arxobject.floor_id:
                    self.floor_layers[arxobject.floor_id].discard(arxobject_id)
                
                # Remove related conflicts
                conflicts_to_remove = [k for k in self.active_conflicts.keys() 
                                     if arxobject_id in k]
                for conflict_key in conflicts_to_remove:
                    self.resolved_conflicts.append(self.active_conflicts[conflict_key])
                    del self.active_conflicts[conflict_key]
                
                # Clear cache entries
                cache_keys_to_remove = [k for k in self.conflict_cache.keys() 
                                       if arxobject_id in k]
                for cache_key in cache_keys_to_remove:
                    del self.conflict_cache[cache_key]
                
                self.stats['total_objects'] -= 1
                
                logger.info(f"Removed ArxObject {arxobject_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to remove ArxObject {arxobject_id}: {e}")
            return False
    
    def detect_conflicts(self, arxobject: ArxObject, 
                        tolerance: Optional[float] = None) -> List[ConflictReport]:
        """
        Detect spatial conflicts for a single ArxObject.
        
        Args:
            arxobject: ArxObject to check for conflicts
            tolerance: Custom tolerance (uses object precision if None)
            
        Returns:
            List of conflict reports
        """
        start_time = time.time()
        conflicts = []
        
        try:
            # Use object precision if no tolerance specified
            if tolerance is None:
                tolerance = arxobject.get_tolerance()
            
            # Check cache first
            cache_key = f"{arxobject.id}_{arxobject.version}_{tolerance}"
            if cache_key in self.conflict_cache:
                self.stats['cache_hit_rate'] = (self.stats.get('cache_hit_rate', 0.0) + 1) / 2
                return self.conflict_cache[cache_key]
            
            # 3D conflict detection using Octree
            octree_conflicts = self.octree.find_conflicts(arxobject, tolerance)
            
            # 2D plan view conflict detection using R-tree
            rtree_conflicts = self.rtree.find_plan_view_conflicts(arxobject, tolerance)
            
            # Combine and deduplicate conflicts
            all_candidates = set()
            conflict_types = {}
            
            for candidate, conflict_type in octree_conflicts:
                all_candidates.add(candidate.id)
                conflict_types[candidate.id] = conflict_type
            
            for candidate, conflict_type in rtree_conflicts:
                if candidate.id not in all_candidates:
                    all_candidates.add(candidate.id)
                    conflict_types[candidate.id] = conflict_type
                else:
                    # Combine conflict types
                    existing_type = conflict_types[candidate.id]
                    if conflict_type != existing_type:
                        conflict_types[candidate.id] = f"{existing_type}_and_{conflict_type}"
            
            # Detailed conflict analysis
            for candidate_id in all_candidates:
                candidate = self.objects[candidate_id]
                detailed_conflicts = self._analyze_detailed_conflict(arxobject, candidate, tolerance)
                conflicts.extend(detailed_conflicts)
            
            # Cache results
            self.conflict_cache[cache_key] = conflicts
            
            # Update statistics
            elapsed = time.time() - start_time
            self.stats['average_detection_time'] = (
                (self.stats['average_detection_time'] + elapsed) / 2
            )
            
            # Store active conflicts
            for conflict in conflicts:
                conflict_key = f"{conflict.object1_id}_{conflict.object2_id}_{conflict.conflict_type.value}"
                self.active_conflicts[conflict_key] = conflict
                self.stats['total_conflicts_detected'] += 1
            
            logger.debug(f"Detected {len(conflicts)} conflicts for {arxobject.id} in {elapsed:.4f}s")
            
            return conflicts
            
        except Exception as e:
            logger.error(f"Conflict detection failed for {arxobject.id}: {e}")
            return []
    
    def batch_detect_conflicts(self, arxobject_ids: Optional[List[str]] = None) -> Dict[str, List[ConflictReport]]:
        """
        Detect conflicts for multiple ArxObjects in parallel.
        
        Args:
            arxobject_ids: List of object IDs to check (all objects if None)
            
        Returns:
            Dictionary mapping object_id -> list of conflicts
        """
        start_time = time.time()
        
        if arxobject_ids is None:
            arxobject_ids = list(self.objects.keys())
        
        logger.info(f"Starting batch conflict detection for {len(arxobject_ids)} objects")
        
        results = {}
        
        # Submit parallel detection tasks
        future_to_id = {}
        for obj_id in arxobject_ids:
            if obj_id in self.objects:
                future = self.executor.submit(self.detect_conflicts, self.objects[obj_id])
                future_to_id[future] = obj_id
        
        # Collect results
        completed = 0
        for future in as_completed(future_to_id):
            obj_id = future_to_id[future]
            try:
                conflicts = future.result()
                results[obj_id] = conflicts
                completed += 1
                
                if completed % 1000 == 0:
                    logger.info(f"Completed conflict detection for {completed}/{len(arxobject_ids)} objects")
                    
            except Exception as e:
                logger.error(f"Conflict detection failed for object {obj_id}: {e}")
                results[obj_id] = []
        
        elapsed = time.time() - start_time
        total_conflicts = sum(len(conflicts) for conflicts in results.values())
        
        logger.info(f"Batch conflict detection completed: {total_conflicts} conflicts found "
                   f"across {len(arxobject_ids)} objects in {elapsed:.2f}s "
                   f"({len(arxobject_ids)/elapsed:.0f} objects/sec)")
        
        # Update parallel efficiency metric
        theoretical_time = sum(self.stats.get('average_detection_time', 0.1) 
                             for _ in arxobject_ids)
        if theoretical_time > 0:
            self.stats['parallel_efficiency'] = theoretical_time / (elapsed * self.max_workers)
        
        return results
    
    def _analyze_detailed_conflict(self, obj1: ArxObject, obj2: ArxObject, 
                                  tolerance: float) -> List[ConflictReport]:
        """Perform detailed conflict analysis between two objects."""
        conflicts = []
        
        # Basic geometric analysis
        distance = obj1.distance_to_point(*obj2.get_center())
        bbox1 = obj1.get_bounding_box()
        bbox2 = obj2.get_bounding_box()
        
        # Check for geometric conflicts
        if bbox1.intersects(bbox2):
            overlap_volume = self._calculate_overlap_volume(bbox1, bbox2)
            
            conflicts.append(ConflictReport(
                object1_id=obj1.id,
                object2_id=obj2.id,
                conflict_type=ConflictType.OVERLAP,
                severity=self._determine_severity(obj1, obj2, overlap_volume),
                description=f"{obj1.type.value} overlaps with {obj2.type.value}",
                geometry_overlap=overlap_volume,
                distance=distance
            ))
        
        # Check clearance requirements
        if distance < tolerance:
            conflicts.append(ConflictReport(
                object1_id=obj1.id,
                object2_id=obj2.id,
                conflict_type=ConflictType.CLEARANCE,
                severity='medium',
                description=f"Insufficient clearance between {obj1.type.value} and {obj2.type.value}",
                geometry_overlap=0.0,
                distance=distance
            ))
        
        # Constraint-based analysis
        constraint_violations = self.constraint_engine.evaluate_constraint_violations(obj1, obj2)
        
        for violation in constraint_violations:
            conflict_type = ConflictType.CODE_VIOLATION if violation['type'] == 'code_violation' else ConflictType.CLEARANCE
            
            conflict = ConflictReport(
                object1_id=obj1.id,
                object2_id=obj2.id,
                conflict_type=conflict_type,
                severity=violation['severity'],
                description=violation.get('description', f"Constraint violation: {violation['type']}"),
                geometry_overlap=0.0,
                distance=distance
            )
            
            if 'code_reference' in violation:
                conflict.code_references.append(violation['code_reference'])
            
            # Suggest resolution
            resolution = self.constraint_engine.suggest_resolution(obj1, obj2, [violation])
            if resolution:
                conflict.resolution_strategy = resolution['strategy']
                conflict.resolution_cost = resolution['estimated_cost']
                conflict.resolution_time_hours = resolution['estimated_time_hours']
            
            conflicts.append(conflict)
        
        return conflicts
    
    def _calculate_overlap_volume(self, bbox1: BoundingBox3D, bbox2: BoundingBox3D) -> float:
        """Calculate intersection volume of two bounding boxes."""
        if not bbox1.intersects(bbox2):
            return 0.0
        
        # Calculate intersection bounds
        min_x = max(bbox1.min_x, bbox2.min_x)
        max_x = min(bbox1.max_x, bbox2.max_x)
        min_y = max(bbox1.min_y, bbox2.min_y)
        max_y = min(bbox1.max_y, bbox2.max_y)
        min_z = max(bbox1.min_z, bbox2.min_z)
        max_z = min(bbox1.max_z, bbox2.max_z)
        
        # Calculate volume
        if min_x < max_x and min_y < max_y and min_z < max_z:
            return (max_x - min_x) * (max_y - min_y) * (max_z - min_z)
        
        return 0.0
    
    def _determine_severity(self, obj1: ArxObject, obj2: ArxObject, overlap_volume: float) -> str:
        """Determine conflict severity based on system priorities and overlap."""
        # System priority based severity
        min_priority = min(obj1.get_system_priority(), obj2.get_system_priority())
        
        if min_priority <= 2:  # Structural or life safety
            base_severity = 'critical'
        elif min_priority == 3:  # MEP systems
            base_severity = 'high'
        elif min_priority == 4:  # Distribution
            base_severity = 'medium'
        else:  # Finishes
            base_severity = 'low'
        
        # Adjust based on overlap volume
        obj1_volume = obj1.get_volume()
        obj2_volume = obj2.get_volume()
        min_volume = min(obj1_volume, obj2_volume)
        
        if min_volume > 0:
            overlap_ratio = overlap_volume / min_volume
            if overlap_ratio > 0.5:  # More than 50% overlap
                if base_severity == 'low':
                    base_severity = 'medium'
                elif base_severity == 'medium':
                    base_severity = 'high'
        
        return base_severity
    
    def resolve_conflicts(self, conflict_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Attempt to resolve spatial conflicts automatically.
        
        Args:
            conflict_ids: Specific conflicts to resolve (all if None)
            
        Returns:
            Resolution summary with statistics
        """
        start_time = time.time()
        
        if conflict_ids is None:
            conflicts_to_resolve = list(self.active_conflicts.values())
        else:
            conflicts_to_resolve = [self.active_conflicts[cid] for cid in conflict_ids 
                                  if cid in self.active_conflicts]
        
        logger.info(f"Starting automated conflict resolution for {len(conflicts_to_resolve)} conflicts")
        
        resolved_count = 0
        failed_count = 0
        total_cost = 0.0
        total_time_hours = 0.0
        
        # Sort conflicts by severity and priority
        conflicts_to_resolve.sort(key=lambda c: (
            {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[c.severity],
            -c.resolution_cost if c.resolution_cost else 0
        ))
        
        for conflict in conflicts_to_resolve:
            try:
                success = self._attempt_conflict_resolution(conflict)
                if success:
                    resolved_count += 1
                    total_cost += conflict.resolution_cost
                    total_time_hours += conflict.resolution_time_hours
                    
                    # Move to resolved conflicts
                    conflict_key = f"{conflict.object1_id}_{conflict.object2_id}_{conflict.conflict_type.value}"
                    if conflict_key in self.active_conflicts:
                        del self.active_conflicts[conflict_key]
                    self.resolved_conflicts.append(conflict)
                    
                    logger.debug(f"Resolved conflict between {conflict.object1_id} and {conflict.object2_id}")
                else:
                    failed_count += 1
                    logger.debug(f"Failed to resolve conflict between {conflict.object1_id} and {conflict.object2_id}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"Error resolving conflict: {e}")
        
        elapsed = time.time() - start_time
        self.stats['total_conflicts_resolved'] += resolved_count
        
        summary = {
            'conflicts_processed': len(conflicts_to_resolve),
            'resolved_count': resolved_count,
            'failed_count': failed_count,
            'success_rate': resolved_count / len(conflicts_to_resolve) if conflicts_to_resolve else 0.0,
            'total_cost': total_cost,
            'total_time_hours': total_time_hours,
            'processing_time_seconds': elapsed
        }
        
        logger.info(f"Conflict resolution completed: {resolved_count}/{len(conflicts_to_resolve)} resolved "
                   f"in {elapsed:.2f}s, estimated cost: ${total_cost:.2f}")
        
        return summary
    
    def _attempt_conflict_resolution(self, conflict: ConflictReport) -> bool:
        """Attempt to resolve a specific conflict."""
        if not conflict.resolution_strategy:
            return False
        
        try:
            if conflict.resolution_strategy == 'relocate_object':
                # For now, we'll simulate successful resolution
                # In a full implementation, this would move the actual object
                logger.debug(f"Simulating relocation resolution for conflict {conflict.object1_id}-{conflict.object2_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Resolution attempt failed: {e}")
            return False
    
    def get_system_conflicts(self, system_type: str) -> List[ConflictReport]:
        """Get all conflicts involving a specific system type."""
        conflicts = []
        
        for conflict in self.active_conflicts.values():
            obj1 = self.objects.get(conflict.object1_id)
            obj2 = self.objects.get(conflict.object2_id)
            
            if obj1 and obj1.get_system_type() == system_type:
                conflicts.append(conflict)
            elif obj2 and obj2.get_system_type() == system_type:
                conflicts.append(conflict)
        
        return conflicts
    
    def get_floor_conflicts(self, floor_id: str) -> List[ConflictReport]:
        """Get all conflicts on a specific floor."""
        conflicts = []
        floor_object_ids = self.floor_layers.get(floor_id, set())
        
        for conflict in self.active_conflicts.values():
            if (conflict.object1_id in floor_object_ids or 
                conflict.object2_id in floor_object_ids):
                conflicts.append(conflict)
        
        return conflicts
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive conflict engine statistics."""
        octree_stats = self.octree.get_statistics()
        rtree_stats = self.rtree.get_statistics()
        
        # Conflict statistics
        conflicts_by_type = defaultdict(int)
        conflicts_by_severity = defaultdict(int)
        
        for conflict in self.active_conflicts.values():
            conflicts_by_type[conflict.conflict_type.value] += 1
            conflicts_by_severity[conflict.severity] += 1
        
        return {
            'engine_stats': self.stats,
            'spatial_indices': {
                'octree': octree_stats,
                'rtree': rtree_stats
            },
            'conflicts': {
                'active_conflicts': len(self.active_conflicts),
                'resolved_conflicts': len(self.resolved_conflicts),
                'conflicts_by_type': dict(conflicts_by_type),
                'conflicts_by_severity': dict(conflicts_by_severity)
            },
            'objects': {
                'total_objects': len(self.objects),
                'objects_by_system': {k: len(v) for k, v in self.system_layers.items()},
                'objects_by_floor': {k: len(v) for k, v in self.floor_layers.items()}
            },
            'cache': {
                'cache_entries': len(self.conflict_cache),
                'cache_hit_rate': self.stats.get('cache_hit_rate', 0.0)
            }
        }
    
    def optimize(self) -> None:
        """Optimize spatial indices and clear caches."""
        logger.info("Starting spatial conflict engine optimization...")
        start_time = time.time()
        
        # Optimize spatial indices
        self.octree.optimize()
        self.rtree.optimize()
        
        # Clear stale cache entries
        self.conflict_cache.clear()
        
        elapsed = time.time() - start_time
        logger.info(f"Optimization completed in {elapsed:.2f}s")
    
    def clear(self) -> None:
        """Clear all data from conflict engine."""
        with self._lock:
            self.octree.clear()
            self.rtree.clear()
            self.objects.clear()
            self.system_layers.clear()
            self.floor_layers.clear()
            self.active_conflicts.clear()
            self.resolved_conflicts.clear()
            self.conflict_cache.clear()
            
            self.stats = {
                'total_objects': 0,
                'total_conflicts_detected': 0,
                'total_conflicts_resolved': 0,
                'average_detection_time': 0.0,
                'cache_hit_rate': 0.0,
                'parallel_efficiency': 0.0
            }
        
        logger.info("Cleared spatial conflict engine")
    
    def export_conflicts(self, format: str = 'json') -> str:
        """Export conflict data in specified format."""
        conflicts_data = [conflict.to_dict() for conflict in self.active_conflicts.values()]
        
        if format == 'json':
            return json.dumps({
                'active_conflicts': conflicts_data,
                'statistics': self.get_statistics(),
                'export_timestamp': time.time()
            }, indent=2)
        
        # Add support for other formats (CSV, XML) as needed
        return json.dumps(conflicts_data, indent=2)
    
    def __len__(self) -> int:
        """Return number of objects in conflict engine."""
        return len(self.objects)
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)