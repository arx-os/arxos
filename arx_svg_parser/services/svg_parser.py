"""
SVG Parser for extracting BIM elements from SVG content.
"""

import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from pathlib import Path

from models.svg import SVGElement, SVGAttribute
from models.bim import BIMElement, Room, Wall, Device, Geometry, GeometryType


class SVGParser:
    """Parser for SVG files and content."""
    
    def __init__(self):
        self.supported_elements = {
            'rect', 'circle', 'ellipse', 'line', 'polyline', 
            'polygon', 'path', 'text', 'g', 'svg'
        }
    
    def parse(self, svg_content: str) -> List[SVGElement]:
        """
        Parse SVG content and extract elements.
        
        Args:
            svg_content: SVG content as string
            
        Returns:
            List of parsed SVG elements
        """
        try:
            root = ET.fromstring(svg_content)
            elements = []
            
            # Parse root SVG element
            svg_attrs = self._extract_attributes(root)
            elements.append(SVGElement(
                tag='svg',
                attributes=svg_attrs,
                content='',
                position=[0, 0]
            ))
            
            # Parse child elements
            for child in root.iter():
                if child.tag in self.supported_elements and child != root:
                    element = self._parse_element(child)
                    if element:
                        elements.append(element)
            
            return elements
            
        except ET.ParseError as e:
            raise ValueError(f"Invalid SVG content: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse SVG: {e}")
    
    def _parse_element(self, element: ET.Element) -> Optional[SVGElement]:
        """Parse individual SVG element."""
        try:
            tag = element.tag
            attributes = self._extract_attributes(element)
            content = element.text or ''
            position = self._extract_position(attributes)
            
            return SVGElement(
                tag=tag,
                attributes=attributes,
                content=content,
                position=position
            )
        except Exception:
            return None
    
    def _extract_attributes(self, element: ET.Element) -> Dict[str, str]:
        """Extract attributes from SVG element."""
        attributes = {}
        for key, value in element.attrib.items():
            attributes[key] = value
        return attributes
    
    def _extract_position(self, attributes: Dict[str, str]) -> List[float]:
        """Extract position from element attributes."""
        x = float(attributes.get('x', 0))
        y = float(attributes.get('y', 0))
        return [x, y]
    
    def parse_file(self, file_path: str) -> List[SVGElement]:
        """
        Parse SVG file and extract elements.
        
        Args:
            file_path: Path to SVG file
            
        Returns:
            List of parsed SVG elements
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            return self.parse(svg_content)
        except FileNotFoundError:
            raise ValueError(f"SVG file not found: {file_path}")
        except Exception as e:
            raise ValueError(f"Failed to parse SVG file: {e}")
    
    def extract_bim_elements(self, svg_elements: List[SVGElement]) -> List[BIMElement]:
        """
        Extract BIM elements from SVG elements.
        
        Args:
            svg_elements: List of parsed SVG elements
            
        Returns:
            List of BIM elements
        """
        bim_elements = []
        
        for svg_elem in svg_elements:
            bim_elem = self._convert_to_bim_element(svg_elem)
            if bim_elem:
                bim_elements.append(bim_elem)
        
        return bim_elements
    
    def _convert_to_bim_element(self, svg_elem: SVGElement) -> Optional[BIMElement]:
        """Convert SVG element to BIM element."""
        try:
            # Determine element type based on SVG tag and attributes
            element_type = self._determine_element_type(svg_elem)
            
            # Extract geometry
            geometry = self._extract_geometry(svg_elem)
            
            # Extract properties
            properties = self._extract_properties(svg_elem)
            
            # Create BIM element
            if element_type == 'room':
                return Room(
                    name=svg_elem.attributes.get('id', f"room_{len(properties)}"),
                    geometry=geometry,
                    room_type=properties.get('room_type', 'unknown'),
                    room_number=properties.get('room_number', ''),
                    area=properties.get('area', 0.0)
                )
            elif element_type == 'wall':
                return Wall(
                    name=svg_elem.attributes.get('id', f"wall_{len(properties)}"),
                    geometry=geometry,
                    wall_type=properties.get('wall_type', 'unknown'),
                    thickness=properties.get('thickness', 0.2),
                    height=properties.get('height', 3.0)
                )
            elif element_type == 'device':
                return Device(
                    name=svg_elem.attributes.get('id', f"device_{len(properties)}"),
                    geometry=geometry,
                    device_type=properties.get('device_type', 'unknown'),
                    manufacturer=properties.get('manufacturer', ''),
                    model=properties.get('model', '')
                )
            else:
                # Generic BIM element
                return BIMElement(
                    id=svg_elem.attributes.get('id', f"element_{len(properties)}"),
                    name=svg_elem.attributes.get('id', f"element_{len(properties)}"),
                    element_type=element_type,
                    geometry=geometry,
                    properties=properties
                )
                
        except Exception:
            return None
    
    def _determine_element_type(self, svg_elem: SVGElement) -> str:
        """Determine BIM element type from SVG element."""
        # Check for BIM-specific attributes
        bim_type = svg_elem.attributes.get('data-bim-type')
        if bim_type:
            return bim_type
        
        # Check for class attributes
        class_attr = svg_elem.attributes.get('class', '')
        if 'room' in class_attr:
            return 'room'
        elif 'wall' in class_attr:
            return 'wall'
        elif 'device' in class_attr:
            return 'device'
        
        # Determine by SVG tag and properties
        if svg_elem.tag == 'rect':
            # Large rectangles are likely rooms
            width = float(svg_elem.attributes.get('width', 0))
            height = float(svg_elem.attributes.get('height', 0))
            if width > 50 and height > 50:
                return 'room'
            else:
                return 'wall'
        elif svg_elem.tag == 'circle':
            return 'device'
        elif svg_elem.tag == 'text':
            return 'annotation'
        else:
            return 'unknown'
    
    def _extract_geometry(self, svg_elem: SVGElement) -> Geometry:
        """Extract geometry from SVG element."""
        if svg_elem.tag == 'rect':
            x = float(svg_elem.attributes.get('x', 0))
            y = float(svg_elem.attributes.get('y', 0))
            width = float(svg_elem.attributes.get('width', 0))
            height = float(svg_elem.attributes.get('height', 0))
            
            coordinates = [
                [x, y],
                [x + width, y],
                [x + width, y + height],
                [x, y + height],
                [x, y]
            ]
            
            return Geometry(
                type=GeometryType.POLYGON,
                coordinates=[coordinates],
                properties={'width': width, 'height': height}
            )
            
        elif svg_elem.tag == 'circle':
            cx = float(svg_elem.attributes.get('cx', 0))
            cy = float(svg_elem.attributes.get('cy', 0))
            r = float(svg_elem.attributes.get('r', 0))
            
            return Geometry(
                type=GeometryType.POINT,
                coordinates=[[cx, cy]],
                properties={'radius': r}
            )
            
        elif svg_elem.tag == 'line':
            x1 = float(svg_elem.attributes.get('x1', 0))
            y1 = float(svg_elem.attributes.get('y1', 0))
            x2 = float(svg_elem.attributes.get('x2', 0))
            y2 = float(svg_elem.attributes.get('y2', 0))
            
            return Geometry(
                type=GeometryType.LINESTRING,
                coordinates=[[x1, y1], [x2, y2]],
                properties={}
            )
            
        else:
            # Default point geometry
            return Geometry(
                type=GeometryType.POINT,
                coordinates=[svg_elem.position],
                properties={}
            )
    
    def _extract_properties(self, svg_elem: SVGElement) -> Dict[str, Any]:
        """Extract properties from SVG element."""
        properties = {}
        
        # Extract common properties
        if 'fill' in svg_elem.attributes:
            properties['fill_color'] = svg_elem.attributes['fill']
        if 'stroke' in svg_elem.attributes:
            properties['stroke_color'] = svg_elem.attributes['stroke']
        if 'stroke-width' in svg_elem.attributes:
            properties['stroke_width'] = float(svg_elem.attributes['stroke-width'])
        
        # Extract BIM-specific properties
        for key, value in svg_elem.attributes.items():
            if key.startswith('data-'):
                prop_name = key[5:]  # Remove 'data-' prefix
                properties[prop_name] = value
        
        return properties 

def extract_svg_elements(svg_content: str) -> List[SVGElement]:
    """
    Extract SVG elements from SVG content.
    
    Args:
        svg_content: SVG content as string
        
    Returns:
        List of SVG elements
    """
    parser = SVGParser()
    return parser.parse(svg_content) 