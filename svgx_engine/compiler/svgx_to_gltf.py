"""
SVGX to GLTF Compiler for 3D visualization.

This module compiles SVGX content to GLTF format for 3D visualization
and VR/AR applications.
"""

import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SVGXToGLTFCompiler:
    """Compiler for converting SVGX to GLTF format."""
    
    def __init__(self):
        self.gltf_version = "2.0"
        self.asset_info = {
            "version": self.gltf_version,
            "generator": "SVGX Engine"
        }
    
    def compile(self, svgx_content: str) -> str:
        """
        Compile SVGX content to GLTF format.
        
        Args:
            svgx_content: SVGX content as string
            
        Returns:
            GLTF content as JSON string
        """
        try:
            # Parse SVGX content using the parser
            from ..parser import SVGXParser
            parser = SVGXParser()
            elements = parser.parse(svgx_content)
            
            # Generate GLTF content
            gltf_content = self._generate_gltf_content(elements)
            
            return json.dumps(gltf_content, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to compile SVGX to GLTF: {e}")
            raise ValueError(f"Compilation failed: {e}")
    
    def _generate_gltf_content(self, elements: List) -> Dict[str, Any]:
        """
        Generate GLTF content from SVGX elements.
        
        Args:
            elements: List of parsed SVGX elements
            
        Returns:
            GLTF content as dictionary
        """
        gltf = {
            "asset": self.asset_info,
            "scene": 0,
            "scenes": [{
                "name": "SVGX Scene",
                "nodes": []
            }],
            "nodes": [],
            "meshes": [],
            "materials": [],
            "accessors": [],
            "bufferViews": [],
            "buffers": []
        }
        
        # Process SVGX objects
        node_id = 0
        mesh_id = 0
        material_id = 0
        
        for element in elements:
            if element.arx_object:
                # Create node
                node = self._create_node(element, node_id)
                gltf["nodes"].append(node)
                gltf["scenes"][0]["nodes"].append(node_id)
                node_id += 1
                
                # Create mesh if needed
                if self._needs_mesh(element):
                    mesh = self._create_mesh(element, mesh_id, material_id)
                    gltf["meshes"].append(mesh)
                    mesh_id += 1
                    material_id += 1
        
        return gltf
    
    def _create_node(self, element, node_id: int) -> Dict[str, Any]:
        """Create a GLTF node from SVGX element."""
        node = {
            "name": element.arx_object.object_id,
            "matrix": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        }
        
        # Add mesh if element has geometry
        if self._needs_mesh(element):
            node["mesh"] = node_id
        
        # Add physics properties if available
        if element.arx_physics:
            node["extras"] = {
                "physics": {
                    "mass": element.arx_physics.mass,
                    "anchor": element.arx_physics.anchor,
                    "forces": element.arx_physics.forces
                }
            }
        
        # Add behavior properties if available
        if element.arx_behavior:
            if "extras" not in node:
                node["extras"] = {}
            node["extras"]["behavior"] = {
                "variables": element.arx_behavior.variables,
                "calculations": element.arx_behavior.calculations,
                "triggers": element.arx_behavior.triggers
            }
        
        return node
    
    def _needs_mesh(self, element) -> bool:
        """Determine if element needs a mesh representation."""
        # Basic check - if it has geometric attributes, it needs a mesh
        geometric_attrs = ['x', 'y', 'width', 'height', 'cx', 'cy', 'r', 'd']
        return any(attr in element.attributes for attr in geometric_attrs)
    
    def _create_mesh(self, element, mesh_id: int, material_id: int) -> Dict[str, Any]:
        """Create a GLTF mesh from SVGX element."""
        mesh = {
            "name": f"mesh_{element.arx_object.object_id}",
            "primitives": [{
                "attributes": self._get_geometry_attributes(element),
                "material": material_id
            }]
        }
        
        return mesh
    
    def _get_geometry_attributes(self, element) -> Dict[str, int]:
        """Get geometry attributes for mesh."""
        # Basic implementation - would need more sophisticated geometry generation
        # For now, return empty attributes
        return {}
    
    def compile_file(self, input_file: str, output_file: str):
        """
        Compile SVGX file to GLTF file.
        
        Args:
            input_file: Path to input SVGX file
            output_file: Path to output GLTF file
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                svgx_content = f.read()
            
            gltf_content = self.compile(svgx_content)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(gltf_content)
            
            logger.info(f"Compiled {input_file} to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to compile file {input_file}: {e}")
            raise 