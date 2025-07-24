"""
SVGX Engine - Assembly Management System

This module implements the assembly management system for CAD-parity functionality,
providing multi-part assemblies with component placement and relationships.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import math
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .precision_drawing_system import PrecisionPoint, PrecisionVector, PrecisionLevel

logger = logging.getLogger(__name__)


class ComponentType(Enum):
    """Types of assembly components."""
    PART = "part"
    SUB_ASSEMBLY = "sub_assembly"
    STANDARD_PART = "standard_part"
    CUSTOM_PART = "custom_part"


class AssemblyConstraintType(Enum):
    """Types of assembly constraints."""
    COINCIDENT = "coincident"
    PARALLEL = "parallel"
    PERPENDICULAR = "perpendicular"
    ANGLE = "angle"
    DISTANCE = "distance"
    TANGENT = "tangent"
    CONCENTRIC = "concentric"


class AssemblyStatus(Enum):
    """Assembly status."""
    VALID = "valid"
    INVALID = "invalid"
    OVER_CONSTRAINED = "over_constrained"
    UNDER_CONSTRAINED = "under_constrained"
    ERROR = "error"


@dataclass
class Component:
    """A component in an assembly."""
    component_id: str
    name: str
    component_type: ComponentType
    position: PrecisionPoint
    orientation: PrecisionVector = field(default_factory=lambda: PrecisionVector(1, 0, 0))
    scale: Decimal = Decimal("1.0")
    visible: bool = True
    locked: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate component after initialization."""
        self._validate_component()
    
    def _validate_component(self) -> None:
        """Validate component parameters."""
        if not self.component_id:
            raise ValueError("Component ID cannot be empty")
        if not self.name:
            raise ValueError("Component name cannot be empty")
        if self.scale <= 0:
            raise ValueError("Component scale must be positive")
    
    def get_transform_matrix(self) -> List[List[Decimal]]:
        """Get transformation matrix for the component."""
        # Simplified 2D transformation matrix
        cos_angle = self.orientation.dx
        sin_angle = self.orientation.dy
        
        return [
            [self.scale * cos_angle, -self.scale * sin_angle, self.position.x],
            [self.scale * sin_angle, self.scale * cos_angle, self.position.y],
            [Decimal("0"), Decimal("0"), Decimal("1")]
        ]
    
    def transform_point(self, point: PrecisionPoint) -> PrecisionPoint:
        """Transform a point using the component's transformation."""
        matrix = self.get_transform_matrix()
        
        x = point.x * matrix[0][0] + point.y * matrix[0][1] + matrix[0][2]
        y = point.x * matrix[1][0] + point.y * matrix[1][1] + matrix[1][2]
        
        return PrecisionPoint(x, y, precision_level=point.precision_level)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary representation."""
        return {
            "component_id": self.component_id,
            "name": self.name,
            "component_type": self.component_type.value,
            "position": self.position.to_dict(),
            "orientation": self.orientation.to_dict(),
            "scale": float(self.scale),
            "visible": self.visible,
            "locked": self.locked,
            "metadata": self.metadata
        }


@dataclass
class AssemblyConstraint:
    """A constraint between assembly components."""
    constraint_id: str
    constraint_type: AssemblyConstraintType
    component1_id: str
    component2_id: str
    feature1: str = ""  # Feature on component1 (e.g., "face1", "edge1")
    feature2: str = ""  # Feature on component2
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: AssemblyStatus = AssemblyStatus.VALID
    
    def __post_init__(self):
        """Validate constraint after initialization."""
        self._validate_constraint()
    
    def _validate_constraint(self) -> None:
        """Validate constraint parameters."""
        if not self.constraint_id:
            raise ValueError("Constraint ID cannot be empty")
        if not self.component1_id or not self.component2_id:
            raise ValueError("Both component IDs must be specified")
        if self.component1_id == self.component2_id:
            raise ValueError("Cannot constrain component to itself")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert constraint to dictionary representation."""
        return {
            "constraint_id": self.constraint_id,
            "constraint_type": self.constraint_type.value,
            "component1_id": self.component1_id,
            "component2_id": self.component2_id,
            "feature1": self.feature1,
            "feature2": self.feature2,
            "parameters": self.parameters,
            "status": self.status.value
        }


class Assembly:
    """An assembly containing multiple components."""
    
    def __init__(self, assembly_id: str, name: str):
        """Initialize assembly."""
        self.assembly_id = assembly_id
        self.name = name
        self.components: Dict[str, Component] = {}
        self.constraints: Dict[str, AssemblyConstraint] = {}
        self.next_component_id = 1
        self.next_constraint_id = 1
        self.status = AssemblyStatus.VALID
        logger.info(f"Assembly '{name}' initialized")
    
    def add_component(self, component: Component) -> bool:
        """Add a component to the assembly."""
        if component.component_id in self.components:
            logger.warning(f"Component '{component.component_id}' already exists in assembly")
            return False
        
        self.components[component.component_id] = component
        logger.debug(f"Added component '{component.name}' to assembly '{self.name}'")
        return True
    
    def remove_component(self, component_id: str) -> bool:
        """Remove a component from the assembly."""
        if component_id in self.components:
            # Remove associated constraints
            constraints_to_remove = [
                constraint_id for constraint_id, constraint in self.constraints.items()
                if constraint.component1_id == component_id or constraint.component2_id == component_id
            ]
            
            for constraint_id in constraints_to_remove:
                del self.constraints[constraint_id]
            
            del self.components[component_id]
            logger.debug(f"Removed component '{component_id}' from assembly '{self.name}'")
            return True
        return False
    
    def get_component(self, component_id: str) -> Optional[Component]:
        """Get a component by ID."""
        return self.components.get(component_id)
    
    def add_constraint(self, constraint: AssemblyConstraint) -> bool:
        """Add a constraint to the assembly."""
        # Validate that both components exist
        if constraint.component1_id not in self.components:
            logger.error(f"Component '{constraint.component1_id}' not found in assembly")
            return False
        
        if constraint.component2_id not in self.components:
            logger.error(f"Component '{constraint.component2_id}' not found in assembly")
            return False
        
        self.constraints[constraint.constraint_id] = constraint
        logger.debug(f"Added constraint '{constraint.constraint_id}' to assembly '{self.name}'")
        return True
    
    def remove_constraint(self, constraint_id: str) -> bool:
        """Remove a constraint from the assembly."""
        if constraint_id in self.constraints:
            del self.constraints[constraint_id]
            logger.debug(f"Removed constraint '{constraint_id}' from assembly '{self.name}'")
            return True
        return False
    
    def get_constraint(self, constraint_id: str) -> Optional[AssemblyConstraint]:
        """Get a constraint by ID."""
        return self.constraints.get(constraint_id)
    
    def update_component_position(self, component_id: str, new_position: PrecisionPoint) -> bool:
        """Update component position."""
        component = self.components.get(component_id)
        if component and not component.locked:
            component.position = new_position
            self._validate_assembly()
            logger.debug(f"Updated component '{component_id}' position")
            return True
        return False
    
    def update_component_orientation(self, component_id: str, new_orientation: PrecisionVector) -> bool:
        """Update component orientation."""
        component = self.components.get(component_id)
        if component and not component.locked:
            component.orientation = new_orientation
            self._validate_assembly()
            logger.debug(f"Updated component '{component_id}' orientation")
            return True
        return False
    
    def update_component_scale(self, component_id: str, new_scale: Union[float, Decimal]) -> bool:
        """Update component scale."""
        component = self.components.get(component_id)
        if component and not component.locked:
            component.scale = Decimal(str(new_scale))
            self._validate_assembly()
            logger.debug(f"Updated component '{component_id}' scale")
            return True
        return False
    
    def _validate_assembly(self) -> None:
        """Validate assembly constraints and update status."""
        try:
            # Check for constraint violations
            violations = 0
            for constraint in self.constraints.values():
                if not self._validate_constraint(constraint):
                    violations += 1
            
            if violations == 0:
                self.status = AssemblyStatus.VALID
            else:
                self.status = AssemblyStatus.INVALID
                logger.warning(f"Assembly '{self.name}' has {violations} constraint violations")
                
        except Exception as e:
            self.status = AssemblyStatus.ERROR
            logger.error(f"Error validating assembly '{self.name}': {e}")
    
    def _validate_constraint(self, constraint: AssemblyConstraint) -> bool:
        """Validate a single constraint."""
        component1 = self.components.get(constraint.component1_id)
        component2 = self.components.get(constraint.component2_id)
        
        if not component1 or not component2:
            return False
        
        # Simplified constraint validation
        # In a full CAD system, this would perform detailed geometric validation
        
        if constraint.constraint_type == AssemblyConstraintType.COINCIDENT:
            # Check if components are at the same position
            distance = component1.position.distance_to(component2.position)
            return distance <= Decimal("0.001")  # 1 micron tolerance
        
        elif constraint.constraint_type == AssemblyConstraintType.PARALLEL:
            # Check if component orientations are parallel
            dot_product = (component1.orientation.dx * component2.orientation.dx +
                          component1.orientation.dy * component2.orientation.dy)
            return abs(dot_product) >= Decimal("0.999")  # Within 1 degree
        
        elif constraint.constraint_type == AssemblyConstraintType.PERPENDICULAR:
            # Check if component orientations are perpendicular
            dot_product = (component1.orientation.dx * component2.orientation.dx +
                          component1.orientation.dy * component2.orientation.dy)
            return abs(dot_product) <= Decimal("0.001")  # Within 1 degree
        
        elif constraint.constraint_type == AssemblyConstraintType.DISTANCE:
            # Check distance constraint
            target_distance = constraint.parameters.get("distance", Decimal("0"))
            actual_distance = component1.position.distance_to(component2.position)
            tolerance = constraint.parameters.get("tolerance", Decimal("0.001"))
            return abs(actual_distance - target_distance) <= tolerance
        
        return True
    
    def get_assembly_statistics(self) -> Dict[str, Any]:
        """Get assembly statistics."""
        component_types = {}
        constraint_types = {}
        
        for component in self.components.values():
            comp_type = component.component_type.value
            component_types[comp_type] = component_types.get(comp_type, 0) + 1
        
        for constraint in self.constraints.values():
            const_type = constraint.constraint_type.value
            constraint_types[const_type] = constraint_types.get(const_type, 0) + 1
        
        return {
            "assembly_id": self.assembly_id,
            "name": self.name,
            "total_components": len(self.components),
            "total_constraints": len(self.constraints),
            "component_types": component_types,
            "constraint_types": constraint_types,
            "status": self.status.value
        }
    
    def export_data(self) -> Dict[str, Any]:
        """Export assembly data."""
        return {
            "assembly_id": self.assembly_id,
            "name": self.name,
            "components": {
                comp_id: component.to_dict()
                for comp_id, component in self.components.items()
            },
            "constraints": {
                const_id: constraint.to_dict()
                for const_id, constraint in self.constraints.items()
            },
            "status": self.status.value
        }


class AssemblyManager:
    """Main assembly management system for CAD operations."""
    
    def __init__(self):
        """Initialize assembly manager."""
        self.assemblies: Dict[str, Assembly] = {}
        self.next_assembly_id = 1
        logger.info("Assembly manager initialized")
    
    def create_assembly(self, name: str) -> str:
        """Create a new assembly."""
        assembly_id = f"assembly_{self.next_assembly_id}"
        assembly = Assembly(assembly_id, name)
        self.assemblies[assembly_id] = assembly
        self.next_assembly_id += 1
        
        logger.info(f"Created assembly: {name} (ID: {assembly_id})")
        return assembly_id
    
    def get_assembly(self, assembly_id: str) -> Optional[Assembly]:
        """Get an assembly by ID."""
        return self.assemblies.get(assembly_id)
    
    def remove_assembly(self, assembly_id: str) -> bool:
        """Remove an assembly."""
        if assembly_id in self.assemblies:
            del self.assemblies[assembly_id]
            logger.info(f"Removed assembly: {assembly_id}")
            return True
        return False
    
    def add_component_to_assembly(self, assembly_id: str, component: Component) -> bool:
        """Add a component to an assembly."""
        assembly = self.assemblies.get(assembly_id)
        if assembly:
            return assembly.add_component(component)
        return False
    
    def add_constraint_to_assembly(self, assembly_id: str, constraint: AssemblyConstraint) -> bool:
        """Add a constraint to an assembly."""
        assembly = self.assemblies.get(assembly_id)
        if assembly:
            return assembly.add_constraint(constraint)
        return False
    
    def validate_assembly(self, assembly_id: str) -> bool:
        """Validate an assembly."""
        assembly = self.assemblies.get(assembly_id)
        if assembly:
            assembly._validate_assembly()
            return assembly.status == AssemblyStatus.VALID
        return False
    
    def get_assembly_bounding_box(self, assembly_id: str) -> Optional[Tuple[PrecisionPoint, PrecisionPoint]]:
        """Get the bounding box of an assembly."""
        assembly = self.assemblies.get(assembly_id)
        if not assembly or not assembly.components:
            return None
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for component in assembly.components.values():
            # Simplified bounding box calculation
            # In practice, this would consider the component's geometry
            x, y = float(component.position.x), float(component.position.y)
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
        
        if min_x == float('inf'):
            return None
        
        min_point = PrecisionPoint(Decimal(str(min_x)), Decimal(str(min_y)))
        max_point = PrecisionPoint(Decimal(str(max_x)), Decimal(str(max_y)))
        
        return min_point, max_point
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get assembly manager statistics."""
        total_components = sum(len(assembly.components) for assembly in self.assemblies.values())
        total_constraints = sum(len(assembly.constraints) for assembly in self.assemblies.values())
        
        assembly_statuses = {}
        for assembly in self.assemblies.values():
            status = assembly.status.value
            assembly_statuses[status] = assembly_statuses.get(status, 0) + 1
        
        return {
            "total_assemblies": len(self.assemblies),
            "total_components": total_components,
            "total_constraints": total_constraints,
            "assembly_statuses": assembly_statuses,
            "assemblies": {
                assembly_id: assembly.get_assembly_statistics()
                for assembly_id, assembly in self.assemblies.items()
            }
        }
    
    def export_data(self) -> Dict[str, Any]:
        """Export assembly manager data."""
        return {
            "assemblies": {
                assembly_id: assembly.export_data()
                for assembly_id, assembly in self.assemblies.items()
            },
            "next_assembly_id": self.next_assembly_id
        }


# Factory functions for easy instantiation
def create_component(component_id: str, name: str, component_type: ComponentType,
                    position: PrecisionPoint, orientation: Optional[PrecisionVector] = None,
                    scale: Union[float, Decimal] = 1.0) -> Component:
    """Create a component."""
    if orientation is None:
        orientation = PrecisionVector(1, 0, 0)
    
    return Component(
        component_id=component_id,
        name=name,
        component_type=component_type,
        position=position,
        orientation=orientation,
        scale=Decimal(str(scale))
    )


def create_assembly_constraint(constraint_id: str, constraint_type: AssemblyConstraintType,
                             component1_id: str, component2_id: str,
                             feature1: str = "", feature2: str = "",
                             parameters: Optional[Dict[str, Any]] = None) -> AssemblyConstraint:
    """Create an assembly constraint."""
    if parameters is None:
        parameters = {}
    
    return AssemblyConstraint(
        constraint_id=constraint_id,
        constraint_type=constraint_type,
        component1_id=component1_id,
        component2_id=component2_id,
        feature1=feature1,
        feature2=feature2,
        parameters=parameters
    )


def create_assembly(assembly_id: str, name: str) -> Assembly:
    """Create a new assembly."""
    return Assembly(assembly_id, name)


def create_assembly_manager() -> AssemblyManager:
    """Create a new assembly manager."""
    return AssemblyManager() 