"""
SVGX to JSON Compiler for logic export.

This module compiles SVGX content to JSON format, extracting
behavior logic, physics data, and object properties.
"""

import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SVGXToJSONCompiler:
    """Compiler for converting SVGX to JSON format."""
    
    def __init__(self):
    """
    Perform __init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.output_structure = {
            "metadata": {},
            "objects": [],
            "behaviors": [],
            "physics": [],
            "systems": []
        }
    
    def compile(self, svgx_content: str) -> str:
        """
        Compile SVGX content to JSON format.
        
        Args:
            svgx_content: SVGX content as string
            
        Returns:
            JSON string representation
        """
        try:
            # Parse SVGX content using the parser
            from svgx_engine.parser import SVGXParser
            parser = SVGXParser()
            elements = parser.parse(svgx_content)
            
            # Extract data from elements
            result = self._extract_json_data(elements)
            
            # Convert to JSON string
            return json.dumps(result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Failed to compile SVGX to JSON: {e}")
            raise ValueError(f"Compilation failed: {e}")
    
    def _extract_json_data(self, elements: List) -> Dict[str, Any]:
        """
        Extract JSON data from SVGX elements.
        
        Args:
            elements: List of parsed SVGX elements
            
        Returns:
            Structured JSON data
        """
        result = {
            "metadata": self._extract_metadata(elements),
            "objects": self._extract_objects(elements),
            "behaviors": self._extract_behaviors(elements),
            "physics": self._extract_physics(elements),
            "systems": self._extract_systems(elements)
        }
        
        return result
    
    def _extract_metadata(self, elements: List) -> Dict[str, Any]:
        """Extract metadata from SVGX elements."""
        metadata = {}
        
        # Find root SVG element
        svg_element = next((elem for elem in elements if elem.tag == 'svg'), None)
        if svg_element:
            metadata.update({
                "version": svg_element.attributes.get('version', '1.1'),
                "width": svg_element.attributes.get('width', ''),
                "height": svg_element.attributes.get('height', ''),
                "viewBox": svg_element.attributes.get('viewBox', ''),
                "namespaces": {
                    "svg": "http://www.w3.org/2000/svg",
                    "arx": "http://arxos.io/svgx"
                }
            })
        
        return metadata
    
    def _extract_objects(self, elements: List) -> List[Dict[str, Any]]:
        """Extract object data from SVGX elements."""
        objects = []
        
        for element in elements:
            if element.arx_object:
                obj_data = {
                    "id": element.arx_object.object_id,
                    "type": element.arx_object.object_type,
                    "system": element.arx_object.system,
                    "properties": element.arx_object.properties,
                    "geometry": self._extract_geometry(element),
                    "attributes": element.attributes
                }
                objects.append(obj_data)
        
        return objects
    
    def _extract_behaviors(self, elements: List) -> List[Dict[str, Any]]:
        """Extract behavior data from SVGX elements."""
        behaviors = []
        
        for element in elements:
            if element.arx_behavior:
                behavior_data = {
                    "element_id": element.attributes.get('id', ''),
                    "variables": element.arx_behavior.variables,
                    "calculations": element.arx_behavior.calculations,
                    "triggers": element.arx_behavior.triggers
                }
                behaviors.append(behavior_data)
        
        return behaviors
    
    def _extract_physics(self, elements: List) -> List[Dict[str, Any]]:
        """Extract physics data from SVGX elements."""
        physics = []
        
        for element in elements:
            if element.arx_physics:
                physics_data = {
                    "element_id": element.attributes.get('id', ''),
                    "mass": element.arx_physics.mass,
                    "anchor": element.arx_physics.anchor,
                    "forces": element.arx_physics.forces
                }
                physics.append(physics_data)
        
        return physics
    
    def _extract_systems(self, elements: List) -> List[Dict[str, Any]]:
        """Extract system data from SVGX elements."""
        systems = []
        
        # Group objects by system
        system_groups = {}
        for element in elements:
            if element.arx_object and element.arx_object.system:
                system = element.arx_object.system
                if system not in system_groups:
                    system_groups[system] = []
                system_groups[system].append({
                    "id": element.arx_object.object_id,
                    "type": element.arx_object.object_type
                })
        
        # Convert to system list
        for system_name, components in system_groups.items():
            system_data = {
                "name": system_name,
                "components": components,
                "type": self._determine_system_type(components)
            }
            systems.append(system_data)
        
        return systems
    
    def _extract_geometry(self, element) -> Dict[str, Any]:
        """Extract geometry data from element."""
        geometry = {}
        
        # Extract basic geometric properties
        for attr in ['x', 'y', 'width', 'height', 'cx', 'cy', 'r', 'rx', 'ry']:
            if attr in element.attributes:
                geometry[attr] = element.attributes[attr]
        
        # Extract path data
        if 'd' in element.attributes:
            geometry['path'] = element.attributes['d']
        
        # Extract transform
        if 'transform' in element.attributes:
            geometry['transform'] = element.attributes['transform']
        
        return geometry
    
    def _determine_system_type(self, components: List[Dict[str, Any]]) -> str:
        """Determine system type based on components."""
        component_types = [comp['type'] for comp in components]
        
        if any('electrical' in comp_type for comp_type in component_types):
            return 'electrical'
        elif any('mechanical' in comp_type for comp_type in component_types):
            return 'mechanical'
        elif any('plumbing' in comp_type for comp_type in component_types):
            return 'plumbing'
        elif any('hvac' in comp_type for comp_type in component_types):
            return 'hvac'
        else:
            return 'general'
    
    def compile_file(self, input_file: str, output_file: str):
        """
        Compile SVGX file to JSON file.
        
        Args:
            input_file: Path to input SVGX file
            output_file: Path to output JSON file
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                svgx_content = f.read()
            
            json_content = self.compile(svgx_content)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_content)
            
            logger.info(f"Compiled {input_file} to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to compile file {input_file}: {e}")
            raise 