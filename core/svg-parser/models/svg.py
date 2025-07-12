"""
SVG Element Models

Defines data models for SVG elements and their properties.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class SVGElementType(Enum):
    """Types of SVG elements"""
    RECT = "rect"
    CIRCLE = "circle"
    ELLIPSE = "ellipse"
    LINE = "line"
    POLYLINE = "polyline"
    POLYGON = "polygon"
    PATH = "path"
    TEXT = "text"
    GROUP = "g"
    UNKNOWN = "unknown"


@dataclass
class SVGAttribute:
    """Represents an SVG attribute with name and value."""
    name: str
    value: str
    
    def __str__(self) -> str:
        return f'{self.name}="{self.value}"'


@dataclass
class SVGElement:
    """Represents an SVG element with its properties and attributes."""
    
    tag: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    content: Optional[str] = None
    children: List['SVGElement'] = field(default_factory=list)
    element_type: SVGElementType = SVGElementType.UNKNOWN
    position: List[float] = field(default_factory=lambda: [0.0, 0.0])
    
    def __post_init__(self):
        """Set element type based on tag."""
        try:
            self.element_type = SVGElementType(self.tag)
        except ValueError:
            self.element_type = SVGElementType.UNKNOWN
    
    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Get attribute value with default."""
        return self.attributes.get(key, default)
    
    def has_attribute(self, key: str) -> bool:
        """Check if element has attribute."""
        return key in self.attributes
    
    def get_id(self) -> Optional[str]:
        """Get element ID."""
        return self.attributes.get('id')
    
    def get_class(self) -> str:
        """Get element class."""
        return self.attributes.get('class', '')
    
    def get_position(self) -> Dict[str, float]:
        """Get element position."""
        position = {}
        
        if self.tag == 'rect':
            position['x'] = float(self.attributes.get('x', 0))
            position['y'] = float(self.attributes.get('y', 0))
        elif self.tag in ['circle', 'ellipse']:
            position['x'] = float(self.attributes.get('cx', 0))
            position['y'] = float(self.attributes.get('cy', 0))
        elif self.tag == 'line':
            position['x1'] = float(self.attributes.get('x1', 0))
            position['y1'] = float(self.attributes.get('y1', 0))
            position['x2'] = float(self.attributes.get('x2', 0))
            position['y2'] = float(self.attributes.get('y2', 0))
        elif self.tag == 'text':
            position['x'] = float(self.attributes.get('x', 0))
            position['y'] = float(self.attributes.get('y', 0))
        
        return position
    
    def get_size(self) -> Dict[str, float]:
        """Get element size."""
        size = {}
        
        if self.tag == 'rect':
            size['width'] = float(self.attributes.get('width', 0))
            size['height'] = float(self.attributes.get('height', 0))
        elif self.tag == 'circle':
            size['radius'] = float(self.attributes.get('r', 0))
        elif self.tag == 'ellipse':
            size['rx'] = float(self.attributes.get('rx', 0))
            size['ry'] = float(self.attributes.get('ry', 0))
        
        return size
    
    def get_style(self) -> Dict[str, str]:
        """Get element style properties."""
        style_str = self.attributes.get('style', '')
        style_dict = {}
        
        if style_str:
            for item in style_str.split(';'):
                if ':' in item:
                    key, value = item.split(':', 1)
                    style_dict[key.strip()] = value.strip()
        
        return style_dict
    
    def is_visible(self) -> bool:
        """Check if element is visible."""
        style = self.get_style()
        display = style.get('display', '')
        visibility = style.get('visibility', '')
        
        return display != 'none' and visibility != 'hidden'
    
    def get_bounding_box(self) -> Dict[str, float]:
        """Get element bounding box."""
        position = self.get_position()
        size = self.get_size()
        
        if self.tag == 'rect':
            return {
                'x': position.get('x', 0),
                'y': position.get('y', 0),
                'width': size.get('width', 0),
                'height': size.get('height', 0)
            }
        elif self.tag in ['circle', 'ellipse']:
            radius = size.get('radius', 0)
            rx = size.get('rx', radius)
            ry = size.get('ry', radius)
            return {
                'x': position.get('x', 0) - rx,
                'y': position.get('y', 0) - ry,
                'width': rx * 2,
                'height': ry * 2
            }
        else:
            return {
                'x': 0,
                'y': 0,
                'width': 0,
                'height': 0
            }


@dataclass
class SVGDocument:
    """Represents a complete SVG document."""
    
    width: float
    height: float
    viewbox: Optional[List[float]] = None
    elements: List[SVGElement] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_element_by_id(self, element_id: str) -> Optional[SVGElement]:
        """Get element by ID."""
        for element in self.elements:
            if element.get_id() == element_id:
                return element
        return None
    
    def get_elements_by_class(self, class_name: str) -> List[SVGElement]:
        """Get elements by class name."""
        return [
            element for element in self.elements
            if class_name in element.get_class().split()
        ]
    
    def get_elements_by_type(self, element_type: SVGElementType) -> List[SVGElement]:
        """Get elements by type."""
        return [
            element for element in self.elements
            if element.element_type == element_type
        ]
    
    def get_visible_elements(self) -> List[SVGElement]:
        """Get all visible elements."""
        return [element for element in self.elements if element.is_visible()] 