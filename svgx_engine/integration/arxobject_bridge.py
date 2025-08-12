"""
ArxObject to SVGX Bridge

This module provides the critical integration between the high-performance
Go ArxObject engine and the SVGX rendering system.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

# Import real ArxObject client
from services.arxobject.client.python_client import ArxObjectClient, ArxObject as GoArxObject

# Import SVGX models
from svgx_engine.models.svgx import SVGXElement, ArxObject as SVGXArxObject, ArxBehavior, ArxPhysics

logger = logging.getLogger(__name__)


class ArxObjectToSVGXBridge:
    """
    Bridge between Go ArxObject engine and SVGX rendering.
    
    This is the critical integration point that allows SVGX to render
    real ArxObjects with all their spatial and constraint data.
    """
    
    def __init__(self, arxobject_host: str = "localhost", arxobject_port: int = 50051):
        """Initialize bridge with ArxObject service connection."""
        self.client = ArxObjectClient(arxobject_host, arxobject_port)
        self.type_to_svg_map = self._init_type_mappings()
        self.style_cache = {}
        
    async def connect(self):
        """Connect to ArxObject service."""
        await self.client.connect()
        logger.info("Connected to ArxObject service for SVGX rendering")
    
    async def arxobject_to_svgx(self, object_id: int) -> SVGXElement:
        """
        Convert a Go ArxObject to SVGX element.
        
        This is the core conversion that brings real building data into SVG.
        """
        # Fetch real ArxObject from Go service
        go_obj = await self.client.get_object(object_id, include_relationships=True)
        
        if not go_obj:
            raise ValueError(f"ArxObject {object_id} not found")
        
        # Create SVGX element based on object type
        svg_tag = self._get_svg_tag(go_obj.type)
        
        # Convert coordinates from mm to SVG units
        x = go_obj.geometry.x  # Already in drawing units
        y = go_obj.geometry.y
        
        # Create base SVG element
        svgx_element = SVGXElement(
            tag=svg_tag,
            attributes={
                'id': f'arx-{go_obj.id}',
                'x': str(x),
                'y': str(y),
                'class': self._get_css_class(go_obj.type),
                # ArxObject namespace attributes
                'arx:id': str(go_obj.id),
                'arx:type': go_obj.type,
                'arx:system': self._get_system_type(go_obj.type),
                'arx:precision': go_obj.precision,
            },
            position=[x, y]
        )
        
        # Add geometry based on object type
        self._add_geometry_attributes(svgx_element, go_obj)
        
        # Convert ArxObject data to SVGX ArxObject
        svgx_arx = SVGXArxObject(
            object_id=str(go_obj.id),
            object_type=go_obj.type,
            system=self._get_system_type(go_obj.type),
            properties=go_obj.properties or {},
            geometry={
                'x': go_obj.geometry.x,
                'y': go_obj.geometry.y,
                'z': go_obj.geometry.z,
                'width': go_obj.geometry.width,
                'height': go_obj.geometry.height,
                'length': go_obj.geometry.length,
            }
        )
        
        # Add behavior if electrical/mechanical
        if self._has_behavior(go_obj.type):
            svgx_arx.behavior = self._create_behavior(go_obj)
        
        # Add physics if structural
        if self._has_physics(go_obj.type):
            svgx_arx.physics = self._create_physics(go_obj)
        
        svgx_element.arx_object = svgx_arx
        
        return svgx_element
    
    async def query_and_render(
        self,
        min_x: float, min_y: float,
        max_x: float, max_y: float,
        object_types: Optional[List[str]] = None
    ) -> List[SVGXElement]:
        """
        Query ArxObjects in a region and convert to SVGX.
        
        This enables efficient rendering of building sections.
        """
        # Query Go engine for objects in region
        go_objects = await self.client.query_region(
            min_x, min_y, 0,  # Z=0 for floor plan
            max_x, max_y, 100,  # Z=100 for reasonable height
            object_types=object_types
        )
        
        # Convert all to SVGX
        svgx_elements = []
        for go_obj in go_objects:
            try:
                element = await self._quick_convert(go_obj)
                svgx_elements.append(element)
            except Exception as e:
                logger.error(f"Failed to convert ArxObject {go_obj.id}: {e}")
        
        return svgx_elements
    
    async def render_with_relationships(self, object_id: int) -> Dict[str, Any]:
        """
        Render an ArxObject with all its relationships as SVG graph.
        
        This creates connected diagrams showing electrical circuits,
        plumbing connections, etc.
        """
        # Get object and relationships from Go engine
        go_obj = await self.client.get_object(object_id, include_relationships=True)
        
        # Convert main object
        main_element = await self.arxobject_to_svgx(object_id)
        
        # Get connected objects
        # This would query relationships and render connection lines
        connections = []
        
        return {
            'main': main_element,
            'connections': connections,
            'svg': self._generate_relationship_svg(main_element, connections)
        }
    
    def _quick_convert(self, go_obj: GoArxObject) -> SVGXElement:
        """Quick conversion for batch rendering."""
        svg_tag = self._get_svg_tag(go_obj.type)
        
        # Simplified conversion for performance
        return SVGXElement(
            tag=svg_tag,
            attributes={
                'id': f'arx-{go_obj.id}',
                'x': str(go_obj.geometry.x),
                'y': str(go_obj.geometry.y),
                'width': str(go_obj.geometry.width),
                'height': str(go_obj.geometry.height),
                'class': self._get_css_class(go_obj.type),
                'arx:id': str(go_obj.id),
                'arx:type': go_obj.type,
            },
            position=[go_obj.geometry.x, go_obj.geometry.y]
        )
    
    def _get_svg_tag(self, object_type: str) -> str:
        """Map ArxObject type to SVG element tag."""
        type_map = {
            'ELECTRICAL_OUTLET': 'circle',
            'ELECTRICAL_PANEL': 'rect',
            'STRUCTURAL_WALL': 'rect',
            'STRUCTURAL_COLUMN': 'rect',
            'STRUCTURAL_BEAM': 'line',
            'PLUMBING_PIPE': 'line',
            'HVAC_DUCT': 'rect',
        }
        return type_map.get(object_type, 'rect')
    
    def _get_css_class(self, object_type: str) -> str:
        """Get CSS class for object type."""
        if 'ELECTRICAL' in object_type:
            return 'electrical-component'
        elif 'STRUCTURAL' in object_type:
            return 'structural-component'
        elif 'PLUMBING' in object_type:
            return 'plumbing-component'
        elif 'HVAC' in object_type:
            return 'hvac-component'
        return 'building-component'
    
    def _get_system_type(self, object_type: str) -> str:
        """Extract system type from object type."""
        if 'ELECTRICAL' in object_type:
            return 'electrical'
        elif 'STRUCTURAL' in object_type:
            return 'structural'
        elif 'PLUMBING' in object_type:
            return 'plumbing'
        elif 'HVAC' in object_type:
            return 'hvac'
        return 'general'
    
    def _add_geometry_attributes(self, element: SVGXElement, go_obj: GoArxObject):
        """Add geometry-specific attributes based on object type."""
        if element.tag == 'circle':
            # For outlets, etc.
            element.attributes['cx'] = str(go_obj.geometry.x)
            element.attributes['cy'] = str(go_obj.geometry.y)
            element.attributes['r'] = '10'  # Standard outlet radius
        elif element.tag == 'rect':
            # For panels, walls, etc.
            element.attributes['width'] = str(go_obj.geometry.width)
            element.attributes['height'] = str(go_obj.geometry.height)
        elif element.tag == 'line':
            # For pipes, beams, etc.
            element.attributes['x1'] = str(go_obj.geometry.x)
            element.attributes['y1'] = str(go_obj.geometry.y)
            element.attributes['x2'] = str(go_obj.geometry.x + go_obj.geometry.length)
            element.attributes['y2'] = str(go_obj.geometry.y)
    
    def _has_behavior(self, object_type: str) -> bool:
        """Check if object type should have behavior."""
        return 'ELECTRICAL' in object_type or 'HVAC' in object_type
    
    def _has_physics(self, object_type: str) -> bool:
        """Check if object type should have physics."""
        return 'STRUCTURAL' in object_type
    
    def _create_behavior(self, go_obj: GoArxObject) -> ArxBehavior:
        """Create ArxBehavior from Go ArxObject properties."""
        behavior = ArxBehavior()
        
        # Add electrical properties as variables
        if 'voltage' in go_obj.properties:
            behavior.add_variable('voltage', go_obj.properties['voltage'], 'V')
        if 'amperage' in go_obj.properties:
            behavior.add_variable('amperage', go_obj.properties['amperage'], 'A')
        
        # Add power calculation
        if 'voltage' in go_obj.properties and 'amperage' in go_obj.properties:
            behavior.add_calculation('power', 'voltage * amperage')
        
        return behavior
    
    def _create_physics(self, go_obj: GoArxObject) -> ArxPhysics:
        """Create ArxPhysics from Go ArxObject properties."""
        physics = ArxPhysics()
        
        # Add structural properties
        if 'load_capacity' in go_obj.properties:
            physics.add_force('load_capacity', 'vertical', go_obj.properties['load_capacity'])
        
        if 'material' in go_obj.properties:
            # Set mass based on material and volume
            volume = (go_obj.geometry.length * go_obj.geometry.width * go_obj.geometry.height) / 1e9  # mm³ to m³
            density = self._get_material_density(go_obj.properties['material'])
            physics.set_mass(volume * density, 'kg')
        
        return physics
    
    def _get_material_density(self, material: str) -> float:
        """Get material density in kg/m³."""
        densities = {
            'steel': 7850,
            'concrete': 2400,
            'wood': 600,
            'aluminum': 2700,
        }
        return densities.get(material.lower(), 1000)
    
    def _generate_relationship_svg(self, main: SVGXElement, connections: List) -> str:
        """Generate SVG with relationship connections."""
        svg = f'<g id="relationships-{main.attributes["id"]}">\n'
        
        # Add main element
        svg += f'  <use href="#{main.attributes["id"]}" />\n'
        
        # Add connection lines
        for conn in connections:
            svg += f'  <line class="relationship-line" '
            svg += f'x1="{main.position[0]}" y1="{main.position[1]}" '
            svg += f'x2="{conn["x"]}" y2="{conn["y"]}" />\n'
        
        svg += '</g>'
        return svg
    
    def _init_type_mappings(self) -> Dict[str, str]:
        """Initialize object type to SVG mappings."""
        return {
            'ELECTRICAL_OUTLET': 'electrical-outlet-symbol',
            'ELECTRICAL_PANEL': 'electrical-panel-symbol',
            'STRUCTURAL_BEAM': 'structural-beam-symbol',
            'PLUMBING_FIXTURE': 'plumbing-fixture-symbol',
        }


# Singleton instance for global use
_bridge_instance = None

def get_arxobject_bridge() -> ArxObjectToSVGXBridge:
    """Get or create the ArxObject to SVGX bridge."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = ArxObjectToSVGXBridge()
    return _bridge_instance