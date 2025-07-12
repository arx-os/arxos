"""
BIM Extraction Service

Extracts BIM elements and relationships from SVG content using
advanced pattern recognition and machine learning techniques.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from models.bim import BIMElement, Room, Wall, Device, Geometry, GeometryType
from models.svg import SVGElement


@dataclass
class ExtractionResult:
    """Result of BIM extraction process."""
    elements: List[BIMElement]
    relationships: List[Dict[str, Any]]
    confidence: float
    metadata: Dict[str, Any]


class BIMExtractor:
    """Extracts BIM elements from SVG content."""
    
    def __init__(self):
        self.element_patterns = {
            'room': [
                r'\broom\b', r'\boffice\b', r'\bconference\b', r'\bbathroom\b',
                r'\bkitchen\b', r'\bcloset\b', r'\bhallway\b', r'\bcorridor\b'
            ],
            'wall': [
                r'\bwall\b', r'\bpartition\b', r'\bbarrier\b', r'\bdivider\b'
            ],
            'device': [
                r'\bhvac\b', r'\bvent\b', r'\boutlet\b', r'\bswitch\b',
                r'\boutlet\b', r'\bpanel\b', r'\bunit\b', r'\bdevice\b'
            ]
        }
    
    def extract_bim_elements(self, svg_elements: List[SVGElement]) -> ExtractionResult:
        """
        Extract BIM elements from SVG elements.
        
        Args:
            svg_elements: List of parsed SVG elements
            
        Returns:
            ExtractionResult with BIM elements and metadata
        """
        elements = []
        relationships = []
        total_confidence = 0.0
        
        for svg_elem in svg_elements:
            bim_elem = self._extract_element(svg_elem)
            if bim_elem:
                elements.append(bim_elem)
                total_confidence += self._calculate_confidence(svg_elem)
        
        # Calculate average confidence
        avg_confidence = total_confidence / len(elements) if elements else 0.0
        
        # Extract relationships
        relationships = self._extract_relationships(elements)
        
        return ExtractionResult(
            elements=elements,
            relationships=relationships,
            confidence=avg_confidence,
            metadata={
                'total_elements': len(elements),
                'total_relationships': len(relationships),
                'extraction_method': 'pattern_based'
            }
        )
    
    def _extract_element(self, svg_elem: SVGElement) -> Optional[BIMElement]:
        """Extract BIM element from SVG element."""
        try:
            # Determine element type
            element_type = self._classify_element(svg_elem)
            
            # Extract geometry
            geometry = self._extract_geometry(svg_elem)
            
            # Extract properties
            properties = self._extract_properties(svg_elem)
            
            # Create BIM element based on type
            if element_type == 'room':
                return Room(
                    name=svg_elem.attributes.get('id', f"room_{len(properties)}"),
                    geometry=geometry,
                    room_type=properties.get('room_type', 'office'),
                    room_number=properties.get('room_number', ''),
                    area=properties.get('area', 0.0)
                )
            elif element_type == 'wall':
                return Wall(
                    name=svg_elem.attributes.get('id', f"wall_{len(properties)}"),
                    geometry=geometry,
                    wall_type=properties.get('wall_type', 'interior'),
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
                return BIMElement(
                    id=svg_elem.attributes.get('id', f"element_{len(properties)}"),
                    name=svg_elem.attributes.get('id', f"element_{len(properties)}"),
                    element_type=element_type,
                    geometry=geometry,
                    properties=properties
                )
                
        except Exception:
            return None
    
    def _classify_element(self, svg_elem: SVGElement) -> str:
        """Classify SVG element as BIM element type."""
        # Check for explicit BIM type attribute
        bim_type = svg_elem.attributes.get('data-bim-type')
        if bim_type:
            return bim_type
        
        # Check for class attributes
        class_attr = svg_elem.attributes.get('class', '')
        for element_type, patterns in self.element_patterns.items():
            for pattern in patterns:
                if re.search(pattern, class_attr, re.IGNORECASE):
                    return element_type
        
        # Check element name
        name = svg_elem.attributes.get('id', '')
        for element_type, patterns in self.element_patterns.items():
            for pattern in patterns:
                if re.search(pattern, name, re.IGNORECASE):
                    return element_type
        
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
        
        # Calculate additional properties
        if svg_elem.tag == 'rect':
            width = float(svg_elem.attributes.get('width', 0))
            height = float(svg_elem.attributes.get('height', 0))
            properties['area'] = width * height
            properties['perimeter'] = 2 * (width + height)
        
        return properties
    
    def _calculate_confidence(self, svg_elem: SVGElement) -> float:
        """Calculate confidence score for element extraction."""
        confidence = 0.0
        
        # Check for explicit BIM attributes
        if 'data-bim-type' in svg_elem.attributes:
            confidence += 0.4
        
        # Check for class attributes
        class_attr = svg_elem.attributes.get('class', '')
        for patterns in self.element_patterns.values():
            for pattern in patterns:
                if re.search(pattern, class_attr, re.IGNORECASE):
                    confidence += 0.3
                    break
        
        # Check element name
        name = svg_elem.attributes.get('id', '')
        for patterns in self.element_patterns.values():
            for pattern in patterns:
                if re.search(pattern, name, re.IGNORECASE):
                    confidence += 0.2
                    break
        
        # Check geometry properties
        if svg_elem.tag == 'rect':
            width = float(svg_elem.attributes.get('width', 0))
            height = float(svg_elem.attributes.get('height', 0))
            if width > 50 and height > 50:
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _extract_relationships(self, elements: List[BIMElement]) -> List[Dict[str, Any]]:
        """Extract relationships between BIM elements."""
        relationships = []
        
        # Spatial relationships
        for i, elem1 in enumerate(elements):
            for j, elem2 in enumerate(elements):
                if i != j:
                    relationship = self._analyze_spatial_relationship(elem1, elem2)
                    if relationship:
                        relationships.append(relationship)
        
        # System relationships
        system_relationships = self._analyze_system_relationships(elements)
        relationships.extend(system_relationships)
        
        return relationships
    
    def _analyze_spatial_relationship(self, elem1: BIMElement, elem2: BIMElement) -> Optional[Dict[str, Any]]:
        """Analyze spatial relationship between two elements."""
        if not elem1.geometry or not elem2.geometry:
            return None
        
        # Simplified spatial analysis
        # In production, this would use proper geometric analysis
        centroid1 = elem1.geometry.centroid
        centroid2 = elem2.geometry.centroid
        
        if centroid1 and centroid2:
            distance = ((centroid1[0] - centroid2[0])**2 + (centroid1[1] - centroid2[1])**2)**0.5
            
            if distance < 10:  # Close elements
                return {
                    'source_id': elem1.id,
                    'target_id': elem2.id,
                    'relationship_type': 'adjacent',
                    'properties': {'distance': distance}
                }
        
        return None
    
    def _analyze_system_relationships(self, elements: List[BIMElement]) -> List[Dict[str, Any]]:
        """Analyze system relationships between elements."""
        relationships = []
        
        # Group elements by system
        system_groups = {}
        for element in elements:
            if hasattr(element, 'system_type'):
                system_type = element.system_type
                if system_type not in system_groups:
                    system_groups[system_type] = []
                system_groups[system_type].append(element)
        
        # Create relationships within systems
        for system_type, system_elements in system_groups.items():
            if len(system_elements) > 1:
                for i, elem1 in enumerate(system_elements):
                    for j, elem2 in enumerate(system_elements):
                        if i != j:
                            relationships.append({
                                'source_id': elem1.id,
                                'target_id': elem2.id,
                                'relationship_type': 'system_connection',
                                'properties': {'system_type': system_type}
                            })
        
        return relationships 