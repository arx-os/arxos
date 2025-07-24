"""
Assembly Management System for SVGX Engine

Provides multi-part assembly capabilities including assembly creation,
component placement, constraints, interference checking, and validation.

CTO Directives:
- Enterprise-grade assembly management
- Multi-part assembly capabilities
- Component placement and positioning
- Assembly constraints and relationships
- Interference checking and validation
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any, Set
from decimal import Decimal
import logging

from .precision_system import PrecisionPoint, PrecisionLevel
from .constraint_system import Constraint, ConstraintType

logger = logging.getLogger(__name__)

class AssemblyStatus(Enum):
    """Assembly Status"""
    VALID = "valid"
    INVALID = "invalid"
    OVER_CONSTRAINED = "over_constrained"
    UNDER_CONSTRAINED = "under_constrained"
    INTERFERENCE = "interference"
    PENDING = "pending"

class ComponentStatus(Enum):
    """Component Status"""
    PLACED = "placed"
    UNPLACED = "unplaced"
    CONSTRAINED = "constrained"
    FLOATING = "floating"
    FIXED = "fixed"

@dataclass
class Component:
    """Assembly component"""
    component_id: str
    name: str
    geometry: Dict[str, Any]
    position: PrecisionPoint
    rotation: Decimal = Decimal('0.0')  # radians
    scale: Decimal = Decimal('1.0')
    status: ComponentStatus = ComponentStatus.UNPLACED
    constraints: List[str] = field(default_factory=list)
    parent_assembly: Optional[str] = None
    children: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def get_bounding_box(self) -> Dict[str, PrecisionPoint]:
        """Get component bounding box"""
        # This would calculate the actual bounding box based on geometry
        # For now, return a simple bounding box
        return {
            'min': PrecisionPoint(self.position.x - 10, self.position.y - 10),
            'max': PrecisionPoint(self.position.x + 10, self.position.y + 10)
        }
    
    def transform_point(self, point: PrecisionPoint) -> PrecisionPoint:
        """Transform point by component transformation"""
        # Apply rotation
        cos_rot = Decimal(str(math.cos(float(self.rotation))))
        sin_rot = Decimal(str(math.sin(float(self.rotation))))
        
        # Rotate point
        rotated_x = point.x * cos_rot - point.y * sin_rot
        rotated_y = point.x * sin_rot + point.y * cos_rot
        
        # Apply scale
        scaled_x = rotated_x * self.scale
        scaled_y = rotated_y * self.scale
        
        # Apply translation
        final_x = scaled_x + self.position.x
        final_y = scaled_y + self.position.y
        
        return PrecisionPoint(final_x, final_y)
    
    def get_transformed_geometry(self) -> Dict[str, Any]:
        """Get geometry with applied transformations"""
        transformed_geometry = self.geometry.copy()
        
        # Apply transformations to geometry points
        if 'points' in transformed_geometry:
            transformed_geometry['points'] = [
                self.transform_point(PrecisionPoint(p['x'], p['y']))
                for p in transformed_geometry['points']
            ]
        
        if 'center' in transformed_geometry:
            center = transformed_geometry['center']
            transformed_geometry['center'] = self.transform_point(
                PrecisionPoint(center['x'], center['y'])
            )
        
        return transformed_geometry

@dataclass
class AssemblyConstraint:
    """Assembly constraint between components"""
    constraint_id: str
    constraint_type: ConstraintType
    component1: str
    component2: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    
    def validate(self) -> bool:
        """Validate assembly constraint"""
        return self.component1 != self.component2 and self.constraint_type in [
            ConstraintType.COINCIDENT,
            ConstraintType.DISTANCE,
            ConstraintType.ANGLE,
            ConstraintType.PARALLEL,
            ConstraintType.PERPENDICULAR
        ]

@dataclass
class Assembly:
    """Assembly definition"""
    assembly_id: str
    name: str
    components: Dict[str, Component] = field(default_factory=dict)
    constraints: List[AssemblyConstraint] = field(default_factory=list)
    status: AssemblyStatus = AssemblyStatus.PENDING
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def add_component(self, component: Component) -> bool:
        """Add component to assembly"""
        if component.component_id not in self.components:
            self.components[component.component_id] = component
            component.parent_assembly = self.assembly_id
            logger.info(f"Added component: {component.name}")
            return True
        return False
    
    def remove_component(self, component_id: str) -> bool:
        """Remove component from assembly"""
        if component_id in self.components:
            component = self.components[component_id]
            # Remove component constraints
            self.constraints = [c for c in self.constraints 
                              if c.component1 != component_id and c.component2 != component_id]
            del self.components[component_id]
            logger.info(f"Removed component: {component.name}")
            return True
        return False
    
    def add_constraint(self, constraint: AssemblyConstraint) -> bool:
        """Add constraint to assembly"""
        if constraint.validate():
            self.constraints.append(constraint)
            logger.info(f"Added constraint: {constraint.constraint_type.value}")
            return True
        return False
    
    def get_component_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get all component positions"""
        positions = {}
        for component_id, component in self.components.items():
            positions[component_id] = {
                'position': component.position.to_dict(),
                'rotation': float(component.rotation),
                'scale': float(component.scale),
                'status': component.status.value
            }
        return positions

class InterferenceChecker:
    """Interference checking system"""
    
    def __init__(self):
        self.tolerance = Decimal('0.001')  # Sub-millimeter tolerance
        
    def check_interference(self, component1: Component, component2: Component) -> bool:
        """Check for interference between two components"""
        try:
            # Get bounding boxes
            bbox1 = component1.get_bounding_box()
            bbox2 = component2.get_bounding_box()
            
            # Check for bounding box overlap
            if self._bounding_boxes_overlap(bbox1, bbox2):
                # Perform detailed interference check
                return self._detailed_interference_check(component1, component2)
            
            return False
            
        except Exception as e:
            logger.error(f"Interference check error: {e}")
            return False
    
    def _bounding_boxes_overlap(self, bbox1: Dict[str, PrecisionPoint], 
                               bbox2: Dict[str, PrecisionPoint]) -> bool:
        """Check if bounding boxes overlap"""
        return not (bbox1['max'].x < bbox2['min'].x or bbox1['min'].x > bbox2['max'].x or
                   bbox1['max'].y < bbox2['min'].y or bbox1['min'].y > bbox2['max'].y)
    
    def _detailed_interference_check(self, component1: Component, 
                                   component2: Component) -> bool:
        """Perform detailed interference check"""
        # This is a simplified implementation
        # In a real system, this would perform detailed geometric intersection tests
        
        # Check if components are too close
        distance = component1.position.distance_to(component2.position)
        min_distance = Decimal('1.0')  # Minimum distance between components
        
        return distance < min_distance
    
    def check_assembly_interference(self, assembly: Assembly) -> List[Tuple[str, str]]:
        """Check for interference in entire assembly"""
        interference_pairs = []
        component_ids = list(assembly.components.keys())
        
        for i in range(len(component_ids)):
            for j in range(i + 1, len(component_ids)):
                comp1 = assembly.components[component_ids[i]]
                comp2 = assembly.components[component_ids[j]]
                
                if self.check_interference(comp1, comp2):
                    interference_pairs.append((component_ids[i], component_ids[j]))
        
        return interference_pairs

class AssemblyValidator:
    """Assembly validation system"""
    
    def __init__(self):
        self.interference_checker = InterferenceChecker()
    
    def validate_assembly(self, assembly: Assembly) -> bool:
        """Validate assembly"""
        try:
            # Check component validity
            for component in assembly.components.values():
                if not self._validate_component(component):
                    return False
            
            # Check constraint validity
            for constraint in assembly.constraints:
                if not self._validate_constraint(constraint, assembly):
                    return False
            
            # Check for interference
            interference_pairs = self.interference_checker.check_assembly_interference(assembly)
            if interference_pairs:
                assembly.status = AssemblyStatus.INTERFERENCE
                logger.warning(f"Assembly has interference: {interference_pairs}")
                return False
            
            # Check constraint consistency
            if not self._check_constraint_consistency(assembly):
                assembly.status = AssemblyStatus.OVER_CONSTRAINED
                return False
            
            assembly.status = AssemblyStatus.VALID
            return True
            
        except Exception as e:
            logger.error(f"Assembly validation error: {e}")
            assembly.status = AssemblyStatus.INVALID
            return False
    
    def _validate_component(self, component: Component) -> bool:
        """Validate component"""
        try:
            # Check position validity
            if not isinstance(component.position, PrecisionPoint):
                return False
            
            # Check rotation validity
            if not (Decimal('0') <= component.rotation <= Decimal(str(2 * math.pi))):
                return False
            
            # Check scale validity
            if component.scale <= 0:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Component validation error: {e}")
            return False
    
    def _validate_constraint(self, constraint: AssemblyConstraint, 
                           assembly: Assembly) -> bool:
        """Validate constraint"""
        try:
            # Check if components exist
            if constraint.component1 not in assembly.components:
                return False
            if constraint.component2 not in assembly.components:
                return False
            
            # Check constraint type validity
            return constraint.validate()
            
        except Exception as e:
            logger.error(f"Constraint validation error: {e}")
            return False
    
    def _check_constraint_consistency(self, assembly: Assembly) -> bool:
        """Check constraint consistency"""
        # This is a simplified implementation
        # In a real system, this would check for over/under-constrained systems
        
        component_count = len(assembly.components)
        constraint_count = len(assembly.constraints)
        
        # Basic check: constraints should not exceed reasonable limit
        if constraint_count > component_count * 3:
            return False
        
        return True

class AssemblyManager:
    """Main assembly management system"""
    
    def __init__(self):
        self.assemblies: Dict[str, Assembly] = {}
        self.validator = AssemblyValidator()
        self.interference_checker = InterferenceChecker()
        
        logger.info("Assembly manager initialized")
    
    def create_assembly(self, name: str) -> Assembly:
        """Create new assembly"""
        assembly_id = f"assembly_{len(self.assemblies)}"
        
        assembly = Assembly(
            assembly_id=assembly_id,
            name=name
        )
        
        self.assemblies[assembly_id] = assembly
        logger.info(f"Created assembly: {name}")
        return assembly
    
    def add_component_to_assembly(self, assembly_id: str, component: Component) -> bool:
        """Add component to assembly"""
        if assembly_id in self.assemblies:
            assembly = self.assemblies[assembly_id]
            return assembly.add_component(component)
        return False
    
    def add_constraint_to_assembly(self, assembly_id: str, constraint: AssemblyConstraint) -> bool:
        """Add constraint to assembly"""
        if assembly_id in self.assemblies:
            assembly = self.assemblies[assembly_id]
            return assembly.add_constraint(constraint)
        return False
    
    def validate_assembly(self, assembly_id: str) -> bool:
        """Validate assembly"""
        if assembly_id in self.assemblies:
            assembly = self.assemblies[assembly_id]
            return self.validator.validate_assembly(assembly)
        return False
    
    def check_assembly_interference(self, assembly_id: str) -> List[Tuple[str, str]]:
        """Check assembly interference"""
        if assembly_id in self.assemblies:
            assembly = self.assemblies[assembly_id]
            return self.interference_checker.check_assembly_interference(assembly)
        return []
    
    def get_assembly_info(self, assembly_id: str) -> Dict[str, Any]:
        """Get assembly information"""
        if assembly_id in self.assemblies:
            assembly = self.assemblies[assembly_id]
            return {
                'assembly_id': assembly.assembly_id,
                'name': assembly.name,
                'component_count': len(assembly.components),
                'constraint_count': len(assembly.constraints),
                'status': assembly.status.value,
                'components': list(assembly.components.keys()),
                'positions': assembly.get_component_positions()
            }
        return {}
    
    def get_all_assemblies(self) -> Dict[str, Dict[str, Any]]:
        """Get all assemblies information"""
        return {
            assembly_id: self.get_assembly_info(assembly_id)
            for assembly_id in self.assemblies.keys()
        }
    
    def validate_all_assemblies(self) -> bool:
        """Validate all assemblies"""
        all_valid = True
        for assembly_id in self.assemblies.keys():
            if not self.validate_assembly(assembly_id):
                all_valid = False
        
        return all_valid

# Global instance for easy access
assembly_manager = AssemblyManager() 