"""
System Constraints for Interdependency and Capacity Validation.

Implements constraints for building system relationships, capacity limits,
installation sequences, and compatibility requirements.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from collections import defaultdict

# Import Phase 1 foundation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.spatial import ArxObject, ArxObjectType, BoundingBox3D
from .constraint_core import (
    Constraint, ParametricConstraint, ConstraintType, ConstraintSeverity, 
    ConstraintScope, ConstraintResult, ConstraintViolation
)
from .constraint_engine import ConstraintEvaluationContext

logger = logging.getLogger(__name__)


class SystemConstraint(ParametricConstraint):
    """
    Base class for building system constraints.
    
    Provides common functionality for system-level validation including
    capacity calculations, interdependency tracking, and system health.
    """
    
    def __init__(self,
                 name: str = "System Constraint",
                 target_systems: Optional[Set[ArxObjectType]] = None,
                 **kwargs):
        """Initialize system constraint."""
        super().__init__(
            name=name,
            scope=ConstraintScope.SYSTEM,
            **kwargs
        )
        
        self.set_parameter('target_systems', target_systems or set())
        self.set_parameter('system_health_threshold', 0.8)  # 80% efficiency threshold
        
    def get_affected_systems(self) -> List[ArxObjectType]:
        """Get systems affected by this constraint."""
        return list(self.get_parameter('target_systems', set()))
    
    def get_system_objects(self, 
                          context: ConstraintEvaluationContext,
                          system_type: ArxObjectType) -> List[ArxObject]:
        """Get all objects of specified system type."""
        return [obj for obj in context.spatial_engine.objects.values()
                if obj.type == system_type]
    
    def calculate_system_load(self, 
                             system_objects: List[ArxObject],
                             load_property: str = "capacity") -> float:
        """Calculate total system load or capacity."""
        total_load = 0.0
        
        for obj in system_objects:
            if hasattr(obj, 'metadata') and obj.metadata:
                # Extract load value from metadata
                custom_attrs = getattr(obj.metadata, 'custom_attributes', {})
                if load_property in custom_attrs:
                    try:
                        value_str = custom_attrs[load_property]
                        # Extract numeric value (handle units)
                        import re
                        numbers = re.findall(r'[\d.]+', str(value_str))
                        if numbers:
                            total_load += float(numbers[0])
                    except (ValueError, AttributeError):
                        continue
        
        return total_load


class InterdependencyConstraint(SystemConstraint):
    """
    System interdependency constraint validator.
    
    Ensures proper relationships and dependencies between building systems
    such as electrical panels serving outlets, HVAC connections, etc.
    """
    
    def __init__(self,
                 name: str = "System Interdependency Constraint",
                 dependency_type: str = "electrical_circuit",
                 **kwargs):
        """Initialize interdependency constraint."""
        super().__init__(
            name=name,
            constraint_type=ConstraintType.SYSTEM_INTERDEPENDENCY,
            **kwargs
        )
        
        self.set_parameter('dependency_type', dependency_type)
        
        # Define system relationships
        if dependency_type == "electrical_circuit":
            self.set_parameter('provider_type', ArxObjectType.ELECTRICAL_PANEL)
            self.set_parameter('consumer_types', {
                ArxObjectType.ELECTRICAL_OUTLET,
                ArxObjectType.ELECTRICAL_FIXTURE
            })
            self.set_parameter('max_circuit_length', 100.0)  # feet
        
        elif dependency_type == "hvac_supply":
            self.set_parameter('provider_type', ArxObjectType.HVAC_UNIT)
            self.set_parameter('consumer_types', {
                ArxObjectType.HVAC_DUCT,
                ArxObjectType.HVAC_DIFFUSER
            })
            self.set_parameter('max_supply_distance', 200.0)  # feet
    
    def is_applicable(self, arxobject: ArxObject) -> bool:
        """Check if object is part of interdependency check."""
        consumer_types = self.get_parameter('consumer_types', set())
        provider_type = self.get_parameter('provider_type')
        
        return (arxobject.type in consumer_types or
                arxobject.type == provider_type)
    
    def evaluate(self, 
                context: ConstraintEvaluationContext,
                target_objects: List[ArxObject]) -> ConstraintResult:
        """Evaluate system interdependencies."""
        start_time = time.time()
        
        result = ConstraintResult(
            constraint_id=self.constraint_id,
            constraint_name=self.name,
            is_satisfied=True,
            evaluation_time_ms=0.0,
            evaluated_objects=[obj.id for obj in target_objects],
            evaluation_method="interdependency_check"
        )
        
        dependency_type = self.get_parameter('dependency_type')
        
        if dependency_type == "electrical_circuit":
            self._check_electrical_dependencies(context, target_objects, result)
        elif dependency_type == "hvac_supply":
            self._check_hvac_dependencies(context, target_objects, result)
        
        result.evaluation_time_ms = (time.time() - start_time) * 1000
        return result
    
    def _check_electrical_dependencies(self,
                                     context: ConstraintEvaluationContext,
                                     objects: List[ArxObject],
                                     result: ConstraintResult) -> None:
        """Check electrical system dependencies."""
        provider_type = self.get_parameter('provider_type')
        consumer_types = self.get_parameter('consumer_types')
        max_circuit_length = self.get_parameter('max_circuit_length')
        
        # Get all electrical panels and consumers
        panels = [obj for obj in objects if obj.type == provider_type]
        consumers = [obj for obj in objects if obj.type in consumer_types]
        
        # Check each consumer has accessible panel
        for consumer in consumers:
            connected_panel = None
            min_distance = float('inf')
            
            # Find closest panel
            for panel in panels:
                from .spatial_constraints import SpatialConstraintValidator
                distance = SpatialConstraintValidator.calculate_3d_distance(consumer, panel)
                
                if distance < min_distance:
                    min_distance = distance
                    connected_panel = panel
            
            if connected_panel is None:
                violation = self.create_violation(
                    description=f"No electrical panel found to serve {consumer.type.value}",
                    primary_object=consumer,
                    severity=ConstraintSeverity.ERROR,
                    technical_details={
                        'consumer_type': consumer.type.value,
                        'consumer_location': f"({consumer.geometry.x:.1f}, {consumer.geometry.y:.1f}, {consumer.geometry.z:.1f})",
                        'available_panels': len(panels)
                    },
                    suggested_fixes=[
                        "Install electrical panel within service area",
                        "Extend electrical distribution to this area",
                        "Relocate electrical device closer to existing panel"
                    ]
                )
                
                result.add_violation(violation)
            
            elif min_distance > max_circuit_length:
                violation = self.create_violation(
                    description=f"Electrical circuit too long: {min_distance:.1f}ft "
                               f"(maximum recommended: {max_circuit_length:.1f}ft)",
                    primary_object=consumer,
                    secondary_objects=[connected_panel],
                    severity=ConstraintSeverity.WARNING,
                    technical_details={
                        'circuit_length': min_distance,
                        'max_circuit_length': max_circuit_length,
                        'excess_length': min_distance - max_circuit_length,
                        'voltage_drop_risk': True
                    },
                    suggested_fixes=[
                        "Install additional electrical panel closer to load",
                        "Use larger conductor size to compensate for distance",
                        "Consider relocating electrical device"
                    ]
                )
                
                result.add_violation(violation)
    
    def _check_hvac_dependencies(self,
                               context: ConstraintEvaluationContext,
                               objects: List[ArxObject],
                               result: ConstraintResult) -> None:
        """Check HVAC system dependencies."""
        provider_type = self.get_parameter('provider_type')
        consumer_types = self.get_parameter('consumer_types')
        max_supply_distance = self.get_parameter('max_supply_distance')
        
        # Get HVAC units and distribution components
        hvac_units = [obj for obj in objects if obj.type == provider_type]
        consumers = [obj for obj in objects if obj.type in consumer_types]
        
        for consumer in consumers:
            nearest_unit = None
            min_distance = float('inf')
            
            # Find nearest HVAC unit
            for unit in hvac_units:
                from .spatial_constraints import SpatialConstraintValidator
                distance = SpatialConstraintValidator.calculate_3d_distance(consumer, unit)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_unit = unit
            
            if nearest_unit is None:
                violation = self.create_violation(
                    description=f"No HVAC unit found to serve {consumer.type.value}",
                    primary_object=consumer,
                    severity=ConstraintSeverity.ERROR,
                    technical_details={
                        'consumer_type': consumer.type.value,
                        'available_units': len(hvac_units)
                    },
                    suggested_fixes=[
                        "Install HVAC unit to serve this area",
                        "Extend HVAC distribution system",
                        "Review HVAC zoning and coverage"
                    ]
                )
                
                result.add_violation(violation)
            
            elif min_distance > max_supply_distance:
                violation = self.create_violation(
                    description=f"HVAC supply distance excessive: {min_distance:.1f}ft "
                               f"(maximum recommended: {max_supply_distance:.1f}ft)",
                    primary_object=consumer,
                    secondary_objects=[nearest_unit],
                    severity=ConstraintSeverity.WARNING,
                    technical_details={
                        'supply_distance': min_distance,
                        'max_supply_distance': max_supply_distance,
                        'efficiency_impact': True
                    },
                    suggested_fixes=[
                        "Install additional HVAC unit for better distribution",
                        "Optimize duct routing for shorter supply runs",
                        "Consider zoned HVAC system design"
                    ]
                )
                
                result.add_violation(violation)


class CapacityConstraint(SystemConstraint):
    """
    System capacity constraint validator.
    
    Ensures building systems have adequate capacity to serve connected
    loads including electrical, HVAC, plumbing, and structural systems.
    """
    
    def __init__(self,
                 name: str = "System Capacity Constraint",
                 capacity_type: str = "electrical_load",
                 **kwargs):
        """Initialize capacity constraint."""
        super().__init__(
            name=name,
            constraint_type=ConstraintType.SYSTEM_CAPACITY,
            **kwargs
        )
        
        self.set_parameter('capacity_type', capacity_type)
        self.set_parameter('safety_factor', 1.25)  # 25% safety margin
        
        # Define capacity parameters by type
        if capacity_type == "electrical_load":
            self.set_parameter('provider_type', ArxObjectType.ELECTRICAL_PANEL)
            self.set_parameter('consumer_types', {
                ArxObjectType.ELECTRICAL_OUTLET,
                ArxObjectType.ELECTRICAL_FIXTURE
            })
            self.set_parameter('default_panel_capacity', 200.0)  # Amps
            self.set_parameter('default_outlet_load', 15.0)     # Amps
        
        elif capacity_type == "hvac_cooling":
            self.set_parameter('provider_type', ArxObjectType.HVAC_UNIT)
            self.set_parameter('consumer_types', {ArxObjectType.HVAC_DIFFUSER})
            self.set_parameter('default_unit_capacity', 60000.0)   # BTU/hr
            self.set_parameter('default_diffuser_load', 2000.0)    # BTU/hr
    
    def is_applicable(self, arxobject: ArxObject) -> bool:
        """Check if object is part of capacity analysis."""
        provider_type = self.get_parameter('provider_type')
        consumer_types = self.get_parameter('consumer_types', set())
        
        return (arxobject.type == provider_type or
                arxobject.type in consumer_types)
    
    def evaluate(self, 
                context: ConstraintEvaluationContext,
                target_objects: List[ArxObject]) -> ConstraintResult:
        """Evaluate system capacity requirements."""
        start_time = time.time()
        
        result = ConstraintResult(
            constraint_id=self.constraint_id,
            constraint_name=self.name,
            is_satisfied=True,
            evaluation_time_ms=0.0,
            evaluated_objects=[obj.id for obj in target_objects],
            evaluation_method="capacity_analysis"
        )
        
        capacity_type = self.get_parameter('capacity_type')
        
        if capacity_type == "electrical_load":
            self._check_electrical_capacity(context, target_objects, result)
        elif capacity_type == "hvac_cooling":
            self._check_hvac_capacity(context, target_objects, result)
        
        result.evaluation_time_ms = (time.time() - start_time) * 1000
        return result
    
    def _check_electrical_capacity(self,
                                 context: ConstraintEvaluationContext,
                                 objects: List[ArxObject],
                                 result: ConstraintResult) -> None:
        """Check electrical system capacity."""
        provider_type = self.get_parameter('provider_type')
        consumer_types = self.get_parameter('consumer_types')
        safety_factor = self.get_parameter('safety_factor')
        default_panel_capacity = self.get_parameter('default_panel_capacity')
        default_outlet_load = self.get_parameter('default_outlet_load')
        
        # Get electrical panels and loads
        panels = [obj for obj in objects if obj.type == provider_type]
        consumers = [obj for obj in objects if obj.type in consumer_types]
        
        for panel in panels:
            # Calculate panel capacity
            panel_capacity = default_panel_capacity  # Would get from metadata in practice
            
            # Find consumers served by this panel (simplified - by proximity)
            served_consumers = []
            for consumer in consumers:
                from .spatial_constraints import SpatialConstraintValidator
                distance = SpatialConstraintValidator.calculate_3d_distance(panel, consumer)
                
                # Assume panel serves loads within 100ft (simplified)
                if distance <= 100.0:
                    served_consumers.append(consumer)
            
            # Calculate total load
            total_load = len(served_consumers) * default_outlet_load
            required_capacity = total_load * safety_factor
            
            if required_capacity > panel_capacity:
                capacity_deficit = required_capacity - panel_capacity
                
                violation = self.create_violation(
                    description=f"Electrical panel capacity exceeded: {required_capacity:.0f}A required "
                               f"({panel_capacity:.0f}A available)",
                    primary_object=panel,
                    secondary_objects=served_consumers[:5],  # Limit to first 5
                    severity=ConstraintSeverity.ERROR,
                    technical_details={
                        'panel_capacity_amps': panel_capacity,
                        'total_load_amps': total_load,
                        'required_capacity_amps': required_capacity,
                        'capacity_deficit_amps': capacity_deficit,
                        'loads_served': len(served_consumers),
                        'safety_factor': safety_factor
                    },
                    suggested_fixes=[
                        "Install additional electrical panel to distribute load",
                        "Upgrade panel to higher capacity rating",
                        "Redistribute electrical loads to other panels",
                        "Review electrical load calculations and requirements"
                    ]
                )
                
                result.add_violation(violation)
    
    def _check_hvac_capacity(self,
                           context: ConstraintEvaluationContext,
                           objects: List[ArxObject],
                           result: ConstraintResult) -> None:
        """Check HVAC system capacity."""
        provider_type = self.get_parameter('provider_type')
        consumer_types = self.get_parameter('consumer_types')
        safety_factor = self.get_parameter('safety_factor')
        default_unit_capacity = self.get_parameter('default_unit_capacity')
        default_diffuser_load = self.get_parameter('default_diffuser_load')
        
        # Get HVAC units and diffusers
        hvac_units = [obj for obj in objects if obj.type == provider_type]
        diffusers = [obj for obj in objects if obj.type in consumer_types]
        
        for unit in hvac_units:
            # Calculate unit capacity
            unit_capacity = default_unit_capacity  # Would get from metadata
            
            # Find diffusers served by this unit (by proximity)
            served_diffusers = []
            for diffuser in diffusers:
                from .spatial_constraints import SpatialConstraintValidator
                distance = SpatialConstraintValidator.calculate_3d_distance(unit, diffuser)
                
                # Assume unit serves diffusers within 150ft
                if distance <= 150.0:
                    served_diffusers.append(diffuser)
            
            # Calculate cooling load
            total_load = len(served_diffusers) * default_diffuser_load
            required_capacity = total_load * safety_factor
            
            if required_capacity > unit_capacity:
                capacity_deficit = required_capacity - unit_capacity
                
                violation = self.create_violation(
                    description=f"HVAC unit capacity exceeded: {required_capacity:.0f} BTU/hr required "
                               f"({unit_capacity:.0f} BTU/hr available)",
                    primary_object=unit,
                    secondary_objects=served_diffusers[:3],
                    severity=ConstraintSeverity.ERROR,
                    technical_details={
                        'unit_capacity_btu': unit_capacity,
                        'total_load_btu': total_load,
                        'required_capacity_btu': required_capacity,
                        'capacity_deficit_btu': capacity_deficit,
                        'diffusers_served': len(served_diffusers)
                    },
                    suggested_fixes=[
                        "Install additional HVAC unit for this zone",
                        "Upgrade HVAC unit to higher capacity",
                        "Redistribute HVAC load across multiple units",
                        "Review cooling load calculations"
                    ]
                )
                
                result.add_violation(violation)


class SequenceConstraint(SystemConstraint):
    """
    Installation sequence constraint validator.
    
    Ensures proper installation order for building systems where
    sequence dependencies exist (structural before MEP, etc.).
    """
    
    def __init__(self,
                 name: str = "Installation Sequence Constraint",
                 sequence_rule: str = "structural_first",
                 **kwargs):
        """Initialize sequence constraint."""
        super().__init__(
            name=name,
            constraint_type=ConstraintType.SYSTEM_SEQUENCE,
            **kwargs
        )
        
        self.set_parameter('sequence_rule', sequence_rule)
        
        # Define installation sequences
        if sequence_rule == "structural_first":
            self.set_parameter('prerequisite_systems', {
                ArxObjectType.STRUCTURAL_BEAM,
                ArxObjectType.STRUCTURAL_COLUMN,
                ArxObjectType.STRUCTURAL_WALL,
                ArxObjectType.STRUCTURAL_SLAB
            })
            self.set_parameter('dependent_systems', {
                ArxObjectType.ELECTRICAL_OUTLET,
                ArxObjectType.HVAC_DUCT,
                ArxObjectType.PLUMBING_PIPE
            })
    
    def is_applicable(self, arxobject: ArxObject) -> bool:
        """Check if object is part of sequence validation."""
        prerequisite_systems = self.get_parameter('prerequisite_systems', set())
        dependent_systems = self.get_parameter('dependent_systems', set())
        
        return (arxobject.type in prerequisite_systems or
                arxobject.type in dependent_systems)
    
    def evaluate(self, 
                context: ConstraintEvaluationContext,
                target_objects: List[ArxObject]) -> ConstraintResult:
        """Evaluate installation sequence requirements."""
        start_time = time.time()
        
        result = ConstraintResult(
            constraint_id=self.constraint_id,
            constraint_name=self.name,
            is_satisfied=True,
            evaluation_time_ms=0.0,
            evaluated_objects=[obj.id for obj in target_objects],
            evaluation_method="sequence_validation"
        )
        
        prerequisite_systems = self.get_parameter('prerequisite_systems', set())
        dependent_systems = self.get_parameter('dependent_systems', set())
        
        # Check if prerequisites exist for dependent systems
        prerequisite_objects = [obj for obj in target_objects 
                              if obj.type in prerequisite_systems]
        dependent_objects = [obj for obj in target_objects 
                           if obj.type in dependent_systems]
        
        if dependent_objects and not prerequisite_objects:
            violation = self.create_violation(
                description=f"Installation sequence violation: dependent systems present without prerequisites",
                severity=ConstraintSeverity.WARNING,
                technical_details={
                    'prerequisite_systems': [sys.value for sys in prerequisite_systems],
                    'dependent_systems': [sys.value for sys in dependent_systems],
                    'dependent_objects_count': len(dependent_objects),
                    'prerequisite_objects_count': len(prerequisite_objects)
                },
                suggested_fixes=[
                    "Install structural elements before MEP systems",
                    "Review construction sequence and phasing",
                    "Coordinate trades for proper installation order"
                ]
            )
            
            result.add_violation(violation)
        
        result.evaluation_time_ms = (time.time() - start_time) * 1000
        return result


class CompatibilityConstraint(SystemConstraint):
    """
    System compatibility constraint validator.
    
    Ensures compatible systems, materials, and configurations are
    used together to prevent performance or safety issues.
    """
    
    def __init__(self,
                 name: str = "System Compatibility Constraint",
                 compatibility_rule: str = "material_compatibility",
                 **kwargs):
        """Initialize compatibility constraint."""
        super().__init__(
            name=name,
            constraint_type=ConstraintType.SYSTEM_COMPATIBILITY,
            **kwargs
        )
        
        self.set_parameter('compatibility_rule', compatibility_rule)
        
        # Define compatibility rules
        if compatibility_rule == "material_compatibility":
            self.set_parameter('incompatible_pairs', {
                ('copper', 'galvanized_steel'),  # Galvanic corrosion
                ('aluminum', 'steel'),           # Dissimilar metals
                ('pvc', 'cpvc')                  # Different plastic types
            })
    
    def is_applicable(self, arxobject: ArxObject) -> bool:
        """Check if object is part of compatibility check."""
        # Apply to objects with material properties
        return (hasattr(arxobject, 'metadata') and 
                arxobject.metadata and
                hasattr(arxobject.metadata, 'material') and
                arxobject.metadata.material)
    
    def evaluate(self, 
                context: ConstraintEvaluationContext,
                target_objects: List[ArxObject]) -> ConstraintResult:
        """Evaluate system compatibility requirements."""
        start_time = time.time()
        
        result = ConstraintResult(
            constraint_id=self.constraint_id,
            constraint_name=self.name,
            is_satisfied=True,
            evaluation_time_ms=0.0,
            evaluated_objects=[obj.id for obj in target_objects],
            evaluation_method="compatibility_check"
        )
        
        incompatible_pairs = self.get_parameter('incompatible_pairs', set())
        
        # Check for incompatible material combinations
        for i, obj1 in enumerate(target_objects):
            if not self.is_applicable(obj1):
                continue
            
            material1 = obj1.metadata.material
            
            # Check nearby objects for material compatibility
            nearby_objects = context.get_related_objects(obj1, "spatial", 5.0)  # 5ft radius
            
            for obj2 in nearby_objects:
                if not self.is_applicable(obj2):
                    continue
                
                material2 = obj2.metadata.material
                
                # Check if materials are incompatible
                for mat_pair in incompatible_pairs:
                    if ((material1 in mat_pair and material2 in mat_pair) and
                        material1 != material2):
                        
                        violation = self.create_violation(
                            description=f"Incompatible materials in proximity: {material1} and {material2}",
                            primary_object=obj1,
                            secondary_objects=[obj2],
                            severity=ConstraintSeverity.WARNING,
                            technical_details={
                                'material_1': material1,
                                'material_2': material2,
                                'incompatible_pair': mat_pair,
                                'proximity_risk': True
                            },
                            suggested_fixes=[
                                f"Use compatible materials or provide isolation between {material1} and {material2}",
                                "Consider alternative material selection",
                                "Install dielectric unions or isolation fittings"
                            ]
                        )
                        
                        result.add_violation(violation)
        
        result.evaluation_time_ms = (time.time() - start_time) * 1000
        return result


logger.info("System constraint validators initialized")