"""
Parametric Modeling System for SVGX Engine

Provides parameter-driven design capabilities including parameter definition,
relationships, parametric geometry generation, and assembly support.

CTO Directives:
- Enterprise-grade parametric modeling
- Parameter-driven design capabilities
- Comprehensive parameter relationships
- Parametric geometry generation
- Parameter validation and constraints
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any, Union
from decimal import Decimal
import logging
import re

from .precision_system import PrecisionPoint, PrecisionLevel

logger = logging.getLogger(__name__)

class ParameterType(Enum):
    """Parameter Types"""
    LENGTH = "length"
    ANGLE = "angle"
    RADIUS = "radius"
    DIAMETER = "diameter"
    AREA = "area"
    VOLUME = "volume"
    STRING = "string"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    REAL = "real"

class ParameterStatus(Enum):
    """Parameter Status"""
    VALID = "valid"
    INVALID = "invalid"
    DEPENDENT = "dependent"
    INDEPENDENT = "independent"
    CONSTRAINED = "constrained"

@dataclass
class Parameter:
    """Parameter definition"""
    parameter_id: str
    name: str
    parameter_type: ParameterType
    value: Any
    unit: str = ""
    description: str = ""
    status: ParameterStatus = ParameterStatus.INDEPENDENT
    constraints: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    expressions: List[str] = field(default_factory=list)
    precision_level: PrecisionLevel = PrecisionLevel.SUB_MILLIMETER
    
    def validate(self) -> bool:
        """Validate parameter"""
        try:
            # Check value type
            if self.parameter_type == ParameterType.LENGTH:
                return isinstance(self.value, (int, float, Decimal)) and self.value > 0
            elif self.parameter_type == ParameterType.ANGLE:
                return isinstance(self.value, (int, float, Decimal)) and 0 <= self.value <= 360
            elif self.parameter_type == ParameterType.RADIUS:
                return isinstance(self.value, (int, float, Decimal)) and self.value > 0
            elif self.parameter_type == ParameterType.DIAMETER:
                return isinstance(self.value, (int, float, Decimal)) and self.value > 0
            elif self.parameter_type == ParameterType.STRING:
                return isinstance(self.value, str)
            elif self.parameter_type == ParameterType.BOOLEAN:
                return isinstance(self.value, bool)
            elif self.parameter_type == ParameterType.INTEGER:
                return isinstance(self.value, int)
            elif self.parameter_type == ParameterType.REAL:
                return isinstance(self.value, (int, float, Decimal))
            
            return True
            
        except Exception as e:
            logger.error(f"Parameter validation error: {e}")
            return False
    
    def get_value(self) -> Any:
        """Get parameter value"""
        return self.value
    
    def set_value(self, value: Any) -> bool:
        """Set parameter value"""
        old_value = self.value
        self.value = value
        
        if not self.validate():
            self.value = old_value
            return False
        
        return True

@dataclass
class ParameterExpression:
    """Parameter expression for relationships"""
    expression_id: str
    expression: str
    target_parameter: str
    source_parameters: List[str]
    expression_type: str = "formula"  # formula, constraint, function
    
    def evaluate(self, parameters: Dict[str, Parameter]) -> Any:
        """Evaluate expression"""
        try:
            # Create local variables for source parameters
            locals_dict = {}
            for param_id in self.source_parameters:
                if param_id in parameters:
                    param = parameters[param_id]
                    locals_dict[param.name] = param.get_value()
            
            # Add math functions
            locals_dict.update({
                'math': math,
                'sqrt': math.sqrt,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'pi': math.pi,
                'abs': abs,
                'min': min,
                'max': max
            })
            
            # Evaluate expression
            result = eval(self.expression, {"__builtins__": {}}, locals_dict)
            return result
            
        except Exception as e:
            logger.error(f"Expression evaluation error: {e}")
            return None

@dataclass
class ParametricGeometry:
    """Parametric geometry definition"""
    geometry_id: str
    geometry_type: str  # line, circle, rectangle, polygon, etc.
    parameters: Dict[str, Parameter]
    expressions: List[ParameterExpression]
    constraints: List[str] = field(default_factory=list)
    assembly_id: Optional[str] = None
    
    def generate_geometry(self) -> Dict[str, Any]:
        """Generate geometry from parameters"""
        try:
            # Evaluate all expressions first
            for expression in self.expressions:
                result = expression.evaluate(self.parameters)
                if result is not None:
                    target_param = self.parameters.get(expression.target_parameter)
                    if target_param:
                        target_param.set_value(result)
            
            # Generate geometry based on type
            if self.geometry_type == "line":
                return self._generate_line()
            elif self.geometry_type == "circle":
                return self._generate_circle()
            elif self.geometry_type == "rectangle":
                return self._generate_rectangle()
            elif self.geometry_type == "polygon":
                return self._generate_polygon()
            else:
                logger.warning(f"Unknown geometry type: {self.geometry_type}")
                return {}
                
        except Exception as e:
            logger.error(f"Geometry generation error: {e}")
            return {}
    
    def _generate_line(self) -> Dict[str, Any]:
        """Generate line geometry"""
        start_x = self.parameters.get('start_x', Parameter('', 'start_x', ParameterType.REAL, 0))
        start_y = self.parameters.get('start_y', Parameter('', 'start_y', ParameterType.REAL, 0))
        length = self.parameters.get('length', Parameter('', 'length', ParameterType.LENGTH, 10))
        angle = self.parameters.get('angle', Parameter('', 'angle', ParameterType.ANGLE, 0))
        
        end_x = start_x.get_value() + length.get_value() * math.cos(math.radians(angle.get_value()))
        end_y = start_y.get_value() + length.get_value() * math.sin(math.radians(angle.get_value()))
        
        return {
            'type': 'line',
            'start_point': {'x': start_x.get_value(), 'y': start_y.get_value()},
            'end_point': {'x': end_x, 'y': end_y},
            'length': length.get_value(),
            'angle': angle.get_value()
        }
    
    def _generate_circle(self) -> Dict[str, Any]:
        """Generate circle geometry"""
        center_x = self.parameters.get('center_x', Parameter('', 'center_x', ParameterType.REAL, 0))
        center_y = self.parameters.get('center_y', Parameter('', 'center_y', ParameterType.REAL, 0))
        radius = self.parameters.get('radius', Parameter('', 'radius', ParameterType.RADIUS, 5))
        
        return {
            'type': 'circle',
            'center': {'x': center_x.get_value(), 'y': center_y.get_value()},
            'radius': radius.get_value(),
            'diameter': radius.get_value() * 2
        }
    
    def _generate_rectangle(self) -> Dict[str, Any]:
        """Generate rectangle geometry"""
        center_x = self.parameters.get('center_x', Parameter('', 'center_x', ParameterType.REAL, 0))
        center_y = self.parameters.get('center_y', Parameter('', 'center_y', ParameterType.REAL, 0))
        width = self.parameters.get('width', Parameter('', 'width', ParameterType.LENGTH, 10))
        height = self.parameters.get('height', Parameter('', 'height', ParameterType.LENGTH, 10))
        angle = self.parameters.get('angle', Parameter('', 'angle', ParameterType.ANGLE, 0))
        
        # Calculate corner points
        half_width = width.get_value() / 2
        half_height = height.get_value() / 2
        rad_angle = math.radians(angle.get_value())
        
        corners = []
        for dx, dy in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
            x = center_x.get_value() + dx * half_width * math.cos(rad_angle) - dy * half_height * math.sin(rad_angle)
            y = center_y.get_value() + dx * half_width * math.sin(rad_angle) + dy * half_height * math.cos(rad_angle)
            corners.append({'x': x, 'y': y})
        
        return {
            'type': 'rectangle',
            'center': {'x': center_x.get_value(), 'y': center_y.get_value()},
            'width': width.get_value(),
            'height': height.get_value(),
            'angle': angle.get_value(),
            'corners': corners
        }
    
    def _generate_polygon(self) -> Dict[str, Any]:
        """Generate polygon geometry"""
        center_x = self.parameters.get('center_x', Parameter('', 'center_x', ParameterType.REAL, 0))
        center_y = self.parameters.get('center_y', Parameter('', 'center_y', ParameterType.REAL, 0))
        radius = self.parameters.get('radius', Parameter('', 'radius', ParameterType.RADIUS, 5))
        sides = self.parameters.get('sides', Parameter('', 'sides', ParameterType.INTEGER, 6))
        start_angle = self.parameters.get('start_angle', Parameter('', 'start_angle', ParameterType.ANGLE, 0))
        
        vertices = []
        angle_step = 2 * math.pi / sides.get_value()
        
        for i in range(sides.get_value()):
            angle = math.radians(start_angle.get_value()) + i * angle_step
            x = center_x.get_value() + radius.get_value() * math.cos(angle)
            y = center_y.get_value() + radius.get_value() * math.sin(angle)
            vertices.append({'x': x, 'y': y})
        
        return {
            'type': 'polygon',
            'center': {'x': center_x.get_value(), 'y': center_y.get_value()},
            'radius': radius.get_value(),
            'sides': sides.get_value(),
            'start_angle': start_angle.get_value(),
            'vertices': vertices
        }

@dataclass
class ParametricAssembly:
    """Parametric assembly definition"""
    assembly_id: str
    name: str
    components: List[ParametricGeometry]
    relationships: List[ParameterExpression]
    constraints: List[str] = field(default_factory=list)
    parameters: Dict[str, Parameter] = field(default_factory=dict)
    
    def generate_assembly(self) -> Dict[str, Any]:
        """Generate complete assembly"""
        try:
            # Generate all component geometries
            component_geometries = []
            for component in self.components:
                geometry = component.generate_geometry()
                if geometry:
                    component_geometries.append({
                        'component_id': component.geometry_id,
                        'geometry': geometry,
                        'assembly_id': component.assembly_id
                    })
            
            # Apply assembly relationships
            for relationship in self.relationships:
                result = relationship.evaluate(self.parameters)
                if result is not None:
                    # Update relevant component parameters
                    for component in self.components:
                        if relationship.target_parameter in component.parameters:
                            component.parameters[relationship.target_parameter].set_value(result)
            
            return {
                'assembly_id': self.assembly_id,
                'name': self.name,
                'components': component_geometries,
                'parameters': {k: v.get_value() for k, v in self.parameters.items()}
            }
            
        except Exception as e:
            logger.error(f"Assembly generation error: {e}")
            return {}

class ParametricModelingSystem:
    """Main parametric modeling system"""
    
    def __init__(self):
        self.parameters: Dict[str, Parameter] = {}
        self.expressions: List[ParameterExpression] = []
        self.geometries: List[ParametricGeometry] = []
        self.assemblies: List[ParametricAssembly] = []
        self.parameter_counter = 0
        
        logger.info("Parametric modeling system initialized")
    
    def add_parameter(self, name: str, parameter_type: ParameterType, value: Any, 
                     unit: str = "", description: str = "") -> Parameter:
        """Add parameter to system"""
        parameter_id = f"param_{self.parameter_counter}"
        self.parameter_counter += 1
        
        parameter = Parameter(
            parameter_id=parameter_id,
            name=name,
            parameter_type=parameter_type,
            value=value,
            unit=unit,
            description=description
        )
        
        if parameter.validate():
            self.parameters[parameter_id] = parameter
            logger.info(f"Added parameter: {name}")
            return parameter
        else:
            logger.error(f"Invalid parameter: {name}")
            return None
    
    def add_expression(self, expression: str, target_parameter: str, 
                      source_parameters: List[str]) -> ParameterExpression:
        """Add parameter expression"""
        expression_id = f"expr_{len(self.expressions)}"
        
        param_expr = ParameterExpression(
            expression_id=expression_id,
            expression=expression,
            target_parameter=target_parameter,
            source_parameters=source_parameters
        )
        
        self.expressions.append(param_expr)
        logger.info(f"Added expression: {expression}")
        return param_expr
    
    def create_parametric_geometry(self, geometry_type: str, 
                                  parameters: Dict[str, Parameter],
                                  expressions: List[ParameterExpression] = None) -> ParametricGeometry:
        """Create parametric geometry"""
        geometry_id = f"geom_{len(self.geometries)}"
        
        geometry = ParametricGeometry(
            geometry_id=geometry_id,
            geometry_type=geometry_type,
            parameters=parameters,
            expressions=expressions or []
        )
        
        self.geometries.append(geometry)
        logger.info(f"Created parametric geometry: {geometry_type}")
        return geometry
    
    def create_parametric_assembly(self, name: str, components: List[ParametricGeometry],
                                  relationships: List[ParameterExpression] = None) -> ParametricAssembly:
        """Create parametric assembly"""
        assembly_id = f"assembly_{len(self.assemblies)}"
        
        assembly = ParametricAssembly(
            assembly_id=assembly_id,
            name=name,
            components=components,
            relationships=relationships or []
        )
        
        self.assemblies.append(assembly)
        logger.info(f"Created parametric assembly: {name}")
        return assembly
    
    def update_parameter(self, parameter_id: str, value: Any) -> bool:
        """Update parameter value"""
        if parameter_id in self.parameters:
            parameter = self.parameters[parameter_id]
            if parameter.set_value(value):
                # Trigger dependent updates
                self._update_dependents(parameter_id)
                return True
        
        return False
    
    def _update_dependents(self, parameter_id: str):
        """Update dependent parameters"""
        for expression in self.expressions:
            if parameter_id in expression.source_parameters:
                result = expression.evaluate(self.parameters)
                if result is not None:
                    target_param = self.parameters.get(expression.target_parameter)
                    if target_param:
                        target_param.set_value(result)
    
    def validate_system(self) -> bool:
        """Validate parametric system"""
        try:
            # Validate all parameters
            for parameter in self.parameters.values():
                if not parameter.validate():
                    logger.error(f"Invalid parameter: {parameter.name}")
                    return False
            
            # Validate all expressions
            for expression in self.expressions:
                # Test expression evaluation
                result = expression.evaluate(self.parameters)
                if result is None:
                    logger.error(f"Invalid expression: {expression.expression}")
                    return False
            
            # Validate all geometries
            for geometry in self.geometries:
                if not geometry.generate_geometry():
                    logger.error(f"Invalid geometry: {geometry.geometry_id}")
                    return False
            
            logger.info("Parametric system validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Parametric system validation failed: {e}")
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get parametric system information"""
        return {
            'parameters_count': len(self.parameters),
            'expressions_count': len(self.expressions),
            'geometries_count': len(self.geometries),
            'assemblies_count': len(self.assemblies),
            'parameter_types': list(set(p.parameter_type.value for p in self.parameters.values())),
            'geometry_types': list(set(g.geometry_type for g in self.geometries))
        }

# Global instance for easy access
parametric_modeling_system = ParametricModelingSystem() 