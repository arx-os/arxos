"""
SVGX Engine - Infrastructure as Code Service

Breaks down building models into digital elements (smallest measurable units)
using SVGX/XML for GUS processing and recursive building.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import uuid
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

# Import precision module directly to avoid circular imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))
from precision import precision_manager, PrecisionLevel, PrecisionDisplayMode

# Import CAD primitives and constraints
from svgx_engine.core.primitives import Line, Arc, Circle, Rectangle, Polyline
from svgx_engine.core.constraints import Constraint, ParallelConstraint, PerpendicularConstraint, EqualConstraint, FixedConstraint, ConstraintType

# Use print for logging to avoid circular import issues
def log_info(message):
    print(f"INFO: {message}")

def log_error(message):
    print(f"ERROR: {message}")

def log_warning(message):
    print(f"WARNING: {message}")

class ElementType(Enum):
    WALL = "wall"
    DOOR = "door"
    WINDOW = "window"
    FLOOR = "floor"
    CEILING = "ceiling"
    ROOF = "roof"
    COLUMN = "column"
    BEAM = "beam"
    STAIR = "stair"
    ELEVATOR = "elevator"
    HVAC = "hvac"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    FURNITURE = "furniture"
    EQUIPMENT = "equipment"
    LINE = "line"
    ARC = "arc"
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    POLYLINE = "polyline"

class MeasurementUnit(Enum):
    MILLIMETER = "mm"
    CENTIMETER = "cm"
    METER = "m"
    INCH = "inch"
    FOOT = "foot"

@dataclass
class DigitalElement:
    element_type: ElementType
    position_x: Decimal
    position_y: Decimal
    position_z: Decimal
    width: Decimal
    height: Decimal
    depth: Decimal
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    properties: Dict[str, Any] = field(default_factory=dict)
    connections: List[str] = field(default_factory=list)
    constraints: List[Constraint] = field(default_factory=list)
    cad_primitives: List[Union[Line, Arc, Circle, Rectangle, Polyline]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    measurement_unit: MeasurementUnit = MeasurementUnit.MILLIMETER
    precision_level: PrecisionLevel = PrecisionLevel.MICRON
    
    def __post_init__(self):
        # Ensure all numeric values are Decimal for precision
        self.position_x = Decimal(str(self.position_x))
        self.position_y = Decimal(str(self.position_y))
        self.position_z = Decimal(str(self.position_z))
        self.width = Decimal(str(self.width))
        self.height = Decimal(str(self.height))
        self.depth = Decimal(str(self.depth))
    
    def add_cad_primitive(self, primitive: Union[Line, Arc, Circle, Rectangle, Polyline]):
        """Add a CAD primitive to this element."""
        self.cad_primitives.append(primitive)
        self.updated_at = datetime.now()
        log_info(f"Added CAD primitive {type(primitive).__name__} to element {self.id}")
    
    def add_constraint(self, constraint: Constraint):
        """Add a constraint to this element."""
        self.constraints.append(constraint)
        self.updated_at = datetime.now()
        log_info(f"Added constraint {constraint.constraint_type.value} to element {self.id}")
    
    def get_volume(self) -> Decimal:
        """Calculate volume in cubic units."""
        return self.width * self.height * self.depth
    
    def get_surface_area(self) -> Decimal:
        """Calculate surface area in square units."""
        return 2 * (self.width * self.height + self.width * self.depth + self.height * self.depth)
    
    def to_svgx_element(self) -> ET.Element:
        """Convert to SVGX XML element."""
        el = ET.Element("digital_element")
        el.set("id", self.id)
        el.set("type", self.element_type.value)
        el.set("position_x", str(self.position_x))
        el.set("position_y", str(self.position_y))
        el.set("position_z", str(self.position_z))
        el.set("width", str(self.width))
        el.set("height", str(self.height))
        el.set("depth", str(self.depth))
        el.set("measurement_unit", self.measurement_unit.value)
        el.set("precision_level", self.precision_level.name)
        el.set("created_at", self.created_at.isoformat())
        el.set("updated_at", self.updated_at.isoformat())
        
        # Add properties
        if self.properties:
            props_el = ET.SubElement(el, "properties")
            for key, value in self.properties.items():
                prop_el = ET.SubElement(props_el, "property")
                prop_el.set("key", key)
                prop_el.set("value", str(value))
        
        # Add connections
        if self.connections:
            conn_el = ET.SubElement(el, "connections")
            for conn_id in self.connections:
                conn_item = ET.SubElement(conn_el, "connection")
                conn_item.set("id", conn_id)
        
        # Add CAD primitives
        if self.cad_primitives:
            primitives_el = ET.SubElement(el, "cad_primitives")
            for primitive in self.cad_primitives:
                primitives_el.append(primitive.to_svgx())
        
        # Add constraints
        if self.constraints:
            constraints_el = ET.SubElement(el, "constraints")
            for constraint in self.constraints:
                constraint_el = ET.SubElement(constraints_el, "constraint")
                constraint_el.set("type", constraint.constraint_type.value)
                constraint_el.set("enabled", str(constraint.enabled))
                if constraint.parameters:
                    params_el = ET.SubElement(constraint_el, "parameters")
                    for key, value in constraint.parameters.items():
                        param_el = ET.SubElement(params_el, "parameter")
                        param_el.set("key", key)
                        param_el.set("value", str(value))
        
        return el
    
    def to_gus_instruction(self) -> str:
        """Generate natural language instruction for GUS."""
        instruction = f"Create a {self.element_type.value} at position ({self.position_x}, {self.position_y}, {self.position_z}) "
        instruction += f"with dimensions {self.width} x {self.height} x {self.depth} {self.measurement_unit.value}."
        
        if self.properties:
            instruction += f" Properties: {', '.join([f'{k}={v}' for k, v in self.properties.items()])}."
        
        if self.cad_primitives:
            instruction += f" Contains {len(self.cad_primitives)} CAD primitives."
        
        if self.constraints:
            instruction += f" Has {len(self.constraints)} constraints applied."
        
        return instruction

class InfrastructureAsCodeService:
    def __init__(self):
        self.elements: Dict[str, DigitalElement] = {}
        self.precision_manager = precision_manager
    
    def create_element(self, element_type: ElementType, **kwargs) -> DigitalElement:
        """Create a new digital element with micron precision."""
        # Convert float values to Decimal for precision
        for key in ['position_x', 'position_y', 'position_z', 'width', 'height', 'depth']:
            if key in kwargs and isinstance(kwargs[key], (int, float)):
                kwargs[key] = Decimal(str(kwargs[key]))
        
        element = DigitalElement(element_type=element_type, **kwargs)
        self.elements[element.id] = element
        log_info(f"Created element {element.id} of type {element_type.value}")
        return element
    
    def create_cad_element(self, element_type: ElementType, primitives: List[Union[Line, Arc, Circle, Rectangle, Polyline]], **kwargs) -> DigitalElement:
        """Create a digital element with CAD primitives."""
        element = self.create_element(element_type, **kwargs)
        for primitive in primitives:
            element.add_cad_primitive(primitive)
        return element
    
    def add_constraint_to_element(self, element_id: str, constraint: Constraint) -> bool:
        """Add a constraint to an existing element."""
        if element_id in self.elements:
            self.elements[element_id].add_constraint(constraint)
            return True
        log_error(f"Element {element_id} not found")
        return False
    
    def get_element(self, element_id: str) -> Optional[DigitalElement]:
        """Get an element by ID."""
        return self.elements.get(element_id)
    
    def update_element(self, element_id: str, **kwargs) -> bool:
        """Update an element's properties."""
        if element_id in self.elements:
            element = self.elements[element_id]
            for key, value in kwargs.items():
                if hasattr(element, key):
                    if key in ['position_x', 'position_y', 'position_z', 'width', 'height', 'depth']:
                        setattr(element, key, Decimal(str(value)))
                    else:
                        setattr(element, key, value)
            element.updated_at = datetime.now()
            log_info(f"Updated element {element_id}")
            return True
        log_error(f"Element {element_id} not found")
        return False
    
    def delete_element(self, element_id: str) -> bool:
        """Delete an element."""
        if element_id in self.elements:
            del self.elements[element_id]
            log_info(f"Deleted element {element_id}")
            return True
        log_error(f"Element {element_id} not found")
        return False
    
    def list_elements(self, element_type: Optional[ElementType] = None) -> List[DigitalElement]:
        """List all elements, optionally filtered by type."""
        if element_type:
            return [elem for elem in self.elements.values() if elem.element_type == element_type]
        return list(self.elements.values())
    
    def to_svgx_document(self) -> str:
        """Generate complete SVGX XML document."""
        root = ET.Element("svgx_document")
        root.set("version", "1.0")
        root.set("created_at", datetime.now().isoformat())
        
        # Add precision configuration
        precision_el = ET.SubElement(root, "precision_config")
        precision_el.set("level", PrecisionLevel.MICRON.name)
        precision_el.set("display_mode", PrecisionDisplayMode.DECIMAL.name)
        
        # Add all elements
        elements_el = ET.SubElement(root, "elements")
        for element in self.elements.values():
            elements_el.append(element.to_svgx_element())
        
        # Pretty print XML
        rough_string = ET.tostring(root, 'unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def to_gus_instructions(self) -> List[str]:
        """Generate natural language instructions for GUS."""
        instructions = []
        for element in self.elements.values():
            instructions.append(element.to_gus_instruction())
        return instructions
    
    def export_for_gus(self, format_type: str = "svgx") -> str:
        """Export data for GUS processing."""
        if format_type == "svgx":
            return self.to_svgx_document()
        elif format_type == "instructions":
            return "\n".join(self.to_gus_instructions())
        elif format_type == "json":
            import json
            data = {
                "elements": [
                    {
                        "id": elem.id,
                        "type": elem.element_type.value,
                        "position": [float(elem.position_x), float(elem.position_y), float(elem.position_z)],
                        "dimensions": [float(elem.width), float(elem.height), float(elem.depth)],
                        "properties": elem.properties,
                        "cad_primitives_count": len(elem.cad_primitives),
                        "constraints_count": len(elem.constraints)
                    }
                    for elem in self.elements.values()
                ],
                "total_elements": len(self.elements),
                "export_format": "json"
            }
            return json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def import_from_svgx(self, svgx_content: str):
        """Import elements from SVGX content."""
        try:
            root = ET.fromstring(svgx_content)
            self.elements.clear()
            
            elements_el = root.find("elements")
            if elements_el is not None:
                for elem_el in elements_el.findall("digital_element"):
                    element_id = elem_el.get("id")
                    element_type = ElementType(elem_el.get("type"))
                    
                    # Parse basic properties
                    element = DigitalElement(
                        id=element_id,
                        element_type=element_type,
                        position_x=Decimal(elem_el.get("position_x")),
                        position_y=Decimal(elem_el.get("position_y")),
                        position_z=Decimal(elem_el.get("position_z")),
                        width=Decimal(elem_el.get("width")),
                        height=Decimal(elem_el.get("height")),
                        depth=Decimal(elem_el.get("depth")),
                        measurement_unit=MeasurementUnit(elem_el.get("measurement_unit")),
                        precision_level=PrecisionLevel(elem_el.get("precision_level"))
                    )
                    
                    # Parse properties
                    props_el = elem_el.find("properties")
                    if props_el is not None:
                        for prop_el in props_el.findall("property"):
                            key = prop_el.get("key")
                            value = prop_el.get("value")
                            element.properties[key] = value
                    
                    # Parse connections
                    conn_el = elem_el.find("connections")
                    if conn_el is not None:
                        for conn_item in conn_el.findall("connection"):
                            element.connections.append(conn_item.get("id"))
                    
                    self.elements[element_id] = element
                
                log_info(f"Imported {len(self.elements)} elements from SVGX")
            else:
                log_warning("No elements found in SVGX content")
                
        except Exception as e:
            log_error(f"Error importing from SVGX: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the infrastructure."""
        total_elements = len(self.elements)
        element_types = {}
        total_cad_primitives = 0
        total_constraints = 0
        
        for element in self.elements.values():
            element_types[element.element_type.value] = element_types.get(element.element_type.value, 0) + 1
            total_cad_primitives += len(element.cad_primitives)
            total_constraints += len(element.constraints)
        
        return {
            "total_elements": total_elements,
            "element_types": element_types,
            "total_cad_primitives": total_cad_primitives,
            "total_constraints": total_constraints,
            "precision_level": PrecisionLevel.MICRON.name,
            "measurement_unit": MeasurementUnit.MILLIMETER.value
        }

# Global service instance
infrastructure_service = InfrastructureAsCodeService() 