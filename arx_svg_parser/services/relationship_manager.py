"""
Advanced Relationship Management System for BIM Models

This module provides comprehensive relationship management capabilities for BIM models,
including spatial relationships, system connections, functional dependencies, and
performance optimization with full bidirectional support and reference integrity.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict, deque
import json
import uuid

from structlog import get_logger

from pydantic import BaseModel, Field, field_validator, model_validator

from ..models.bim import (
    BIMElementBase, BIMModel, SystemType, DeviceCategory,
    Room, Wall, Door, Window, HVACZone, AirHandler, VAVBox,
    ElectricalCircuit, ElectricalPanel, ElectricalOutlet,
    PlumbingSystem, PlumbingFixture, Valve,
    FireAlarmSystem, SmokeDetector, SecuritySystem, Camera, Device
)

logger = get_logger()

class RelationshipType(str, Enum):
    """Types of relationships between BIM elements."""
    # Spatial relationships
    CONTAINS = "contains"  # Room contains devices
    ADJACENT = "adjacent"  # Rooms share a wall
    ABOVE = "above"        # Element is above another
    BELOW = "below"        # Element is below another
    INSIDE = "inside"      # Element is inside another
    OUTSIDE = "outside"    # Element is outside another
    
    # System relationships
    CONNECTS_TO = "connects_to"      # Physical connection
    SUPPLIES = "supplies"            # Provides service/utility
    CONTROLS = "controls"            # Control relationship
    MONITORS = "monitors"            # Monitoring relationship
    MONITORED_BY = "monitored_by"    # Monitored by relationship
    BACKS_UP = "backs_up"            # Backup/redundancy
    DEPENDS_ON = "depends_on"        # Dependency relationship
    
    # Functional relationships
    SERVES = "serves"                # Serves a space/function
    REQUIRES = "requires"            # Requires another element
    SUPPORTS = "supports"            # Structural support
    PROTECTS = "protects"            # Protection relationship
    
    # Network relationships
    NETWORK_CONNECTION = "network_connection"  # Network connectivity
    DATA_FLOW = "data_flow"          # Data communication
    SIGNAL_PATH = "signal_path"      # Signal transmission
    
    # Maintenance relationships
    MAINTAINS = "maintains"          # Maintenance responsibility
    REPLACES = "replaces"            # Replacement relationship
    UPGRADES = "upgrades"            # Upgrade relationship
    
    # Enhanced relationship types
    FLOW = "flow"                    # Fluid/air flow
    CONTROL = "control"              # Control system relationship
    ADJACENCY = "adjacency"          # Spatial adjacency
    CONNECTIVITY = "connectivity"    # Network connectivity
    INTERFACE = "interface"          # System interface
    INTEGRATION = "integration"      # System integration
    COORDINATION = "coordination"    # System coordination
    SYNCHRONIZATION = "synchronization"  # System synchronization

class RelationshipDirection(str, Enum):
    """Direction of relationships."""
    BIDIRECTIONAL = "bidirectional"
    UNIDIRECTIONAL = "unidirectional"

class RelationshipStrength(str, Enum):
    """Strength of relationships."""
    CRITICAL = "critical"      # Essential for operation
    IMPORTANT = "important"    # Significant impact
    MODERATE = "moderate"      # Some impact
    MINOR = "minor"           # Minimal impact
    OPTIONAL = "optional"     # Optional relationship

@dataclass
class RelationshipConstraint:
    """Constraints for relationship validation."""
    max_distance: Optional[float] = None
    min_distance: Optional[float] = None
    required_properties: List[str] = None
    forbidden_properties: List[str] = None
    system_compatibility: List[SystemType] = None
    device_compatibility: List[DeviceCategory] = None

class BIMRelationship(BaseModel):
    """Enhanced BIM relationship model with full bidirectional support."""
    relationship_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    relationship_type: RelationshipType
    source_id: str
    target_id: str
    direction: RelationshipDirection = RelationshipDirection.BIDIRECTIONAL
    strength: RelationshipStrength = RelationshipStrength.MODERATE
    
    # Relationship properties
    properties: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Validation and constraints
    constraints: Optional[RelationshipConstraint] = None
    is_valid: bool = True
    validation_errors: List[str] = Field(default_factory=list)
    
    # Bidirectional navigation
    reverse_relationship_id: Optional[str] = None  # For bidirectional relationships
    
    # Performance tracking
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_validated: Optional[datetime] = None
    
    @field_validator('source_id', 'target_id')
    @classmethod
    def validate_ids(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("ID must be a non-empty string")
        return v
    
    @model_validator(mode='after')
    def validate_relationship(self):
        if self.source_id == self.target_id:
            raise ValueError("Source and target cannot be the same")
        return self
    
    def add_property(self, key: str, value: Any):
        """Add a property to the relationship."""
        self.properties[key] = value
        self.updated_at = datetime.now(timezone.utc)
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a property from the relationship."""
        return self.properties.get(key, default)
    
    def get_reverse_relationship_type(self) -> Optional[RelationshipType]:
        """Get the reverse relationship type for bidirectional relationships."""
        reverse_mapping = {
            RelationshipType.CONTAINS: RelationshipType.INSIDE,
            RelationshipType.INSIDE: RelationshipType.CONTAINS,
            RelationshipType.ABOVE: RelationshipType.BELOW,
            RelationshipType.BELOW: RelationshipType.ABOVE,
            RelationshipType.SUPPLIES: RelationshipType.REQUIRES,
            RelationshipType.REQUIRES: RelationshipType.SUPPLIES,
            RelationshipType.CONTROLS: RelationshipType.CONTROL,
            RelationshipType.CONTROL: RelationshipType.CONTROLS,
            RelationshipType.MONITORS: RelationshipType.MONITORED_BY,
            RelationshipType.DEPENDS_ON: RelationshipType.SUPPORTS,
            RelationshipType.SUPPORTS: RelationshipType.DEPENDS_ON,
        }
        return reverse_mapping.get(self.relationship_type)
    
    def validate_against_model(self, bim_model: 'BIMModel') -> bool:
        """Validate this relationship against the BIM model."""
        self.validation_errors.clear()
        
        # Check if source and target exist
        source = bim_model.get_element_by_id(self.source_id)
        target = bim_model.get_element_by_id(self.target_id)
        
        if not source:
            self.validation_errors.append(f"Source element {self.source_id} not found")
        if not target:
            self.validation_errors.append(f"Target element {self.target_id} not found")
        
        if not source or not target:
            self.is_valid = False
            return False
        
        # Validate constraints
        if self.constraints:
            self._validate_constraints(source, target, bim_model)
        
        # Validate relationship type compatibility
        self._validate_relationship_type_compatibility(source, target)
        
        self.is_valid = len(self.validation_errors) == 0
        self.last_validated = datetime.now(timezone.utc)
        return self.is_valid
    
    def _validate_constraints(self, source: BIMElementBase, target: BIMElementBase, bim_model: 'BIMModel'):
        """Validate relationship constraints."""
        if not self.constraints:
            return
        
        # Distance validation
        if self.constraints.max_distance is not None or self.constraints.min_distance is not None:
            distance = self._calculate_distance(source, target)
            if self.constraints.max_distance and distance > self.constraints.max_distance:
                self.validation_errors.append(f"Distance {distance} exceeds maximum {self.constraints.max_distance}")
            if self.constraints.min_distance and distance < self.constraints.min_distance:
                self.validation_errors.append(f"Distance {distance} below minimum {self.constraints.min_distance}")
        
        # System compatibility
        if self.constraints.system_compatibility:
            source_system = getattr(source, 'system_type', None)
            target_system = getattr(target, 'system_type', None)
            if source_system and source_system not in self.constraints.system_compatibility:
                self.validation_errors.append(f"Source system {source_system} not compatible")
            if target_system and target_system not in self.constraints.system_compatibility:
                self.validation_errors.append(f"Target system {target_system} not compatible")
    
    def _validate_relationship_type_compatibility(self, source: BIMElementBase, target: BIMElementBase):
        """Validate that the relationship type is compatible with the element types."""
        # Define compatibility rules
        compatibility_rules = {
            RelationshipType.CONTAINS: {
                'source_types': [Room],
                'target_types': [Device, HVACZone, ElectricalPanel, PlumbingFixture]
            },
            RelationshipType.CONNECTS_TO: {
                'source_types': [Device, ElectricalPanel, PlumbingFixture],
                'target_types': [Device, ElectricalPanel, PlumbingFixture]
            },
            RelationshipType.SUPPLIES: {
                'source_types': [AirHandler, ElectricalPanel, PlumbingSystem],
                'target_types': [VAVBox, ElectricalOutlet, PlumbingFixture]
            },
            RelationshipType.FLOW: {
                'source_types': [Device, PlumbingFixture, HVACZone],
                'target_types': [Device, PlumbingFixture, HVACZone]
            },
            RelationshipType.CONTROL: {
                'source_types': [Device, ElectricalPanel],
                'target_types': [Device, ElectricalPanel]
            },
            RelationshipType.ADJACENCY: {
                'source_types': [Room, Wall, Device],
                'target_types': [Room, Wall, Device]
            },
            RelationshipType.CONNECTIVITY: {
                'source_types': [Device, ElectricalPanel],
                'target_types': [Device, ElectricalPanel]
            }
        }
        
        rule = compatibility_rules.get(self.relationship_type)
        if rule:
            source_type = type(source)
            target_type = type(target)
            
            if rule.get('source_types') and source_type not in rule['source_types']:
                self.validation_errors.append(f"Source type {source_type.__name__} not compatible with {self.relationship_type}")
            if rule.get('target_types') and target_type not in rule['target_types']:
                self.validation_errors.append(f"Target type {target_type.__name__} not compatible with {self.relationship_type}")
    
    def _calculate_distance(self, source: BIMElementBase, target: BIMElementBase) -> float:
        """Calculate distance between two elements."""
        try:
            # Simple distance calculation based on geometry centers
            source_center = self._get_element_center(source)
            target_center = self._get_element_center(target)
            
            if source_center and target_center:
                dx = source_center[0] - target_center[0]
                dy = source_center[1] - target_center[1]
                return (dx * dx + dy * dy) ** 0.5
            
            return 0.0
        except Exception:
            return 0.0
    
    def _get_element_center(self, element: BIMElementBase) -> Optional[Tuple[float, float]]:
        """Get the center point of an element."""
        try:
            if hasattr(element, 'geometry') and element.geometry:
                coords = element.geometry.coordinates
                if coords and len(coords) >= 2:
                    if isinstance(coords[0], (list, tuple)):
                        # Polygon or complex geometry - calculate centroid
                        x_sum = sum(coord[0] for coord in coords)
                        y_sum = sum(coord[1] for coord in coords)
                        return (x_sum / len(coords), y_sum / len(coords))
                    else:
                        # Point geometry
                        return (coords[0], coords[1])
            return None
        except Exception:
            return None

class RelationshipManager:
    """Advanced relationship management system with full bidirectional support."""
    
    def __init__(self, bim_model: BIMModel):
        self.bim_model = bim_model
        self.relationships: Dict[str, BIMRelationship] = {}
        self.relationship_index: Dict[str, Set[str]] = defaultdict(set)
        self.spatial_index: Dict[str, Set[str]] = defaultdict(set)
        self.system_index: Dict[SystemType, Set[str]] = defaultdict(set)
        
        # Bidirectional relationship tracking
        self.bidirectional_pairs: Dict[str, str] = {}  # relationship_id -> reverse_relationship_id
        
        # Reference integrity tracking
        self.reference_errors: List[Dict[str, Any]] = []
        self.repair_log: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.stats = {
            'total_relationships': 0,
            'valid_relationships': 0,
            'invalid_relationships': 0,
            'bidirectional_relationships': 0,
            'reference_errors_fixed': 0,
            'last_validation': None
        }
    
    def add_relationship(self, relationship: BIMRelationship) -> bool:
        """Add a relationship to the manager with bidirectional support."""
        try:
            # Validate the relationship
            if not relationship.validate_against_model(self.bim_model):
                logger.warning(f"Invalid relationship {relationship.relationship_id}: {relationship.validation_errors}")
                self.stats['invalid_relationships'] += 1
                return False
            
            # Add to main storage
            self.relationships[relationship.relationship_id] = relationship
            
            # Create bidirectional relationship if needed
            if relationship.direction == RelationshipDirection.BIDIRECTIONAL:
                self._create_bidirectional_relationship(relationship)
            
            # Update indices
            self._update_indices(relationship)
            
            self.stats['total_relationships'] += 1
            self.stats['valid_relationships'] += 1
            
            logger.info(f"Added relationship {relationship.relationship_id}: {relationship.relationship_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding relationship: {e}")
            return False
    
    def _create_bidirectional_relationship(self, relationship: BIMRelationship):
        """Create the reverse relationship for bidirectional relationships."""
        reverse_type = relationship.get_reverse_relationship_type()
        if reverse_type:
            reverse_relationship = BIMRelationship(
                relationship_id=f"{relationship.relationship_id}_reverse",
                relationship_type=reverse_type,
                source_id=relationship.target_id,
                target_id=relationship.source_id,
                direction=RelationshipDirection.BIDIRECTIONAL,
                strength=relationship.strength,
                properties=relationship.properties.copy(),
                metadata=relationship.metadata.copy(),
                constraints=relationship.constraints
            )
            
            # Link the relationships
            relationship.reverse_relationship_id = reverse_relationship.relationship_id
            reverse_relationship.reverse_relationship_id = relationship.relationship_id
            
            # Store both relationships
            self.relationships[reverse_relationship.relationship_id] = reverse_relationship
            self.bidirectional_pairs[relationship.relationship_id] = reverse_relationship.relationship_id
            self.bidirectional_pairs[reverse_relationship.relationship_id] = relationship.relationship_id
            
            self.stats['bidirectional_relationships'] += 1
            self.stats['total_relationships'] += 1
            self.stats['valid_relationships'] += 1
    
    def remove_relationship(self, relationship_id: str) -> bool:
        """Remove a relationship from the manager."""
        if relationship_id not in self.relationships:
            return False
        
        relationship = self.relationships[relationship_id]
        
        # Remove reverse relationship if it exists
        if relationship.reverse_relationship_id:
            reverse_id = relationship.reverse_relationship_id
            if reverse_id in self.relationships:
                self._remove_single_relationship(reverse_id)
                self.bidirectional_pairs.pop(reverse_id, None)
                self.bidirectional_pairs.pop(relationship_id, None)
        
        # Remove the main relationship
        self._remove_single_relationship(relationship_id)
        
        logger.info(f"Removed relationship {relationship_id}")
        return True
    
    def _remove_single_relationship(self, relationship_id: str):
        """Remove a single relationship without affecting its pair."""
        if relationship_id not in self.relationships:
            return
        
        relationship = self.relationships[relationship_id]
        
        # Remove from indices
        self._remove_from_indices(relationship)
        
        # Remove from main storage
        del self.relationships[relationship_id]
        
        self.stats['total_relationships'] -= 1
        if relationship.is_valid:
            self.stats['valid_relationships'] -= 1
        else:
            self.stats['invalid_relationships'] -= 1
    
    def get_relationships(self, 
                        source_id: Optional[str] = None,
                        target_id: Optional[str] = None,
                        relationship_type: Optional[RelationshipType] = None,
                        system_type: Optional[SystemType] = None,
                        include_reverse: bool = True) -> List[BIMRelationship]:
        """Get relationships based on filters with bidirectional support."""
        results = []
        
        for relationship in self.relationships.values():
            # Skip reverse relationships if not requested
            if not include_reverse and relationship.reverse_relationship_id:
                continue
                
            if source_id and relationship.source_id != source_id:
                continue
            if target_id and relationship.target_id != target_id:
                continue
            if relationship_type and relationship.relationship_type != relationship_type:
                continue
            if system_type:
                source = self.bim_model.get_element_by_id(relationship.source_id)
                target = self.bim_model.get_element_by_id(relationship.target_id)
                if not (source and hasattr(source, 'system_type') and source.system_type == system_type or
                       target and hasattr(target, 'system_type') and target.system_type == system_type):
                    continue
            
            results.append(relationship)
        
        return results
    
    def get_connected_elements(self, element_id: str, 
                             relationship_type: Optional[RelationshipType] = None,
                             bidirectional: bool = True) -> List[BIMElementBase]:
        """Get all elements connected to a given element with bidirectional support."""
        connected_ids = set()
        
        # Get relationships where element is source
        for relationship in self.get_relationships(source_id=element_id, relationship_type=relationship_type):
            connected_ids.add(relationship.target_id)
        
        # Get relationships where element is target
        for relationship in self.get_relationships(target_id=element_id, relationship_type=relationship_type):
            connected_ids.add(relationship.source_id)
        
        # Convert to elements
        elements = []
        for element_id in connected_ids:
            element = self.bim_model.get_element_by_id(element_id)
            if element:
                elements.append(element)
        
        return elements
    
    def find_path(self, start_id: str, end_id: str, 
                  relationship_types: Optional[List[RelationshipType]] = None) -> List[BIMRelationship]:
        """Find a path between two elements using breadth-first search."""
        if start_id == end_id:
            return []
        
        visited = set()
        queue = deque([(start_id, [])])
        
        while queue:
            current_id, path = queue.popleft()
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            # Get all relationships for current element
            relationships = self.get_relationships(source_id=current_id)
            if relationship_types:
                relationships = [r for r in relationships if r.relationship_type in relationship_types]
            
            for relationship in relationships:
                next_id = relationship.target_id
                new_path = path + [relationship]
                
                if next_id == end_id:
                    return new_path
                
                if next_id not in visited:
                    queue.append((next_id, new_path))
            
            # Also check relationships where current is target
            relationships = self.get_relationships(target_id=current_id)
            if relationship_types:
                relationships = [r for r in relationships if r.relationship_type in relationship_types]
            
            for relationship in relationships:
                next_id = relationship.source_id
                new_path = path + [relationship]
                
                if next_id == end_id:
                    return new_path
                
                if next_id not in visited:
                    queue.append((next_id, new_path))
        
        return []  # No path found
    
    def detect_conflicts(self) -> List[Dict[str, Any]]:
        """Detect relationship conflicts."""
        conflicts = []
        
        # Check for circular dependencies
        for relationship in self.relationships.values():
            if relationship.relationship_type in [RelationshipType.DEPENDS_ON, RelationshipType.REQUIRES]:
                path = self.find_path(relationship.target_id, relationship.source_id, 
                                   [RelationshipType.DEPENDS_ON, RelationshipType.REQUIRES])
                if path:
                    conflicts.append({
                        'type': 'circular_dependency',
                        'relationship_id': relationship.relationship_id,
                        'path': [r.relationship_id for r in path],
                        'severity': 'critical'
                    })
        
        # Check for conflicting relationships
        relationship_pairs = {}
        for relationship in self.relationships.values():
            pair_key = tuple(sorted([relationship.source_id, relationship.target_id]))
            if pair_key in relationship_pairs:
                existing = relationship_pairs[pair_key]
                if existing.relationship_type != relationship.relationship_type:
                    conflicts.append({
                        'type': 'conflicting_relationships',
                        'relationship_ids': [existing.relationship_id, relationship.relationship_id],
                        'severity': 'moderate'
                    })
            else:
                relationship_pairs[pair_key] = relationship
        
        return conflicts
    
    def resolve_conflicts(self, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve detected conflicts."""
        resolution_results = {
            'resolved': 0,
            'failed': 0,
            'actions_taken': []
        }
        
        for conflict in conflicts:
            if conflict['type'] == 'circular_dependency':
                # Remove the most recent relationship in the cycle
                relationship_id = conflict['relationship_id']
                if self.remove_relationship(relationship_id):
                    resolution_results['resolved'] += 1
                    resolution_results['actions_taken'].append({
                        'action': 'removed_circular_dependency',
                        'relationship_id': relationship_id
                    })
                else:
                    resolution_results['failed'] += 1
            
            elif conflict['type'] == 'conflicting_relationships':
                # Keep the stronger relationship
                rel1_id, rel2_id = conflict['relationship_ids']
                rel1 = self.relationships.get(rel1_id)
                rel2 = self.relationships.get(rel2_id)
                
                if rel1 and rel2:
                    # Remove the weaker relationship
                    if rel1.strength.value > rel2.strength.value:
                        self.remove_relationship(rel2_id)
                        resolution_results['actions_taken'].append({
                            'action': 'removed_weaker_relationship',
                            'removed_id': rel2_id,
                            'kept_id': rel1_id
                        })
                    else:
                        self.remove_relationship(rel1_id)
                        resolution_results['actions_taken'].append({
                            'action': 'removed_weaker_relationship',
                            'removed_id': rel1_id,
                            'kept_id': rel2_id
                        })
                    resolution_results['resolved'] += 1
        
        return resolution_results
    
    def validate_all_relationships(self) -> Dict[str, Any]:
        """Validate all relationships in the manager."""
        validation_results = {
            'total': len(self.relationships),
            'valid': 0,
            'invalid': 0,
            'errors': []
        }
        
        for relationship in self.relationships.values():
            if relationship.validate_against_model(self.bim_model):
                validation_results['valid'] += 1
            else:
                validation_results['invalid'] += 1
                validation_results['errors'].extend(relationship.validation_errors)
        
        self.stats['last_validation'] = datetime.now(timezone.utc)
        self.stats['valid_relationships'] = validation_results['valid']
        self.stats['invalid_relationships'] = validation_results['invalid']
        
        return validation_results
    
    def export_relationships(self, format: str = 'json') -> str:
        """Export relationships to various formats."""
        if format == 'json':
            data = {
                'relationships': [rel.model_dump() for rel in self.relationships.values()],
                'stats': self.stats,
                'exported_at': datetime.now(timezone.utc).isoformat()
            }
            return json.dumps(data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def import_relationships(self, data: str, format: str = 'json') -> Dict[str, Any]:
        """Import relationships from various formats."""
        import_results = {
            'imported': 0,
            'failed': 0,
            'errors': []
        }
        
        if format == 'json':
            try:
                data_dict = json.loads(data)
                relationships_data = data_dict.get('relationships', [])
                
                for rel_data in relationships_data:
                    try:
                        relationship = BIMRelationship(**rel_data)
                        if self.add_relationship(relationship):
                            import_results['imported'] += 1
                        else:
                            import_results['failed'] += 1
                    except Exception as e:
                        import_results['failed'] += 1
                        import_results['errors'].append(str(e))
                
            except Exception as e:
                import_results['errors'].append(f"Failed to parse data: {e}")
        
        return import_results
    
    def _update_indices(self, relationship: BIMRelationship):
        """Update all indices for a relationship."""
        # Update relationship index
        self.relationship_index[relationship.source_id].add(relationship.relationship_id)
        self.relationship_index[relationship.target_id].add(relationship.relationship_id)
        
        # Update spatial index for spatial relationships
        if relationship.relationship_type in [
            RelationshipType.CONTAINS, RelationshipType.ADJACENT, 
            RelationshipType.ABOVE, RelationshipType.BELOW,
            RelationshipType.INSIDE, RelationshipType.OUTSIDE
        ]:
            self.spatial_index[relationship.source_id].add(relationship.relationship_id)
            self.spatial_index[relationship.target_id].add(relationship.relationship_id)
        
        # Update system index
        source = self.bim_model.get_element_by_id(relationship.source_id)
        target = self.bim_model.get_element_by_id(relationship.target_id)
        
        if source and hasattr(source, 'system_type'):
            self.system_index[source.system_type].add(relationship.relationship_id)
        if target and hasattr(target, 'system_type'):
            self.system_index[target.system_type].add(relationship.relationship_id)
    
    def _remove_from_indices(self, relationship: BIMRelationship):
        """Remove a relationship from all indices."""
        # Remove from relationship index
        self.relationship_index[relationship.source_id].discard(relationship.relationship_id)
        self.relationship_index[relationship.target_id].discard(relationship.relationship_id)
        
        # Remove from spatial index
        self.spatial_index[relationship.source_id].discard(relationship.relationship_id)
        self.spatial_index[relationship.target_id].discard(relationship.relationship_id)
        
        # Remove from system index
        source = self.bim_model.get_element_by_id(relationship.source_id)
        target = self.bim_model.get_element_by_id(relationship.target_id)
        
        if source and hasattr(source, 'system_type'):
            self.system_index[source.system_type].discard(relationship.relationship_id)
        if target and hasattr(target, 'system_type'):
            self.system_index[target.system_type].discard(relationship.relationship_id)

    def validate_reference_integrity(self) -> Dict[str, Any]:
        """Validate all relationship references and return integrity report."""
        integrity_report = {
            'total_relationships': len(self.relationships),
            'valid_references': 0,
            'invalid_references': 0,
            'missing_elements': set(),
            'orphaned_relationships': [],
            'errors': []
        }
        
        for relationship_id, relationship in self.relationships.items():
            # Check source element exists
            source = self.bim_model.get_element_by_id(relationship.source_id)
            if not source:
                integrity_report['invalid_references'] += 1
                integrity_report['missing_elements'].add(relationship.source_id)
                integrity_report['orphaned_relationships'].append(relationship_id)
                integrity_report['errors'].append(f"Source element {relationship.source_id} not found")
            
            # Check target element exists
            target = self.bim_model.get_element_by_id(relationship.target_id)
            if not target:
                integrity_report['invalid_references'] += 1
                integrity_report['missing_elements'].add(relationship.target_id)
                integrity_report['orphaned_relationships'].append(relationship_id)
                integrity_report['errors'].append(f"Target element {relationship.target_id} not found")
            
            if source and target:
                integrity_report['valid_references'] += 1
        
        return integrity_report
    
    def repair_reference_integrity(self, auto_repair: bool = True) -> Dict[str, Any]:
        """Repair reference integrity issues."""
        repair_report = {
            'relationships_removed': 0,
            'relationships_repaired': 0,
            'errors_fixed': 0,
            'repair_actions': []
        }
        
        # Get integrity report
        integrity_report = self.validate_reference_integrity()
        
        if integrity_report['invalid_references'] == 0:
            return repair_report
        
        # Repair orphaned relationships
        for relationship_id in integrity_report['orphaned_relationships']:
            if relationship_id in self.relationships:
                relationship = self.relationships[relationship_id]
                
                if auto_repair:
                    # Remove the relationship
                    self._remove_single_relationship(relationship_id)
                    repair_report['relationships_removed'] += 1
                    repair_report['repair_actions'].append(f"Removed orphaned relationship {relationship_id}")
                    
                    # Log the repair
                    self.repair_log.append({
                        'action': 'remove_orphaned_relationship',
                        'relationship_id': relationship_id,
                        'reason': 'missing_elements',
                        'timestamp': datetime.now(timezone.utc)
                    })
                else:
                    # Mark as invalid but keep for manual review
                    relationship.is_valid = False
                    relationship.validation_errors.append("Orphaned relationship - elements not found")
                    repair_report['relationships_repaired'] += 1
                    repair_report['repair_actions'].append(f"Marked relationship {relationship_id} as invalid")
        
        repair_report['errors_fixed'] = len(integrity_report['orphaned_relationships'])
        self.stats['reference_errors_fixed'] += repair_report['errors_fixed']
        
        logger.info(f"Reference integrity repair completed: {repair_report}")
        return repair_report 