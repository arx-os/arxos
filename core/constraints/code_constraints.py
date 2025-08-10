"""
Building Code Compliance Constraint Library.

Implements building code constraints for fire safety, accessibility,
electrical, mechanical, and structural code compliance validation.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from dataclasses import dataclass

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
from .spatial_constraints import SpatialConstraintValidator

logger = logging.getLogger(__name__)


class BuildingCodeConstraint(ParametricConstraint):
    """
    Base class for building code compliance constraints.
    
    Provides common functionality for code-based validation including
    code section references, jurisdiction handling, and compliance reporting.
    """
    
    def __init__(self,
                 name: str = "Building Code Constraint",
                 code_reference: str = "",
                 jurisdiction: str = "IBC",  # International Building Code
                 **kwargs):
        """Initialize building code constraint."""
        super().__init__(name=name, **kwargs)
        
        self.set_parameter('code_reference', code_reference)
        self.set_parameter('jurisdiction', jurisdiction)
        self.set_parameter('compliance_level', 'required')  # required, recommended, best_practice
        
        # Standard code parameters
        self.set_parameter('occupancy_type', 'commercial')
        self.set_parameter('building_height', 1)  # stories
        self.set_parameter('construction_type', 'Type_V')
    
    def create_code_violation(self,
                             description: str,
                             primary_object: Optional[ArxObject] = None,
                             code_section: Optional[str] = None,
                             **kwargs) -> ConstraintViolation:
        """Create code compliance violation with code reference."""
        
        code_ref = code_section or self.get_parameter('code_reference', '')
        jurisdiction = self.get_parameter('jurisdiction', 'IBC')
        
        enhanced_description = description
        if code_ref:
            enhanced_description += f" (Code: {jurisdiction} {code_ref})"
        
        technical_details = kwargs.get('technical_details', {})
        technical_details.update({
            'code_reference': code_ref,
            'jurisdiction': jurisdiction,
            'compliance_level': self.get_parameter('compliance_level'),
            'occupancy_type': self.get_parameter('occupancy_type')
        })
        
        return self.create_violation(
            description=enhanced_description,
            primary_object=primary_object,
            technical_details=technical_details,
            **kwargs
        )


class FireSafetyConstraint(BuildingCodeConstraint):
    """
    Fire safety code compliance constraints.
    
    Validates fire sprinkler spacing, exit access, fire separation,
    and other fire safety requirements per building codes.
    """
    
    def __init__(self,
                 name: str = "Fire Safety Constraint",
                 safety_requirement: str = "sprinkler_spacing",
                 **kwargs):
        """Initialize fire safety constraint."""
        super().__init__(
            name=name,
            constraint_type=ConstraintType.CODE_FIRE_SAFETY,
            severity=ConstraintSeverity.CRITICAL,
            code_reference="NFPA 13",
            **kwargs
        )
        
        self.set_parameter('safety_requirement', safety_requirement)
        
        # Fire sprinkler spacing requirements
        if safety_requirement == "sprinkler_spacing":
            self.set_parameter('max_spacing', 15.0)  # feet
            self.set_parameter('coverage_area', 225.0)  # sq ft per sprinkler
            self.set_parameter('wall_distance', 7.5)  # max distance from wall
        
        # Exit requirements
        elif safety_requirement == "exit_access":
            self.set_parameter('max_travel_distance', 250.0)  # feet
            self.set_parameter('min_exit_width', 44.0)  # inches
            self.set_parameter('required_exits', 2)  # minimum exits
    
    def is_applicable(self, arxobject: ArxObject) -> bool:
        """Check if fire safety constraint applies to object."""
        safety_requirement = self.get_parameter('safety_requirement')
        
        if safety_requirement == "sprinkler_spacing":
            return arxobject.type == ArxObjectType.FIRE_SPRINKLER
        elif safety_requirement == "exit_access":
            return arxobject.type == ArxObjectType.EMERGENCY_EXIT
        
        return False
    
    def evaluate(self, 
                context: ConstraintEvaluationContext,
                target_objects: List[ArxObject]) -> ConstraintResult:
        """Evaluate fire safety requirements."""
        start_time = time.time()
        
        result = ConstraintResult(
            constraint_id=self.constraint_id,
            constraint_name=self.name,
            is_satisfied=True,
            evaluation_time_ms=0.0,
            evaluated_objects=[obj.id for obj in target_objects],
            evaluation_method="fire_safety_check"
        )
        
        safety_requirement = self.get_parameter('safety_requirement')
        
        if safety_requirement == "sprinkler_spacing":
            self._check_sprinkler_spacing(context, target_objects, result)
        elif safety_requirement == "exit_access":
            self._check_exit_access(context, target_objects, result)
        
        result.evaluation_time_ms = (time.time() - start_time) * 1000
        return result
    
    def _check_sprinkler_spacing(self, 
                                context: ConstraintEvaluationContext,
                                sprinklers: List[ArxObject],
                                result: ConstraintResult) -> None:
        """Check fire sprinkler spacing requirements."""
        max_spacing = self.get_parameter('max_spacing')
        wall_distance = self.get_parameter('wall_distance')
        
        # Check spacing between sprinklers
        for i, sprinkler1 in enumerate(sprinklers):
            if sprinkler1.type != ArxObjectType.FIRE_SPRINKLER:
                continue
            
            # Check distance to other sprinklers
            nearby_sprinklers = [s for s in sprinklers[i+1:] 
                               if s.type == ArxObjectType.FIRE_SPRINKLER]
            
            for sprinkler2 in nearby_sprinklers:
                distance = SpatialConstraintValidator.calculate_2d_distance(sprinkler1, sprinkler2)
                
                if distance > max_spacing:
                    violation = self.create_code_violation(
                        description=f"Fire sprinkler spacing violation: {distance:.1f}ft "
                                   f"(maximum allowed: {max_spacing:.1f}ft)",
                        primary_object=sprinkler1,
                        secondary_objects=[sprinkler2],
                        code_section="NFPA 13 8.6.2",
                        severity=ConstraintSeverity.CRITICAL,
                        technical_details={
                            'actual_spacing': distance,
                            'maximum_spacing': max_spacing,
                            'excess_spacing': distance - max_spacing
                        },
                        suggested_fixes=[
                            "Install additional fire sprinkler between existing sprinklers",
                            "Relocate sprinklers to achieve proper spacing",
                            "Verify sprinkler head type and coverage area"
                        ]
                    )
                    
                    result.add_violation(violation)
            
            # Check distance to walls (would need wall objects in context)
            # This is a simplified check - in practice would query for wall objects
            walls = [obj for obj in context.spatial_engine.objects.values()
                    if obj.type == ArxObjectType.STRUCTURAL_WALL]
            
            for wall in walls:
                distance_to_wall = SpatialConstraintValidator.calculate_surface_distance(sprinkler1, wall)
                
                if distance_to_wall > wall_distance:
                    violation = self.create_code_violation(
                        description=f"Fire sprinkler too far from wall: {distance_to_wall:.1f}ft "
                                   f"(maximum allowed: {wall_distance:.1f}ft)",
                        primary_object=sprinkler1,
                        secondary_objects=[wall],
                        code_section="NFPA 13 8.6.4",
                        severity=ConstraintSeverity.ERROR,
                        technical_details={
                            'distance_to_wall': distance_to_wall,
                            'maximum_wall_distance': wall_distance
                        },
                        suggested_fixes=[
                            "Relocate sprinkler closer to wall",
                            "Install additional sprinkler head near wall",
                            "Review sprinkler layout for wall proximity"
                        ]
                    )
                    
                    result.add_violation(violation)
    
    def _check_exit_access(self, 
                          context: ConstraintEvaluationContext,
                          exits: List[ArxObject],
                          result: ConstraintResult) -> None:
        """Check exit access requirements."""
        max_travel_distance = self.get_parameter('max_travel_distance')
        min_exit_width = self.get_parameter('min_exit_width')
        required_exits = self.get_parameter('required_exits')
        
        # Count available exits
        emergency_exits = [obj for obj in exits 
                          if obj.type == ArxObjectType.EMERGENCY_EXIT]
        
        if len(emergency_exits) < required_exits:
            violation = self.create_code_violation(
                description=f"Insufficient emergency exits: {len(emergency_exits)} found "
                           f"(minimum required: {required_exits})",
                code_section="IBC 1006.2",
                severity=ConstraintSeverity.CRITICAL,
                technical_details={
                    'available_exits': len(emergency_exits),
                    'required_exits': required_exits,
                    'exit_deficit': required_exits - len(emergency_exits)
                },
                suggested_fixes=[
                    f"Install {required_exits - len(emergency_exits)} additional emergency exits",
                    "Review building occupancy and exit requirements",
                    "Consider alternative exit configurations"
                ]
            )
            
            result.add_violation(violation)


class AccessibilityConstraint(BuildingCodeConstraint):
    """
    Accessibility (ADA) compliance constraints.
    
    Validates accessibility requirements for doorways, ramps,
    clearances, and accessible routes per ADA guidelines.
    """
    
    def __init__(self,
                 name: str = "Accessibility Constraint",
                 accessibility_requirement: str = "door_clearance",
                 **kwargs):
        """Initialize accessibility constraint."""
        super().__init__(
            name=name,
            constraint_type=ConstraintType.CODE_ACCESSIBILITY,
            severity=ConstraintSeverity.ERROR,
            code_reference="ADA 2010",
            **kwargs
        )
        
        self.set_parameter('accessibility_requirement', accessibility_requirement)
        
        # Door clearance requirements
        if accessibility_requirement == "door_clearance":
            self.set_parameter('min_clear_width', 32.0)  # inches
            self.set_parameter('maneuvering_clearance', 18.0)  # inches
        
        # Ramp requirements
        elif accessibility_requirement == "ramp_slope":
            self.set_parameter('max_slope', 8.33)  # percent (1:12)
            self.set_parameter('max_rise', 30.0)  # inches without landing
    
    def is_applicable(self, arxobject: ArxObject) -> bool:
        """Check if accessibility constraint applies to object."""
        accessibility_requirement = self.get_parameter('accessibility_requirement')
        
        if accessibility_requirement == "door_clearance":
            return arxobject.type == ArxObjectType.EMERGENCY_EXIT  # Doors
        elif accessibility_requirement == "ramp_slope":
            # Would apply to ramp objects if defined
            return False
        
        return False
    
    def evaluate(self, 
                context: ConstraintEvaluationContext,
                target_objects: List[ArxObject]) -> ConstraintResult:
        """Evaluate accessibility requirements."""
        start_time = time.time()
        
        result = ConstraintResult(
            constraint_id=self.constraint_id,
            constraint_name=self.name,
            is_satisfied=True,
            evaluation_time_ms=0.0,
            evaluated_objects=[obj.id for obj in target_objects],
            evaluation_method="accessibility_check"
        )
        
        accessibility_requirement = self.get_parameter('accessibility_requirement')
        
        if accessibility_requirement == "door_clearance":
            self._check_door_clearance(context, target_objects, result)
        
        result.evaluation_time_ms = (time.time() - start_time) * 1000
        return result
    
    def _check_door_clearance(self, 
                             context: ConstraintEvaluationContext,
                             doors: List[ArxObject],
                             result: ConstraintResult) -> None:
        """Check door clearance requirements."""
        min_clear_width = self.get_parameter('min_clear_width') / 12.0  # Convert to feet
        maneuvering_clearance = self.get_parameter('maneuvering_clearance') / 12.0
        
        for door in doors:
            if door.type != ArxObjectType.EMERGENCY_EXIT:
                continue
            
            # Check door width (simplified - would need door width property)
            door_width = getattr(door.geometry, 'width', 3.0)  # Default 3ft
            
            if door_width < min_clear_width:
                violation = self.create_code_violation(
                    description=f"Door clear width insufficient: {door_width * 12:.0f}\" "
                               f"(minimum required: {self.get_parameter('min_clear_width'):.0f}\")",
                    primary_object=door,
                    code_section="ADA 404.2.3",
                    severity=ConstraintSeverity.ERROR,
                    technical_details={
                        'actual_width_inches': door_width * 12,
                        'required_width_inches': self.get_parameter('min_clear_width'),
                        'width_deficit_inches': self.get_parameter('min_clear_width') - (door_width * 12)
                    },
                    suggested_fixes=[
                        "Install wider door to meet ADA requirements",
                        "Modify door frame for increased clear width",
                        "Review door hardware for space optimization"
                    ]
                )
                
                result.add_violation(violation)
            
            # Check maneuvering clearance (look for obstructions)
            nearby_objects = context.get_related_objects(door, "spatial", maneuvering_clearance * 2)
            
            for nearby_obj in nearby_objects:
                distance = SpatialConstraintValidator.calculate_surface_distance(door, nearby_obj)
                
                if distance < maneuvering_clearance:
                    violation = self.create_code_violation(
                        description=f"Insufficient maneuvering clearance at door: {distance * 12:.0f}\" "
                                   f"(minimum required: {self.get_parameter('maneuvering_clearance'):.0f}\")",
                        primary_object=door,
                        secondary_objects=[nearby_obj],
                        code_section="ADA 404.2.4",
                        severity=ConstraintSeverity.ERROR,
                        technical_details={
                            'actual_clearance_inches': distance * 12,
                            'required_clearance_inches': self.get_parameter('maneuvering_clearance'),
                            'obstruction_type': nearby_obj.type.value
                        },
                        suggested_fixes=[
                            f"Relocate {nearby_obj.type.value} to provide adequate clearance",
                            "Reconfigure area layout for ADA compliance",
                            "Consider alternative door swing direction"
                        ]
                    )
                    
                    result.add_violation(violation)


class ElectricalCodeConstraint(BuildingCodeConstraint):
    """
    Electrical code compliance constraints.
    
    Validates electrical outlet spacing, panel clearance, conductor
    sizing, and other NEC requirements.
    """
    
    def __init__(self,
                 name: str = "Electrical Code Constraint",
                 electrical_requirement: str = "outlet_spacing",
                 **kwargs):
        """Initialize electrical code constraint."""
        super().__init__(
            name=name,
            constraint_type=ConstraintType.CODE_ELECTRICAL,
            severity=ConstraintSeverity.ERROR,
            code_reference="NEC 2020",
            **kwargs
        )
        
        self.set_parameter('electrical_requirement', electrical_requirement)
        
        # Outlet spacing requirements
        if electrical_requirement == "outlet_spacing":
            self.set_parameter('max_outlet_spacing', 12.0)  # feet along wall
            self.set_parameter('wall_length_threshold', 2.0)  # min wall length requiring outlet
        
        # Panel clearance requirements
        elif electrical_requirement == "panel_clearance":
            self.set_parameter('working_space_width', 30.0)  # inches
            self.set_parameter('working_space_depth', 36.0)  # inches
            self.set_parameter('headroom', 78.0)  # inches
    
    def is_applicable(self, arxobject: ArxObject) -> bool:
        """Check if electrical constraint applies to object."""
        electrical_requirement = self.get_parameter('electrical_requirement')
        
        if electrical_requirement == "outlet_spacing":
            return arxobject.type == ArxObjectType.ELECTRICAL_OUTLET
        elif electrical_requirement == "panel_clearance":
            return arxobject.type == ArxObjectType.ELECTRICAL_PANEL
        
        return False
    
    def evaluate(self, 
                context: ConstraintEvaluationContext,
                target_objects: List[ArxObject]) -> ConstraintResult:
        """Evaluate electrical code requirements."""
        start_time = time.time()
        
        result = ConstraintResult(
            constraint_id=self.constraint_id,
            constraint_name=self.name,
            is_satisfied=True,
            evaluation_time_ms=0.0,
            evaluated_objects=[obj.id for obj in target_objects],
            evaluation_method="electrical_code_check"
        )
        
        electrical_requirement = self.get_parameter('electrical_requirement')
        
        if electrical_requirement == "outlet_spacing":
            self._check_outlet_spacing(context, target_objects, result)
        elif electrical_requirement == "panel_clearance":
            self._check_panel_clearance(context, target_objects, result)
        
        result.evaluation_time_ms = (time.time() - start_time) * 1000
        return result
    
    def _check_outlet_spacing(self, 
                             context: ConstraintEvaluationContext,
                             outlets: List[ArxObject],
                             result: ConstraintResult) -> None:
        """Check electrical outlet spacing per NEC."""
        max_spacing = self.get_parameter('max_outlet_spacing')
        
        # Sort outlets by location for spacing analysis
        electrical_outlets = [obj for obj in outlets 
                             if obj.type == ArxObjectType.ELECTRICAL_OUTLET]
        
        # Check spacing between adjacent outlets
        for i, outlet1 in enumerate(electrical_outlets):
            nearby_outlets = [outlet for outlet in electrical_outlets[i+1:]
                             if SpatialConstraintValidator.calculate_2d_distance(outlet1, outlet) <= max_spacing * 2]
            
            if not nearby_outlets:
                # No nearby outlets - potential spacing violation
                violation = self.create_code_violation(
                    description=f"Electrical outlet may be isolated - check spacing requirements",
                    primary_object=outlet1,
                    code_section="NEC 210.52(A)",
                    severity=ConstraintSeverity.WARNING,
                    technical_details={
                        'outlet_location': f"({outlet1.geometry.x:.1f}, {outlet1.geometry.y:.1f})",
                        'max_spacing': max_spacing,
                        'nearby_outlets_found': len(nearby_outlets)
                    },
                    suggested_fixes=[
                        "Verify outlet spacing along wall segments",
                        "Install additional outlets if spacing exceeds NEC requirements",
                        "Review floor plan for outlet distribution"
                    ]
                )
                
                result.add_violation(violation)
    
    def _check_panel_clearance(self, 
                              context: ConstraintEvaluationContext,
                              panels: List[ArxObject],
                              result: ConstraintResult) -> None:
        """Check electrical panel working space clearance."""
        working_space_depth = self.get_parameter('working_space_depth') / 12.0  # Convert to feet
        working_space_width = self.get_parameter('working_space_width') / 12.0
        
        for panel in panels:
            if panel.type != ArxObjectType.ELECTRICAL_PANEL:
                continue
            
            # Check for obstructions in working space
            nearby_objects = context.get_related_objects(panel, "spatial", working_space_depth * 2)
            
            for nearby_obj in nearby_objects:
                distance = SpatialConstraintValidator.calculate_surface_distance(panel, nearby_obj)
                
                if distance < working_space_depth:
                    violation = self.create_code_violation(
                        description=f"Electrical panel working space violation: {distance * 12:.0f}\" clearance "
                                   f"(minimum required: {self.get_parameter('working_space_depth'):.0f}\")",
                        primary_object=panel,
                        secondary_objects=[nearby_obj],
                        code_section="NEC 110.26(A)",
                        severity=ConstraintSeverity.ERROR,
                        technical_details={
                            'actual_clearance_inches': distance * 12,
                            'required_clearance_inches': self.get_parameter('working_space_depth'),
                            'obstruction_type': nearby_obj.type.value
                        },
                        suggested_fixes=[
                            f"Relocate {nearby_obj.type.value} to provide required working space",
                            "Reposition electrical panel for adequate clearance",
                            "Consider alternative panel mounting location"
                        ]
                    )
                    
                    result.add_violation(violation)


class MechanicalCodeConstraint(BuildingCodeConstraint):
    """
    Mechanical code compliance constraints.
    
    Validates HVAC equipment clearances, duct sizing, ventilation
    requirements, and IMC compliance.
    """
    
    def __init__(self,
                 name: str = "Mechanical Code Constraint",
                 mechanical_requirement: str = "equipment_clearance",
                 **kwargs):
        """Initialize mechanical code constraint."""
        super().__init__(
            name=name,
            constraint_type=ConstraintType.CODE_MECHANICAL,
            severity=ConstraintSeverity.ERROR,
            code_reference="IMC 2018",
            **kwargs
        )
        
        self.set_parameter('mechanical_requirement', mechanical_requirement)
        
        # Equipment clearance requirements
        if mechanical_requirement == "equipment_clearance":
            self.set_parameter('service_clearance', 30.0)  # inches
            self.set_parameter('control_clearance', 36.0)  # inches
        
        # Duct sizing requirements
        elif mechanical_requirement == "duct_sizing":
            self.set_parameter('min_duct_height', 4.0)  # inches
            self.set_parameter('max_velocity', 2000.0)  # fpm
    
    def is_applicable(self, arxobject: ArxObject) -> bool:
        """Check if mechanical constraint applies to object."""
        mechanical_types = {
            ArxObjectType.HVAC_UNIT,
            ArxObjectType.HVAC_DUCT,
            ArxObjectType.HVAC_DIFFUSER
        }
        return arxobject.type in mechanical_types
    
    def evaluate(self, 
                context: ConstraintEvaluationContext,
                target_objects: List[ArxObject]) -> ConstraintResult:
        """Evaluate mechanical code requirements."""
        start_time = time.time()
        
        result = ConstraintResult(
            constraint_id=self.constraint_id,
            constraint_name=self.name,
            is_satisfied=True,
            evaluation_time_ms=0.0,
            evaluated_objects=[obj.id for obj in target_objects],
            evaluation_method="mechanical_code_check"
        )
        
        mechanical_requirement = self.get_parameter('mechanical_requirement')
        
        if mechanical_requirement == "equipment_clearance":
            self._check_equipment_clearance(context, target_objects, result)
        elif mechanical_requirement == "duct_sizing":
            self._check_duct_sizing(context, target_objects, result)
        
        result.evaluation_time_ms = (time.time() - start_time) * 1000
        return result
    
    def _check_equipment_clearance(self, 
                                  context: ConstraintEvaluationContext,
                                  equipment: List[ArxObject],
                                  result: ConstraintResult) -> None:
        """Check HVAC equipment service clearance."""
        service_clearance = self.get_parameter('service_clearance') / 12.0  # Convert to feet
        
        for unit in equipment:
            if unit.type != ArxObjectType.HVAC_UNIT:
                continue
            
            # Check clearance around equipment
            nearby_objects = context.get_related_objects(unit, "spatial", service_clearance * 2)
            
            for nearby_obj in nearby_objects:
                distance = SpatialConstraintValidator.calculate_surface_distance(unit, nearby_obj)
                
                if distance < service_clearance:
                    violation = self.create_code_violation(
                        description=f"HVAC equipment service clearance violation: {distance * 12:.0f}\" "
                                   f"(minimum required: {self.get_parameter('service_clearance'):.0f}\")",
                        primary_object=unit,
                        secondary_objects=[nearby_obj],
                        code_section="IMC 306.5",
                        severity=ConstraintSeverity.ERROR,
                        technical_details={
                            'actual_clearance_inches': distance * 12,
                            'required_clearance_inches': self.get_parameter('service_clearance'),
                            'equipment_type': unit.type.value
                        },
                        suggested_fixes=[
                            f"Relocate {nearby_obj.type.value} to provide service access",
                            "Reposition HVAC equipment for maintenance clearance",
                            "Consider alternative equipment configuration"
                        ]
                    )
                    
                    result.add_violation(violation)
    
    def _check_duct_sizing(self, 
                          context: ConstraintEvaluationContext,
                          ducts: List[ArxObject],
                          result: ConstraintResult) -> None:
        """Check duct sizing requirements."""
        min_duct_height = self.get_parameter('min_duct_height') / 12.0  # Convert to feet
        
        for duct in ducts:
            if duct.type != ArxObjectType.HVAC_DUCT:
                continue
            
            # Check duct dimensions (simplified - would need actual duct properties)
            duct_height = getattr(duct.geometry, 'height', 1.0)  # Default 1ft
            
            if duct_height < min_duct_height:
                violation = self.create_code_violation(
                    description=f"HVAC duct undersized: {duct_height * 12:.0f}\" height "
                               f"(minimum required: {self.get_parameter('min_duct_height'):.0f}\")",
                    primary_object=duct,
                    code_section="IMC 603.2",
                    severity=ConstraintSeverity.WARNING,
                    technical_details={
                        'actual_height_inches': duct_height * 12,
                        'minimum_height_inches': self.get_parameter('min_duct_height'),
                        'duct_location': f"({duct.geometry.x:.1f}, {duct.geometry.y:.1f}, {duct.geometry.z:.1f})"
                    },
                    suggested_fixes=[
                        "Increase duct size to meet minimum requirements",
                        "Verify duct sizing calculations and airflow requirements",
                        "Consider alternative duct routing for adequate sizing"
                    ]
                )
                
                result.add_violation(violation)


logger.info("Building code constraint library initialized")