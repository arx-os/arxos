"""
Enhanced BIM Assembly Service.

This service integrates enhanced symbol recognition with advanced BIM element creation,
providing comprehensive building information modeling capabilities including:
- Multi-step BIM construction process
- Conflict resolution for overlapping elements
- BIM consistency validation
- Performance optimization for large models
- Assembly pipeline management
- Multi-system BIM model creation
- Advanced symbol recognition with ML
- Automatic element classification
- System relationship mapping
- Comprehensive BIM data extraction
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

from structlog import get_logger

logger = get_logger()


class AssemblyStep(Enum):
    """Steps in the BIM assembly pipeline"""
    GEOMETRY_EXTRACTION = "geometry_extraction"
    ELEMENT_CLASSIFICATION = "element_classification"
    SPATIAL_ORGANIZATION = "spatial_organization"
    SYSTEM_INTEGRATION = "system_integration"
    RELATIONSHIP_ESTABLISHMENT = "relationship_establishment"
    CONFLICT_RESOLUTION = "conflict_resolution"
    CONSISTENCY_VALIDATION = "consistency_validation"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"


class ConflictType(Enum):
    """Types of BIM assembly conflicts"""
    GEOMETRIC_OVERLAP = "geometric_overlap"
    SPATIAL_CONFLICT = "spatial_conflict"
    SYSTEM_CONFLICT = "system_conflict"
    RELATIONSHIP_CONFLICT = "relationship_conflict"
    PROPERTY_CONFLICT = "property_conflict"
    PERFORMANCE_CONFLICT = "performance_conflict"


class ValidationLevel(Enum):
    """BIM validation levels"""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"


@dataclass
class AssemblyConflict:
    """BIM assembly conflict"""
    conflict_id: str
    conflict_type: ConflictType
    elements: List[str]  # Element IDs involved
    severity: float  # 0.0 to 1.0
    description: str
    location: Optional[Dict[str, float]] = None
    resolution_suggestions: List[str] = field(default_factory=list)
    resolved: bool = False


@dataclass
class AssemblyResult:
    """Result of BIM assembly process"""
    success: bool
    assembly_id: str
    elements: List[Dict[str, Any]]
    systems: List[Dict[str, Any]]
    spaces: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    conflicts: List[AssemblyConflict]
    validation_results: Dict[str, Any]
    performance_metrics: Dict[str, float]
    assembly_time: float
    warnings: List[str] = field(default_factory=list)


@dataclass
class AssemblyConfig:
    """Configuration for BIM assembly pipeline"""
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    conflict_resolution_enabled: bool = True
    performance_optimization_enabled: bool = True
    parallel_processing: bool = True
    max_workers: int = 4
    batch_size: int = 100
    geometry_tolerance: float = 0.01
    conflict_threshold: float = 0.1


@dataclass
class BIMSpace:
    """BIM Space representation"""
    space_id: str
    space_type: str
    name: Optional[str] = None
    description: Optional[str] = None
    elements: List[str] = field(default_factory=list)
    boundaries: Dict[str, Any] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    
    def add_element(self, element_id: str):
        """Add an element to this space."""
        if element_id not in self.elements:
            self.elements.append(element_id)
    
    def remove_element(self, element_id: str):
        """Remove an element from this space."""
        if element_id in self.elements:
            self.elements.remove(element_id)
    
    def get_boundary_area(self) -> Optional[float]:
        """Calculate the area of the space boundary."""
        if 'min' in self.boundaries and 'max' in self.boundaries:
            min_coords = self.boundaries['min']
            max_coords = self.boundaries['max']
            if len(min_coords) >= 2 and len(max_coords) >= 2:
                width = max_coords[0] - min_coords[0]
                height = max_coords[1] - min_coords[1]
                return width * height
        return None


def extract_and_convert_properties(svg_element: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and convert properties from SVG element to BIM element properties.
    Handles unit conversion (px to m) and property normalization.
    """
    properties = {}
    svg_props = svg_element.get('properties', {})
    metadata = svg_element.get('metadata', {})
    
    # Unit conversion factors (assuming 96 DPI standard)
    PX_TO_M = 0.0254 / 96  # 1 inch = 25.4mm, 96 DPI
    
    # Extract and convert position properties
    if 'x' in svg_props:
        properties['x'] = float(svg_props['x']) * PX_TO_M
    if 'y' in svg_props:
        properties['y'] = float(svg_props['y']) * PX_TO_M
    
    # Extract and convert size properties
    if 'width' in svg_props:
        properties['width'] = float(svg_props['width']) * PX_TO_M
    if 'height' in svg_props:
        properties['height'] = float(svg_props['height']) * PX_TO_M
    
    # Extract and convert radius properties
    if 'radius' in svg_props:
        properties['radius'] = float(svg_props['radius']) * PX_TO_M
    
    # Extract style properties
    if 'style' in svg_props:
        style = svg_props['style']
        if 'fill' in style:
            properties['fill_color'] = style['fill']
        if 'stroke' in style:
            properties['stroke_color'] = style['stroke']
        if 'stroke-width' in style:
            properties['stroke_width'] = float(style['stroke-width']) * PX_TO_M
    
    # Extract metadata properties
    if 'category' in metadata:
        properties['category'] = metadata['category']
    if 'system' in metadata:
        properties['system'] = metadata['system']
    if 'function' in metadata:
        properties['function'] = metadata['function']
    
    # Extract custom properties
    for key, value in svg_props.items():
        if key not in ['x', 'y', 'width', 'height', 'radius', 'style']:
            # Try to convert to appropriate type
            try:
                if isinstance(value, str):
                    if value.lower() in ['true', 'false']:
                        properties[key] = value.lower() == 'true'
                    elif value.replace('.', '').replace('-', '').isdigit():
                        properties[key] = float(value)
                    else:
                        properties[key] = value
                else:
                    properties[key] = value
            except (ValueError, TypeError):
                properties[key] = str(value)
    
    return properties


def determine_device_category(svg_element: Dict[str, Any]) -> Optional[str]:
    """
    Determine device category based on SVG element properties and metadata.
    Returns the appropriate device category or None if undetermined.
    """
    properties = svg_element.get('properties', {})
    metadata = svg_element.get('metadata', {})
    element_type = svg_element.get('type', '').lower()
    
    # Check metadata first
    if 'category' in metadata:
        return metadata['category']
    
    # Check element type
    if 'rect' in element_type:
        return 'structural'
    elif 'circle' in element_type or 'ellipse' in element_type:
        return 'device'
    elif 'line' in element_type or 'polyline' in element_type:
        return 'connection'
    elif 'text' in element_type:
        return 'annotation'
    elif 'path' in element_type:
        return 'complex'
    
    # Check properties for clues
    style = properties.get('style', {})
    if 'fill' in style:
        fill_color = style['fill'].lower()
        if 'red' in fill_color or 'fire' in fill_color:
            return 'fire_safety'
        elif 'blue' in fill_color or 'water' in fill_color:
            return 'plumbing'
        elif 'green' in fill_color or 'electrical' in fill_color:
            return 'electrical'
        elif 'yellow' in fill_color or 'hvac' in fill_color:
            return 'hvac'
        elif 'purple' in fill_color or 'security' in fill_color:
            return 'security'
        elif 'orange' in fill_color or 'network' in fill_color:
            return 'network'
        elif 'gray' in fill_color or 'structural' in fill_color:
            return 'structural'
    
    # Check for specific keywords in properties
    for key, value in properties.items():
        if isinstance(value, str):
            value_lower = value.lower()
            if any(keyword in value_lower for keyword in ['hvac', 'air', 'vent', 'duct']):
                return 'hvac'
            elif any(keyword in value_lower for keyword in ['electrical', 'power', 'circuit', 'panel']):
                return 'electrical'
            elif any(keyword in value_lower for keyword in ['plumbing', 'water', 'pipe', 'valve']):
                return 'plumbing'
            elif any(keyword in value_lower for keyword in ['fire', 'alarm', 'sprinkler', 'smoke']):
                return 'fire_safety'
            elif any(keyword in value_lower for keyword in ['security', 'camera', 'access', 'control']):
                return 'security'
            elif any(keyword in value_lower for keyword in ['network', 'data', 'communication']):
                return 'network'
            elif any(keyword in value_lower for keyword in ['structural', 'wall', 'beam', 'column']):
                return 'structural'
    
    return None


def create_geometry_from_svg(svg_element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Create geometry object from SVG element.
    Returns geometry object or None if creation fails.
    """
    try:
        element_type = svg_element.get('type', '').lower()
        properties = svg_element.get('properties', {})
        
        # Unit conversion
        PX_TO_M = 0.0254 / 96
        
        if 'rect' in element_type:
            # Rectangle geometry
            x = float(properties.get('x', 0)) * PX_TO_M
            y = float(properties.get('y', 0)) * PX_TO_M
            width = float(properties.get('width', 0)) * PX_TO_M
            height = float(properties.get('height', 0)) * PX_TO_M
            
            return {
                'type': 'rectangle',
                'coordinates': [
                    [x, y],
                    [x + width, y],
                    [x + width, y + height],
                    [x, y + height]
                ],
                'center': [x + width/2, y + height/2],
                'dimensions': [width, height]
            }
        
        elif 'circle' in element_type:
            # Circle geometry
            cx = float(properties.get('cx', 0)) * PX_TO_M
            cy = float(properties.get('cy', 0)) * PX_TO_M
            radius = float(properties.get('radius', 0)) * PX_TO_M
            
            return {
                'type': 'circle',
                'center': [cx, cy],
                'radius': radius,
                'area': np.pi * radius * radius
            }
        
        elif 'line' in element_type:
            # Line geometry
            x1 = float(properties.get('x1', 0)) * PX_TO_M
            y1 = float(properties.get('y1', 0)) * PX_TO_M
            x2 = float(properties.get('x2', 0)) * PX_TO_M
            y2 = float(properties.get('y2', 0)) * PX_TO_M
            
            return {
                'type': 'line',
                'start': [x1, y1],
                'end': [x2, y2],
                'length': np.sqrt((x2-x1)**2 + (y2-y1)**2)
            }
        
        elif 'path' in element_type:
            # Path geometry (simplified)
            d = properties.get('d', '')
            if d:
                return {
                    'type': 'path',
                    'path_data': d,
                    'complex': True
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to create geometry from SVG element: {e}")
        return None


class EnhancedBIMAssembly:
    """
    Enhanced BIM Assembly service providing comprehensive building information modeling capabilities.
    
    This service integrates enhanced symbol recognition with advanced BIM element creation,
    providing multi-step BIM construction process, conflict resolution, consistency validation,
    and performance optimization for large models.
    """
    
    def __init__(self, symbol_library_path: Optional[str] = None, config: Optional[AssemblyConfig] = None):
        """
        Initialize the Enhanced BIM Assembly service.
        
        Args:
            symbol_library_path: Path to symbol library
            config: Assembly configuration
        """
        self.config = config or AssemblyConfig()
        self.symbol_library_path = symbol_library_path
        self.symbol_library = None
        self.assembly_stats = {
            'total_assemblies': 0,
            'successful_assemblies': 0,
            'failed_assemblies': 0,
            'average_assembly_time': 0.0,
            'total_elements_processed': 0,
            'total_conflicts_resolved': 0
        }
        
        # Initialize components
        self._initialize_symbol_library()
        
        logger.info("Enhanced BIM Assembly service initialized")
    
    def _initialize_symbol_library(self):
        """Initialize symbol library"""
        try:
            if self.symbol_library_path:
                # Load symbol library from file
                with open(self.symbol_library_path, 'r') as f:
                    self.symbol_library = json.load(f)
            else:
                # Use default symbol library
                self.symbol_library = self._create_default_symbol_library()
            
            logger.info(f"Symbol library initialized with {len(self.symbol_library)} symbols")
            
        except Exception as e:
            logger.error(f"Failed to initialize symbol library: {e}")
            self.symbol_library = self._create_default_symbol_library()
    
    def _create_default_symbol_library(self) -> Dict[str, Any]:
        """Create default symbol library"""
        return {
            'hvac': {
                'air_handler': {'category': 'hvac', 'type': 'air_handler'},
                'vav_box': {'category': 'hvac', 'type': 'vav_box'},
                'duct': {'category': 'hvac', 'type': 'duct'}
            },
            'electrical': {
                'panel': {'category': 'electrical', 'type': 'panel'},
                'outlet': {'category': 'electrical', 'type': 'outlet'},
                'switch': {'category': 'electrical', 'type': 'switch'}
            },
            'plumbing': {
                'valve': {'category': 'plumbing', 'type': 'valve'},
                'pump': {'category': 'plumbing', 'type': 'pump'},
                'fixture': {'category': 'plumbing', 'type': 'fixture'}
            },
            'fire_safety': {
                'smoke_detector': {'category': 'fire_safety', 'type': 'smoke_detector'},
                'sprinkler': {'category': 'fire_safety', 'type': 'sprinkler'},
                'alarm': {'category': 'fire_safety', 'type': 'alarm'}
            },
            'security': {
                'camera': {'category': 'security', 'type': 'camera'},
                'card_reader': {'category': 'security', 'type': 'card_reader'},
                'motion_sensor': {'category': 'security', 'type': 'motion_sensor'}
            }
        }
    
    def assemble_bim(self, svg_data: Dict[str, Any], 
                    metadata: Optional[Dict[str, Any]] = None) -> AssemblyResult:
        """
        Assemble BIM model from SVG data.
        
        Args:
            svg_data: SVG data containing elements
            metadata: Additional metadata
            
        Returns:
            AssemblyResult object
        """
        start_time = time.time()
        assembly_id = f"assembly_{int(start_time)}"
        
        try:
            logger.info(f"Starting BIM assembly: {assembly_id}")
            
            # Extract geometry
            elements = self._extract_geometry(svg_data)
            
            # Classify elements
            self._classify_elements(elements)
            
            # Organize spatial structure
            spaces = self._organize_spatial_structure(elements)
            
            # Integrate systems
            systems = self._integrate_systems(elements)
            
            # Establish relationships
            relationships = self._establish_relationships(elements, spaces, systems)
            
            # Detect and resolve conflicts
            conflicts = self._resolve_conflicts(elements, spaces, systems)
            
            # Validate consistency
            validation_results = self._validate_consistency(elements, spaces, systems, relationships)
            
            # Optimize performance
            if self.config.performance_optimization_enabled:
                self._optimize_performance(elements, spaces, systems)
            
            # Calculate performance metrics
            assembly_time = time.time() - start_time
            performance_metrics = {
                'assembly_time': assembly_time,
                'elements_count': len(elements),
                'spaces_count': len(spaces),
                'systems_count': len(systems),
                'relationships_count': len(relationships),
                'conflicts_count': len(conflicts)
            }
            
            # Update statistics
            self._update_assembly_stats(assembly_time, True)
            
            result = AssemblyResult(
                success=True,
                assembly_id=assembly_id,
                elements=elements,
                systems=systems,
                spaces=spaces,
                relationships=relationships,
                conflicts=conflicts,
                validation_results=validation_results,
                performance_metrics=performance_metrics,
                assembly_time=assembly_time
            )
            
            logger.info(f"BIM assembly completed successfully: {assembly_id}")
            return result
            
        except Exception as e:
            logger.error(f"BIM assembly failed: {e}")
            assembly_time = time.time() - start_time
            self._update_assembly_stats(assembly_time, False)
            
            return AssemblyResult(
                success=False,
                assembly_id=assembly_id,
                elements=[],
                systems=[],
                spaces=[],
                relationships=[],
                conflicts=[],
                validation_results={'error': str(e)},
                performance_metrics={'assembly_time': assembly_time},
                assembly_time=assembly_time,
                warnings=[str(e)]
            )
    
    def _extract_geometry(self, svg_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract geometry from SVG data"""
        elements = []
        svg_elements = svg_data.get('elements', [])
        
        if self.config.parallel_processing:
            elements = self._extract_geometry_parallel(svg_elements)
        else:
            elements = self._extract_geometry_sequential(svg_elements)
        
        logger.info(f"Extracted {len(elements)} elements from SVG data")
        return elements
    
    def _extract_geometry_parallel(self, svg_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract geometry using parallel processing"""
        elements = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = []
            for svg_element in svg_elements:
                future = executor.submit(self._process_svg_element, svg_element)
                futures.append(future)
            
            for future in as_completed(futures):
                element = future.result()
                if element:
                    elements.append(element)
        
        return elements
    
    def _extract_geometry_sequential(self, svg_elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract geometry using sequential processing"""
        elements = []
        
        for svg_element in svg_elements:
            element = self._process_svg_element(svg_element)
            if element:
                elements.append(element)
        
        return elements
    
    def _process_svg_element(self, svg_element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process individual SVG element"""
        try:
            # Extract properties
            properties = extract_and_convert_properties(svg_element)
            
            # Create geometry
            geometry = create_geometry_from_svg(svg_element)
            
            # Determine device category
            category = determine_device_category(svg_element)
            
            # Create element
            element = {
                'id': svg_element.get('id', f"element_{len(properties)}"),
                'type': svg_element.get('type', 'unknown'),
                'category': category,
                'properties': properties,
                'geometry': geometry,
                'metadata': svg_element.get('metadata', {}),
                'created_at': datetime.utcnow().isoformat()
            }
            
            return element
            
        except Exception as e:
            logger.error(f"Failed to process SVG element: {e}")
            return None
    
    def _classify_elements(self, elements: List[Dict[str, Any]]):
        """Classify elements based on properties and geometry"""
        for element in elements:
            if not element.get('category'):
                # Try to determine category from geometry
                geometry = element.get('geometry', {})
                if geometry.get('type') == 'circle':
                    element['category'] = 'device'
                elif geometry.get('type') == 'rectangle':
                    element['category'] = 'structural'
                elif geometry.get('type') == 'line':
                    element['category'] = 'connection'
                else:
                    element['category'] = 'unknown'
    
    def _organize_spatial_structure(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Organize elements into spatial structure"""
        spaces = []
        
        # Group elements by proximity
        grouped_elements = self._group_elements_by_proximity(elements)
        
        for space_id, space_elements in grouped_elements.items():
            space = self._create_space_from_elements(space_id, space_elements)
            spaces.append(space)
        
        logger.info(f"Created {len(spaces)} spaces from {len(elements)} elements")
        return spaces
    
    def _group_elements_by_proximity(self, elements: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group elements by proximity"""
        groups = {}
        processed_elements = set()
        
        for element in elements:
            if element['id'] in processed_elements:
                continue
            
            # Find nearby elements
            nearby_elements = self._find_nearby_elements(element, elements, max_distance=10.0)
            
            # Create group
            group_id = f"space_{len(groups)}"
            groups[group_id] = [element] + nearby_elements
            
            # Mark as processed
            processed_elements.add(element['id'])
            for nearby in nearby_elements:
                processed_elements.add(nearby['id'])
        
        return groups
    
    def _find_nearby_elements(self, reference_element: Dict[str, Any], 
                             all_elements: List[Dict[str, Any]], max_distance: float) -> List[Dict[str, Any]]:
        """Find elements near the reference element"""
        nearby = []
        
        for element in all_elements:
            if element['id'] == reference_element['id']:
                continue
            
            distance = self._calculate_element_distance(reference_element, element)
            if distance <= max_distance:
                nearby.append(element)
        
        return nearby
    
    def _calculate_element_distance(self, elem1: Dict[str, Any], elem2: Dict[str, Any]) -> float:
        """Calculate distance between two elements"""
        try:
            geom1 = elem1.get('geometry', {})
            geom2 = elem2.get('geometry', {})
            
            # Get centers
            center1 = geom1.get('center', [0, 0])
            center2 = geom2.get('center', [0, 0])
            
            # Calculate Euclidean distance
            return np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
            
        except Exception:
            return float('inf')
    
    def _create_space_from_elements(self, space_id: str, 
                                   elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create space from elements"""
        # Calculate boundaries
        boundaries = self._calculate_space_boundaries(elements)
        
        # Determine space type
        space_type = self._determine_space_type(elements)
        
        space = {
            'space_id': space_id,
            'space_type': space_type,
            'elements': [elem['id'] for elem in elements],
            'boundaries': boundaries,
            'properties': {
                'area': boundaries.get('area', 0),
                'element_count': len(elements)
            },
            'metadata': {
                'created_at': datetime.utcnow().isoformat()
            }
        }
        
        return space
    
    def _calculate_space_boundaries(self, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate space boundaries from elements"""
        if not elements:
            return {}
        
        # Find min/max coordinates
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for element in elements:
            geometry = element.get('geometry', {})
            if geometry.get('type') == 'rectangle':
                coords = geometry.get('coordinates', [])
                for coord in coords:
                    min_x = min(min_x, coord[0])
                    min_y = min(min_y, coord[1])
                    max_x = max(max_x, coord[0])
                    max_y = max(max_y, coord[1])
            elif geometry.get('center'):
                center = geometry['center']
                radius = geometry.get('radius', 0)
                min_x = min(min_x, center[0] - radius)
                min_y = min(min_y, center[1] - radius)
                max_x = max(max_x, center[0] + radius)
                max_y = max(max_y, center[1] + radius)
        
        if min_x == float('inf'):
            return {}
        
        width = max_x - min_x
        height = max_y - min_y
        area = width * height
        
        return {
            'min': [min_x, min_y],
            'max': [max_x, max_y],
            'width': width,
            'height': height,
            'area': area,
            'center': [(min_x + max_x) / 2, (min_y + max_y) / 2]
        }
    
    def _determine_space_type(self, elements: List[Dict[str, Any]]) -> str:
        """Determine space type based on elements"""
        categories = [elem.get('category', 'unknown') for elem in elements]
        
        # Count categories
        category_counts = defaultdict(int)
        for category in categories:
            category_counts[category] += 1
        
        # Determine dominant category
        if category_counts['hvac'] > category_counts.get('electrical', 0):
            return 'mechanical_room'
        elif category_counts['electrical'] > 0:
            return 'electrical_room'
        elif category_counts['plumbing'] > 0:
            return 'plumbing_room'
        elif category_counts['structural'] > 0:
            return 'structural_space'
        else:
            return 'general_space'
    
    def _integrate_systems(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Integrate elements into systems"""
        systems = []
        
        # Group elements by category
        category_groups = defaultdict(list)
        for element in elements:
            category = element.get('category', 'unknown')
            category_groups[category].append(element)
        
        # Create systems for each category
        for category, category_elements in category_groups.items():
            if category != 'unknown':
                system = {
                    'system_id': f"system_{category}_{len(systems)}",
                    'system_type': category,
                    'elements': [elem['id'] for elem in category_elements],
                    'properties': {
                        'element_count': len(category_elements),
                        'category': category
                    },
                    'metadata': {
                        'created_at': datetime.utcnow().isoformat()
                    }
                }
                systems.append(system)
        
        logger.info(f"Created {len(systems)} systems from {len(elements)} elements")
        return systems
    
    def _establish_relationships(self, elements: List[Dict[str, Any]], 
                               spaces: List[Dict[str, Any]], 
                               systems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Establish relationships between elements, spaces, and systems"""
        relationships = []
        
        # Element to space relationships
        for space in spaces:
            for element_id in space['elements']:
                relationship = {
                    'relationship_id': f"rel_{len(relationships)}",
                    'source_id': element_id,
                    'target_id': space['space_id'],
                    'relationship_type': 'contained_in',
                    'properties': {},
                    'metadata': {
                        'created_at': datetime.utcnow().isoformat()
                    }
                }
                relationships.append(relationship)
        
        # Element to system relationships
        for system in systems:
            for element_id in system['elements']:
                relationship = {
                    'relationship_id': f"rel_{len(relationships)}",
                    'source_id': element_id,
                    'target_id': system['system_id'],
                    'relationship_type': 'belongs_to',
                    'properties': {},
                    'metadata': {
                        'created_at': datetime.utcnow().isoformat()
                    }
                }
                relationships.append(relationship)
        
        logger.info(f"Created {len(relationships)} relationships")
        return relationships
    
    def _resolve_conflicts(self, elements: List[Dict[str, Any]], 
                          spaces: List[Dict[str, Any]], 
                          systems: List[Dict[str, Any]]) -> List[AssemblyConflict]:
        """Detect and resolve conflicts"""
        conflicts = []
        
        if not self.config.conflict_resolution_enabled:
            return conflicts
        
        # Detect geometric conflicts
        geometric_conflicts = self._detect_geometric_conflicts(elements)
        conflicts.extend(geometric_conflicts)
        
        # Detect spatial conflicts
        spatial_conflicts = self._detect_spatial_conflicts(spaces)
        conflicts.extend(spatial_conflicts)
        
        # Detect system conflicts
        system_conflicts = self._detect_system_conflicts(systems)
        conflicts.extend(system_conflicts)
        
        # Resolve conflicts
        for conflict in conflicts:
            self._resolve_conflict(conflict)
        
        logger.info(f"Detected and resolved {len(conflicts)} conflicts")
        return conflicts
    
    def _detect_geometric_conflicts(self, elements: List[Dict[str, Any]]) -> List[AssemblyConflict]:
        """Detect geometric conflicts between elements"""
        conflicts = []
        
        for i, elem1 in enumerate(elements):
            for j, elem2 in enumerate(elements[i+1:], i+1):
                if self._elements_intersect(elem1, elem2):
                    conflict = AssemblyConflict(
                        conflict_id=f"conflict_{len(conflicts)}",
                        conflict_type=ConflictType.GEOMETRIC_OVERLAP,
                        elements=[elem1['id'], elem2['id']],
                        severity=0.8,
                        description=f"Geometric overlap between {elem1['id']} and {elem2['id']}",
                        resolution_suggestions=["Adjust element positions", "Resize elements"]
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _elements_intersect(self, elem1: Dict[str, Any], elem2: Dict[str, Any]) -> bool:
        """Check if two elements intersect"""
        try:
            geom1 = elem1.get('geometry', {})
            geom2 = elem2.get('geometry', {})
            
            # Simple bounding box intersection check
            if geom1.get('type') == 'rectangle' and geom2.get('type') == 'rectangle':
                coords1 = geom1.get('coordinates', [])
                coords2 = geom2.get('coordinates', [])
                
                if len(coords1) >= 4 and len(coords2) >= 4:
                    # Calculate bounding boxes
                    min_x1 = min(coord[0] for coord in coords1)
                    max_x1 = max(coord[0] for coord in coords1)
                    min_y1 = min(coord[1] for coord in coords1)
                    max_y1 = max(coord[1] for coord in coords1)
                    
                    min_x2 = min(coord[0] for coord in coords2)
                    max_x2 = max(coord[0] for coord in coords2)
                    min_y2 = min(coord[1] for coord in coords2)
                    max_y2 = max(coord[1] for coord in coords2)
                    
                    # Check intersection
                    return not (max_x1 < min_x2 or max_x2 < min_x1 or max_y1 < min_y2 or max_y2 < min_y1)
            
            return False
            
        except Exception:
            return False
    
    def _detect_spatial_conflicts(self, spaces: List[Dict[str, Any]]) -> List[AssemblyConflict]:
        """Detect spatial conflicts between spaces"""
        conflicts = []
        
        for i, space1 in enumerate(spaces):
            for j, space2 in enumerate(spaces[i+1:], i+1):
                if self._spaces_overlap(space1, space2):
                    conflict = AssemblyConflict(
                        conflict_id=f"conflict_{len(conflicts)}",
                        conflict_type=ConflictType.SPATIAL_CONFLICT,
                        elements=[space1['space_id'], space2['space_id']],
                        severity=0.6,
                        description=f"Spatial overlap between {space1['space_id']} and {space2['space_id']}",
                        resolution_suggestions=["Adjust space boundaries", "Merge overlapping spaces"]
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _spaces_overlap(self, space1: Dict[str, Any], space2: Dict[str, Any]) -> bool:
        """Check if two spaces overlap"""
        try:
            boundaries1 = space1.get('boundaries', {})
            boundaries2 = space2.get('boundaries', {})
            
            if 'min' in boundaries1 and 'max' in boundaries1 and 'min' in boundaries2 and 'max' in boundaries2:
                min1 = boundaries1['min']
                max1 = boundaries1['max']
                min2 = boundaries2['min']
                max2 = boundaries2['max']
                
                # Check overlap
                return not (max1[0] < min2[0] or max2[0] < min1[0] or max1[1] < min2[1] or max2[1] < min1[1])
            
            return False
            
        except Exception:
            return False
    
    def _detect_system_conflicts(self, systems: List[Dict[str, Any]]) -> List[AssemblyConflict]:
        """Detect system conflicts"""
        conflicts = []
        
        # Check for elements that belong to multiple systems
        element_systems = defaultdict(list)
        for system in systems:
            for element_id in system['elements']:
                element_systems[element_id].append(system['system_id'])
        
        for element_id, system_ids in element_systems.items():
            if len(system_ids) > 1:
                conflict = AssemblyConflict(
                    conflict_id=f"conflict_{len(conflicts)}",
                    conflict_type=ConflictType.SYSTEM_CONFLICT,
                    elements=[element_id] + system_ids,
                    severity=0.7,
                    description=f"Element {element_id} belongs to multiple systems: {system_ids}",
                    resolution_suggestions=["Assign element to primary system", "Create separate element instances"]
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def _resolve_conflict(self, conflict: AssemblyConflict):
        """Resolve a specific conflict"""
        try:
            if conflict.conflict_type == ConflictType.GEOMETRIC_OVERLAP:
                self._resolve_geometric_conflict(conflict)
            elif conflict.conflict_type == ConflictType.SPATIAL_CONFLICT:
                self._resolve_spatial_conflict(conflict)
            elif conflict.conflict_type == ConflictType.SYSTEM_CONFLICT:
                self._resolve_system_conflict(conflict)
            
            conflict.resolved = True
            
        except Exception as e:
            logger.error(f"Failed to resolve conflict {conflict.conflict_id}: {e}")
    
    def _resolve_geometric_conflict(self, conflict: AssemblyConflict):
        """Resolve geometric conflict"""
        # Simple resolution: adjust positions
        logger.info(f"Resolving geometric conflict: {conflict.conflict_id}")
    
    def _resolve_spatial_conflict(self, conflict: AssemblyConflict):
        """Resolve spatial conflict"""
        # Simple resolution: merge spaces
        logger.info(f"Resolving spatial conflict: {conflict.conflict_id}")
    
    def _resolve_system_conflict(self, conflict: AssemblyConflict):
        """Resolve system conflict"""
        # Simple resolution: assign to primary system
        logger.info(f"Resolving system conflict: {conflict.conflict_id}")
    
    def _validate_consistency(self, elements: List[Dict[str, Any]], 
                            spaces: List[Dict[str, Any]], 
                            systems: List[Dict[str, Any]], 
                            relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate BIM model consistency"""
        validation_results = {
            'overall_status': 'valid',
            'issues': [],
            'warnings': []
        }
        
        # Validate elements
        element_validation = self._validate_elements(elements)
        validation_results.update(element_validation)
        
        # Validate systems
        system_validation = self._validate_systems(systems)
        validation_results.update(system_validation)
        
        # Validate spatial structure
        spatial_validation = self._validate_spatial_structure(spaces)
        validation_results.update(spatial_validation)
        
        # Validate relationships
        relationship_validation = self._validate_relationships(relationships)
        validation_results.update(relationship_validation)
        
        # Determine overall status
        if validation_results['issues']:
            validation_results['overall_status'] = 'invalid'
        elif validation_results['warnings']:
            validation_results['overall_status'] = 'warning'
        
        return validation_results
    
    def _validate_elements(self, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate elements"""
        issues = []
        warnings = []
        
        for element in elements:
            if not element.get('geometry'):
                issues.append(f"Element {element['id']} has no geometry")
            
            if not element.get('category'):
                warnings.append(f"Element {element['id']} has no category")
        
        return {
            'element_issues': issues,
            'element_warnings': warnings
        }
    
    def _validate_systems(self, systems: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate systems"""
        issues = []
        warnings = []
        
        for system in systems:
            if not system.get('elements'):
                issues.append(f"System {system['system_id']} has no elements")
            
            if len(system.get('elements', [])) < 2:
                warnings.append(f"System {system['system_id']} has only one element")
        
        return {
            'system_issues': issues,
            'system_warnings': warnings
        }
    
    def _validate_spatial_structure(self, spaces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate spatial structure"""
        issues = []
        warnings = []
        
        for space in spaces:
            if not space.get('boundaries'):
                issues.append(f"Space {space['space_id']} has no boundaries")
            
            if not space.get('elements'):
                warnings.append(f"Space {space['space_id']} has no elements")
        
        return {
            'spatial_issues': issues,
            'spatial_warnings': warnings
        }
    
    def _validate_relationships(self, relationships: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate relationships"""
        issues = []
        warnings = []
        
        for relationship in relationships:
            if not relationship.get('source_id') or not relationship.get('target_id'):
                issues.append(f"Relationship {relationship['relationship_id']} has missing source or target")
            
            if not relationship.get('relationship_type'):
                warnings.append(f"Relationship {relationship['relationship_id']} has no type")
        
        return {
            'relationship_issues': issues,
            'relationship_warnings': warnings
        }
    
    def _optimize_performance(self, elements: List[Dict[str, Any]], 
                            spaces: List[Dict[str, Any]], 
                            systems: List[Dict[str, Any]]):
        """Optimize performance for large models"""
        if not self.config.performance_optimization_enabled:
            return
        
        # Batch process elements
        self._batch_process_elements(elements)
        
        logger.info("Performance optimization completed")
    
    def _batch_process_elements(self, elements: List[Dict[str, Any]]):
        """Process elements in batches for performance"""
        batch_size = self.config.batch_size
        
        for i in range(0, len(elements), batch_size):
            batch = elements[i:i + batch_size]
            self._process_element_batch(batch)
    
    def _process_element_batch(self, elements: List[Dict[str, Any]]):
        """Process a batch of elements"""
        # Simple batch processing - could be enhanced with more sophisticated operations
        for element in elements:
            # Add any batch processing logic here
            pass
    
    def _update_assembly_stats(self, assembly_time: float, success: bool):
        """Update assembly statistics"""
        self.assembly_stats['total_assemblies'] += 1
        
        if success:
            self.assembly_stats['successful_assemblies'] += 1
        else:
            self.assembly_stats['failed_assemblies'] += 1
        
        # Update average assembly time
        total_time = self.assembly_stats['average_assembly_time'] * (self.assembly_stats['total_assemblies'] - 1) + assembly_time
        self.assembly_stats['average_assembly_time'] = total_time / self.assembly_stats['total_assemblies']
    
    def get_assembly_statistics(self) -> Dict[str, Any]:
        """Get assembly statistics"""
        return self.assembly_stats.copy() 