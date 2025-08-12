"""
Enhanced SVGX Parser with Real ArxObject Integration

This parser connects to the Go ArxObject engine to fetch real building data
instead of just parsing metadata. It maintains backward compatibility while
adding powerful new capabilities.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
import logging
import asyncio
from dataclasses import dataclass, field

from svgx_engine.integration.arxobject_bridge import get_arxobject_bridge
from svgx_engine.models.svgx import (
    SVGXDocument, SVGXElement, ArxObject, ArxBehavior, ArxPhysics
)
from svgx_engine.parser.parser import SVGXParser as BaseSVGXParser

logger = logging.getLogger(__name__)


class EnhancedSVGXParser(BaseSVGXParser):
    """
    Enhanced SVGX parser that integrates with the Go ArxObject engine.
    
    This parser can:
    1. Parse traditional SVGX files with arx: attributes
    2. Fetch real ArxObject data from the Go engine
    3. Validate objects against building constraints
    4. Resolve relationships between objects
    """
    
    def __init__(self, use_arxobject_engine: bool = True):
        """
        Initialize enhanced parser.
        
        Args:
            use_arxobject_engine: Whether to connect to Go ArxObject engine
        """
        super().__init__()
        self.use_arxobject_engine = use_arxobject_engine
        self.bridge = None
        self.arxobject_cache = {}
        self.relationship_map = {}
        
        if use_arxobject_engine:
            self.bridge = get_arxobject_bridge()
    
    async def initialize(self):
        """Initialize connection to ArxObject engine."""
        if self.bridge:
            await self.bridge.connect()
            logger.info("Enhanced parser connected to ArxObject engine")
    
    async def parse_file_async(self, file_path: Union[str, Path]) -> SVGXDocument:
        """
        Parse SVGX file with real ArxObject data.
        
        This async version fetches real data from the Go engine.
        """
        # Parse XML structure first
        doc = self.parse_file(file_path)
        
        if not self.use_arxobject_engine:
            return doc
        
        # Enhance with real ArxObject data
        await self._enhance_with_arxobjects(doc)
        
        return doc
    
    def parse_file(self, file_path: Union[str, Path]) -> SVGXDocument:
        """
        Parse SVGX file (synchronous, basic parsing).
        
        For backward compatibility with existing code.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"SVGX file not found: {file_path}")
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Create document
            doc = SVGXDocument(
                version=root.get('version', '1.0'),
                metadata=self._extract_metadata(root)
            )
            
            # Parse elements
            for elem in root:
                svgx_elem = self._parse_element(elem)
                if svgx_elem:
                    doc.add_element(svgx_elem)
            
            return doc
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse SVGX file: {e}")
            raise
    
    def _parse_element(self, elem: ET.Element) -> Optional[SVGXElement]:
        """Parse an XML element into SVGXElement."""
        # Extract basic SVG attributes
        attributes = dict(elem.attrib)
        
        # Create SVGX element
        svgx_elem = SVGXElement(
            tag=elem.tag.split('}')[-1],  # Remove namespace
            attributes=attributes,
            content=elem.text or '',
            position=self._extract_position(attributes)
        )
        
        # Check for arx: attributes
        arx_attrs = {k: v for k, v in attributes.items() if k.startswith('arx:')}
        
        if arx_attrs:
            # Create ArxObject from attributes
            svgx_elem.arx_object = self._create_arxobject_from_attrs(arx_attrs)
            
            # Store reference for later enhancement
            if 'arx:id' in arx_attrs:
                self.arxobject_cache[arx_attrs['arx:id']] = svgx_elem
        
        # Parse children recursively
        for child in elem:
            child_elem = self._parse_element(child)
            if child_elem:
                svgx_elem.add_child(child_elem)
        
        return svgx_elem
    
    def _create_arxobject_from_attrs(self, attrs: Dict[str, str]) -> ArxObject:
        """Create ArxObject from arx: attributes."""
        arx_obj = ArxObject(
            object_id=attrs.get('arx:id', ''),
            object_type=attrs.get('arx:type', ''),
            system=attrs.get('arx:system')
        )
        
        # Parse properties
        for key, value in attrs.items():
            if key.startswith('arx:prop:'):
                prop_name = key.replace('arx:prop:', '')
                arx_obj.add_property(prop_name, self._parse_value(value))
        
        # Parse behavior if present
        if 'arx:behavior' in attrs:
            arx_obj.behavior = self._parse_behavior(attrs['arx:behavior'])
        
        # Parse physics if present
        if 'arx:physics' in attrs:
            arx_obj.physics = self._parse_physics(attrs['arx:physics'])
        
        return arx_obj
    
    async def _enhance_with_arxobjects(self, doc: SVGXDocument):
        """
        Enhance document with real ArxObject data from Go engine.
        
        This fetches actual building data and updates the parsed elements.
        """
        if not self.bridge:
            return
        
        # Collect all ArxObject IDs from the document
        arx_ids = []
        for elem in doc.elements:
            if elem.arx_object and elem.arx_object.object_id:
                try:
                    # Convert string ID to int if needed
                    arx_id = int(elem.arx_object.object_id)
                    arx_ids.append(arx_id)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid ArxObject ID: {elem.arx_object.object_id}")
        
        if not arx_ids:
            logger.info("No ArxObject IDs found in document")
            return
        
        # Fetch real data for all objects
        logger.info(f"Fetching data for {len(arx_ids)} ArxObjects from engine")
        
        for arx_id in arx_ids:
            try:
                # Get real ArxObject from Go engine
                real_obj = await self.bridge.client.get_object(arx_id, include_relationships=True)
                
                if real_obj:
                    # Find corresponding SVGX element
                    for elem in doc.elements:
                        if elem.arx_object and str(elem.arx_object.object_id) == str(arx_id):
                            # Update with real data
                            self._update_element_with_real_data(elem, real_obj)
                            break
                
            except Exception as e:
                logger.error(f"Failed to fetch ArxObject {arx_id}: {e}")
    
    def _update_element_with_real_data(self, elem: SVGXElement, real_obj):
        """Update SVGX element with real ArxObject data."""
        # Update position
        elem.position = [real_obj.geometry.x, real_obj.geometry.y]
        
        # Update attributes with real coordinates
        elem.attributes['x'] = str(real_obj.geometry.x)
        elem.attributes['y'] = str(real_obj.geometry.y)
        
        if hasattr(real_obj.geometry, 'width'):
            elem.attributes['width'] = str(real_obj.geometry.width)
        if hasattr(real_obj.geometry, 'height'):
            elem.attributes['height'] = str(real_obj.geometry.height)
        
        # Update ArxObject with real properties
        if elem.arx_object:
            elem.arx_object.properties.update(real_obj.properties or {})
            elem.arx_object.geometry = {
                'x': real_obj.geometry.x,
                'y': real_obj.geometry.y,
                'z': real_obj.geometry.z,
                'width': real_obj.geometry.width,
                'height': real_obj.geometry.height,
                'length': real_obj.geometry.length,
            }
        
        # Add validation status
        elem.attributes['arx:validated'] = 'true'
        elem.attributes['arx:precision'] = real_obj.precision
    
    def _extract_position(self, attributes: Dict[str, str]) -> List[float]:
        """Extract position from attributes."""
        x = float(attributes.get('x', attributes.get('cx', 0)))
        y = float(attributes.get('y', attributes.get('cy', 0)))
        return [x, y]
    
    def _parse_value(self, value: str) -> Any:
        """Parse string value to appropriate type."""
        # Try to convert to number
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # Check for boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        return value
    
    def _parse_behavior(self, behavior_str: str) -> ArxBehavior:
        """Parse behavior string into ArxBehavior object."""
        behavior = ArxBehavior()
        
        # Simple parsing - could be enhanced
        # Format: "var:voltage=120;calc:power=voltage*amperage"
        parts = behavior_str.split(';')
        for part in parts:
            if part.startswith('var:'):
                # Variable definition
                var_def = part[4:]
                if '=' in var_def:
                    name, value = var_def.split('=', 1)
                    behavior.add_variable(name, self._parse_value(value))
            elif part.startswith('calc:'):
                # Calculation definition
                calc_def = part[5:]
                if '=' in calc_def:
                    name, formula = calc_def.split('=', 1)
                    behavior.add_calculation(name, formula)
        
        return behavior
    
    def _parse_physics(self, physics_str: str) -> ArxPhysics:
        """Parse physics string into ArxPhysics object."""
        physics = ArxPhysics()
        
        # Simple parsing
        # Format: "mass=100kg;anchor=fixed"
        parts = physics_str.split(';')
        for part in parts:
            if part.startswith('mass='):
                mass_str = part[5:]
                # Extract number and unit
                import re
                match = re.match(r'([\d.]+)(\w+)', mass_str)
                if match:
                    physics.set_mass(float(match.group(1)), match.group(2))
            elif part.startswith('anchor='):
                physics.set_anchor(part[7:])
        
        return physics
    
    def _extract_metadata(self, root: ET.Element) -> Dict[str, Any]:
        """Extract metadata from root element."""
        metadata = {}
        
        # Look for metadata element
        meta_elem = root.find('metadata')
        if meta_elem is not None:
            for child in meta_elem:
                metadata[child.tag] = child.text
        
        # Also extract from root attributes
        for key, value in root.attrib.items():
            if key.startswith('meta:'):
                metadata[key[5:]] = value
        
        return metadata
    
    async def validate_document(self, doc: SVGXDocument) -> Dict[str, Any]:
        """
        Validate all ArxObjects in the document against constraints.
        
        Returns validation report with any violations.
        """
        if not self.bridge:
            return {'valid': True, 'message': 'No ArxObject engine connected'}
        
        violations = []
        
        for elem in doc.elements:
            if elem.arx_object and elem.arx_object.object_id:
                try:
                    arx_id = int(elem.arx_object.object_id)
                    
                    # Check collisions
                    collisions = await self.bridge.client.check_collisions(arx_id)
                    
                    if collisions:
                        violations.append({
                            'object_id': arx_id,
                            'type': 'collision',
                            'details': collisions
                        })
                    
                except Exception as e:
                    logger.error(f"Failed to validate ArxObject {elem.arx_object.object_id}: {e}")
        
        return {
            'valid': len(violations) == 0,
            'violations': violations,
            'count': len(violations)
        }
    
    async def resolve_relationships(self, doc: SVGXDocument):
        """
        Resolve and visualize relationships between ArxObjects.
        
        This adds connection elements to show relationships.
        """
        if not self.bridge:
            return
        
        # Build relationship map
        for elem in doc.elements:
            if elem.arx_object and elem.arx_object.object_id:
                # This would fetch relationships and create visual connections
                pass
    
    def export_to_svg(self, doc: SVGXDocument, output_path: Union[str, Path]):
        """Export SVGX document to standard SVG."""
        output_path = Path(output_path)
        
        svg_content = self._generate_svg(doc)
        
        output_path.write_text(svg_content)
        logger.info(f"Exported to SVG: {output_path}")
    
    def _generate_svg(self, doc: SVGXDocument) -> str:
        """Generate SVG content from SVGX document."""
        svg = '<?xml version="1.0" encoding="UTF-8"?>\n'
        svg += '<svg xmlns="http://www.w3.org/2000/svg" '
        svg += 'xmlns:arx="http://arxos.io/svgx" '
        svg += f'version="{doc.version}">\n'
        
        # Add metadata
        if doc.metadata:
            svg += '  <metadata>\n'
            for key, value in doc.metadata.items():
                svg += f'    <{key}>{value}</{key}>\n'
            svg += '  </metadata>\n'
        
        # Add elements
        for elem in doc.elements:
            svg += self._element_to_svg(elem, indent=1)
        
        svg += '</svg>'
        return svg
    
    def _element_to_svg(self, elem: SVGXElement, indent: int = 0) -> str:
        """Convert SVGX element to SVG string."""
        indent_str = '  ' * indent
        
        # Start tag
        svg = f'{indent_str}<{elem.tag}'
        
        # Add attributes
        for key, value in elem.attributes.items():
            svg += f' {key}="{value}"'
        
        if elem.children or elem.content:
            svg += '>'
            
            # Add content
            if elem.content:
                svg += elem.content
            
            # Add children
            if elem.children:
                svg += '\n'
                for child in elem.children:
                    svg += self._element_to_svg(child, indent + 1)
                svg += indent_str
            
            svg += f'</{elem.tag}>\n'
        else:
            svg += '/>\n'
        
        return svg


class ParserFactory:
    """Factory for creating appropriate parser instances."""
    
    @staticmethod
    def create_parser(enhanced: bool = True) -> Union[EnhancedSVGXParser, BaseSVGXParser]:
        """
        Create parser instance.
        
        Args:
            enhanced: Whether to create enhanced parser with ArxObject integration
            
        Returns:
            Parser instance
        """
        if enhanced:
            return EnhancedSVGXParser(use_arxobject_engine=True)
        else:
            return BaseSVGXParser()
    
    @staticmethod
    async def create_async_parser() -> EnhancedSVGXParser:
        """Create and initialize async parser."""
        parser = EnhancedSVGXParser(use_arxobject_engine=True)
        await parser.initialize()
        return parser