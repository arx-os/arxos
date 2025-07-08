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

from services.enhanced_symbol_recognition import EnhancedSymbolRecognition, SymbolMatch
from services.geometry_resolver import GeometryResolver, GeometryProcessor, GeometryOptimizer
from services.bim_builder import BIMBuilder
from services.svg_bim_mapping import get_bim_class_for_svg
from models.enhanced_bim_elements import (
    EnhancedBIMModel, System, Connection, SystemType, ElementCategory,
    HVACElement, ElectricalElement, PlumbingElement, FireSafetyElement,
    SecurityElement, NetworkElement, StructuralElement, LightingElement,
    ConnectionType, create_element_id, create_system_id, create_connection_id
)
from models.bim import (
    BIMElementBase, BIMSystem, BIMRelationship,
    Room, Wall, Door, Window, Device, SystemType, DeviceCategory,
    HVACZone, AirHandler, VAVBox, ElectricalCircuit, ElectricalPanel, 
    ElectricalOutlet, PlumbingSystem, PlumbingFixture, Valve,
    FireAlarmSystem, SmokeDetector, SecuritySystem, Camera,
    Geometry, GeometryType
)
from services.json_symbol_library import JSONSymbolLibrary
from utils.errors import (
    BIMAssemblyError, GeometryError, RelationshipError, EnrichmentError, ValidationError, UnknownBIMTypeError
)


# Type alias for BIM elements
BIMElement = Union[
    Room, Wall, Door, Window, Device, HVACZone, AirHandler, VAVBox,
    ElectricalCircuit, ElectricalPanel, ElectricalOutlet, PlumbingSystem,
    PlumbingFixture, Valve, FireAlarmSystem, SmokeDetector, SecuritySystem, Camera
]

# BIM class mapping for instantiation
BIM_CLASS_MAP = {
    'Room': Room,
    'Wall': Wall,
    'Door': Door,
    'Window': Window,
    'Device': Device,
    'HVACZone': HVACZone,
    'AirHandler': AirHandler,
    'VAVBox': VAVBox,
    'ElectricalCircuit': ElectricalCircuit,
    'ElectricalPanel': ElectricalPanel,
    'ElectricalOutlet': ElectricalOutlet,
    'PlumbingSystem': PlumbingSystem,
    'PlumbingFixture': PlumbingFixture,
    'Valve': Valve,
    'FireAlarmSystem': FireAlarmSystem,
    'SmokeDetector': SmokeDetector,
    'SecuritySystem': SecuritySystem,
    'Camera': Camera
}

# BIMSpace class definition
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
    elements: List[BIMElement]
    systems: List[BIMSystem]
    spaces: List[BIMSpace]
    relationships: List[BIMRelationship]
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
    
    # Extract and convert dimensional properties
    if 'width' in svg_props:
        properties['width'] = float(svg_props['width']) * PX_TO_M
    if 'height' in svg_props:
        properties['height'] = float(svg_props['height']) * PX_TO_M
    if 'thickness' in svg_props:
        properties['thickness'] = float(svg_props['thickness']) * PX_TO_M
    
    # Extract position properties
    if 'x' in svg_props:
        properties['x'] = float(svg_props['x']) * PX_TO_M
    if 'y' in svg_props:
        properties['y'] = float(svg_props['y']) * PX_TO_M
    if 'z' in svg_props:
        properties['z'] = float(svg_props['z']) * PX_TO_M
    
    # Extract system-specific properties
    if 'system_type' in svg_props:
        properties['system_type'] = svg_props['system_type']
    if 'category' in svg_props:
        properties['category'] = svg_props['category']
    if 'manufacturer' in svg_props:
        properties['manufacturer'] = svg_props['manufacturer']
    if 'model' in svg_props:
        properties['model'] = svg_props['model']
    
    # Extract room-specific properties
    if 'room_type' in svg_props:
        properties['room_type'] = svg_props['room_type']
    if 'room_number' in svg_props:
        properties['room_number'] = svg_props['room_number']
    if 'area' in svg_props:
        # Convert area from px² to m²
        area_px = float(svg_props['area'])
        properties['area'] = area_px * (PX_TO_M ** 2)
    
    # Extract device-specific properties
    if 'voltage' in svg_props:
        properties['voltage'] = float(svg_props['voltage'])
    if 'amperage' in svg_props:
        properties['amperage'] = float(svg_props['amperage'])
    if 'capacity' in svg_props:
        properties['capacity'] = float(svg_props['capacity'])
    if 'flow_rate' in svg_props:
        properties['flow_rate'] = float(svg_props['flow_rate'])
    
    # Extract metadata
    if 'layer' in metadata:
        properties['layer'] = metadata['layer']
    if 'style' in metadata:
        properties['style'] = metadata['style']
    if 'visibility' in metadata:
        properties['visibility'] = metadata['visibility']
    
    return properties


def determine_device_category(svg_element: Dict[str, Any]) -> Optional[DeviceCategory]:
    """
    Determine the device category based on SVG element properties.
    """
    svg_type = svg_element.get('type', '').lower()
    layer = svg_element.get('metadata', {}).get('layer', '').lower()
    properties = svg_element.get('properties', {})
    
    # HVAC devices
    if 'ahu' in layer or 'air_handler' in layer:
        return DeviceCategory.AHU
    elif 'vav' in layer or 'vav_box' in layer:
        return DeviceCategory.VAV
    elif 'fcu' in layer or 'fan_coil' in layer:
        return DeviceCategory.FCU
    elif 'rtu' in layer or 'rooftop' in layer:
        return DeviceCategory.RTU
    elif 'chiller' in layer:
        return DeviceCategory.CHILLER
    elif 'boiler' in layer:
        return DeviceCategory.BOILER
    elif 'pump' in layer:
        return DeviceCategory.PUMP
    elif 'fan' in layer:
        return DeviceCategory.FAN
    elif 'damper' in layer:
        return DeviceCategory.DAMPER
    elif 'thermostat' in layer:
        return DeviceCategory.THERMOSTAT
    
    # Electrical devices
    elif 'panel' in layer or 'electrical_panel' in layer:
        return DeviceCategory.ELECTRICAL_PANEL
    elif 'outlet' in layer or 'receptacle' in layer:
        return DeviceCategory.ELECTRICAL_OUTLET
    elif 'switch' in layer:
        return DeviceCategory.ELECTRICAL_SWITCH
    elif 'light' in layer or 'lighting' in layer:
        return DeviceCategory.LIGHTING_FIXTURE
    elif 'transformer' in layer:
        return DeviceCategory.TRANSFORMER
    elif 'ups' in layer or 'uninterruptible' in layer:
        return DeviceCategory.UPS
    
    # Plumbing devices
    elif 'pipe' in layer:
        return DeviceCategory.PIPE
    elif 'valve' in layer:
        return DeviceCategory.VALVE
    elif 'fixture' in layer:
        return DeviceCategory.PLUMBING_FIXTURE
    elif 'pump' in layer:
        return DeviceCategory.PUMP
    elif 'tank' in layer:
        return DeviceCategory.TANK
    
    # Fire safety devices
    elif 'sprinkler' in layer:
        return DeviceCategory.SPRINKLER
    elif 'smoke_detector' in layer or 'smoke' in layer:
        return DeviceCategory.SMOKE_DETECTOR
    elif 'heat_detector' in layer or 'heat' in layer:
        return DeviceCategory.HEAT_DETECTOR
    elif 'pull_station' in layer or 'pull' in layer:
        return DeviceCategory.PULL_STATION
    elif 'horn' in layer or 'strobe' in layer:
        return DeviceCategory.HORN_STROBE
    
    # Security devices
    elif 'camera' in layer or 'cctv' in layer:
        return DeviceCategory.CAMERA
    elif 'access_control' in layer or 'card_reader' in layer:
        return DeviceCategory.ACCESS_CONTROL
    elif 'motion_detector' in layer or 'motion' in layer:
        return DeviceCategory.MOTION_DETECTOR
    elif 'door_contact' in layer:
        return DeviceCategory.DOOR_CONTACT
    
    # Network devices
    elif 'router' in layer:
        return DeviceCategory.ROUTER
    elif 'switch' in layer:
        return DeviceCategory.NETWORK_SWITCH
    elif 'access_point' in layer or 'ap' in layer:
        return DeviceCategory.ACCESS_POINT
    elif 'server' in layer:
        return DeviceCategory.SERVER
    
    return None


def create_geometry_from_svg(svg_element: Dict[str, Any]) -> Optional[Geometry]:
    """
    Create geometry object from SVG element data.
    """
    try:
        geometry_data = svg_element.get('geometry', {})
        if not geometry_data:
            return None
        
        geom_type = geometry_data.get('type', 'point')
        coordinates = geometry_data.get('coordinates', [])
        
        if geom_type == 'point':
            return Geometry(
                type=GeometryType.POINT,
                coordinates=coordinates,
                properties=geometry_data.get('properties', {}),
                bounding_box=geometry_data.get('bounding_box'),
                centroid=coordinates[0] if coordinates else None
            )
        elif geom_type == 'linestring':
            return Geometry(
                type=GeometryType.LINESTRING,
                coordinates=coordinates,
                properties=geometry_data.get('properties', {}),
                bounding_box=geometry_data.get('bounding_box'),
                centroid=geometry_data.get('centroid')
            )
        elif geom_type == 'polygon':
            return Geometry(
                type=GeometryType.POLYGON,
                coordinates=coordinates,
                properties=geometry_data.get('properties', {}),
                bounding_box=geometry_data.get('bounding_box'),
                centroid=geometry_data.get('centroid')
            )
        else:
            return None
            
    except Exception as e:
        logger.warning(f"Failed to create geometry from SVG element: {e}")
        return None


class EnhancedBIMAssembly:
    """
    Enhanced BIM assembly service with advanced symbol recognition and element creation.
    
    Features:
    - Multi-system BIM model creation
    - Advanced symbol recognition with ML
    - Automatic element classification
    - System relationship mapping
    - Comprehensive BIM data extraction
    - Multi-step BIM construction process
    - Conflict resolution for overlapping elements
    - BIM consistency validation
    - Performance optimization for large models
    - Assembly pipeline management
    """
    
    def __init__(self, symbol_library_path: Optional[str] = None, config: Optional[AssemblyConfig] = None):
        self.symbol_library = JSONSymbolLibrary(symbol_library_path)
        self.symbol_recognition = EnhancedSymbolRecognition(symbol_library_path)
        self.geometry_resolver = GeometryResolver()
        self.geometry_processor = GeometryProcessor()
        self.geometry_optimizer = GeometryOptimizer()
        self.bim_builder = BIMBuilder()
        self.logger = logging.getLogger(__name__)
        
        # Assembly configuration
        self.config = config or AssemblyConfig()
        
        # Assembly state
        self.assembly_id = None
        self.current_step = None
        self.elements: List[BIMElement] = []
        self.systems: List[BIMSystem] = []
        self.spaces: List[BIMSpace] = []
        self.relationships: List[BIMRelationship] = []
        self.conflicts: List[AssemblyConflict] = []
        self.performance_metrics: Dict[str, float] = {}
        
        # System templates for different building types
        self.system_templates = self._load_system_templates()
    
    def assemble_bim(self, svg_data: Dict[str, Any], 
                     metadata: Optional[Dict[str, Any]] = None) -> AssemblyResult:
        """
        Assemble BIM model from SVG data with enhanced pipeline.
        
        Args:
            svg_data: SVG data to process
            metadata: Optional metadata
            
        Returns:
            AssemblyResult with complete assembly information
        """
        start_time = time.time()
        self.assembly_id = f"bim_assembly_{int(start_time)}"
        
        try:
            self.logger.info(f"Starting BIM assembly: {self.assembly_id}")
            
            # Step 1: Geometry extraction
            self.current_step = AssemblyStep.GEOMETRY_EXTRACTION
            self.elements = self._extract_geometry(svg_data)
            self.logger.info(f"Extracted {len(self.elements)} elements")
            
            # Step 2: Element classification
            self.current_step = AssemblyStep.ELEMENT_CLASSIFICATION
            self._classify_elements()
            
            # Step 3: Spatial organization
            self.current_step = AssemblyStep.SPATIAL_ORGANIZATION
            self._organize_spatial_structure()
            
            # Step 4: System integration
            self.current_step = AssemblyStep.SYSTEM_INTEGRATION
            self._integrate_systems()
            
            # Step 5: Relationship establishment
            self.current_step = AssemblyStep.RELATIONSHIP_ESTABLISHMENT
            self._establish_relationships()
            
            # Step 6: Conflict resolution
            if self.config.conflict_resolution_enabled:
                self.current_step = AssemblyStep.CONFLICT_RESOLUTION
                self._resolve_conflicts()
            
            # Step 7: Consistency validation
            self.current_step = AssemblyStep.CONSISTENCY_VALIDATION
            validation_results = self._validate_consistency()
            
            # Step 8: Performance optimization
            if self.config.performance_optimization_enabled:
                self.current_step = AssemblyStep.PERFORMANCE_OPTIMIZATION
                self._optimize_performance()
            
            assembly_time = time.time() - start_time
            self.performance_metrics['assembly_time'] = assembly_time
            
            result = AssemblyResult(
                success=True,
                assembly_id=self.assembly_id,
                elements=self.elements,
                systems=self.systems,
                spaces=self.spaces,
                relationships=self.relationships,
                conflicts=self.conflicts,
                validation_results=validation_results,
                performance_metrics=self.performance_metrics,
                assembly_time=assembly_time
            )
            
            self.logger.info(f"BIM assembly completed successfully: {len(self.elements)} elements, {len(self.systems)} systems")
            return result
            
        except Exception as e:
            assembly_time = time.time() - start_time
            self.logger.error(f"BIM assembly failed: {e}")
            
            return AssemblyResult(
                success=False,
                assembly_id=self.assembly_id or f"failed_assembly_{int(time.time())}",
                elements=self.elements,
                systems=self.systems,
                spaces=self.spaces,
                relationships=self.relationships,
                conflicts=self.conflicts,
                validation_results={},
                performance_metrics={'assembly_time': assembly_time},
                assembly_time=assembly_time,
                warnings=[str(e)]
            )
    
    def _extract_geometry(self, svg_data: Dict[str, Any]) -> List[BIMElement]:
        """Extract geometry from SVG data."""
        svg_elements = svg_data.get('elements', [])
        
        if self.config.parallel_processing and len(svg_elements) > self.config.batch_size:
            return self._extract_geometry_parallel(svg_elements)
        else:
            return self._extract_geometry_sequential(svg_elements)
    
    def _extract_geometry_parallel(self, svg_elements: List[Dict[str, Any]]) -> List[BIMElement]:
        """Extract geometry using parallel processing."""
        elements = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Process elements in batches
            for i in range(0, len(svg_elements), self.config.batch_size):
                batch = svg_elements[i:i + self.config.batch_size]
                future_to_element = {
                    executor.submit(self._process_svg_element, element): element 
                    for element in batch
                }
                
                for future in as_completed(future_to_element):
                    element = future.result()
                    if element:
                        elements.append(element)
        
        return elements
    
    def _extract_geometry_sequential(self, svg_elements: List[Dict[str, Any]]) -> List[BIMElement]:
        """Extract geometry using sequential processing."""
        elements = []
        
        for svg_element in svg_elements:
            element = self._process_svg_element(svg_element)
            if element:
                elements.append(element)
        
        return elements
    
    def _process_svg_element(self, svg_element: Dict[str, Any]) -> Optional[BIMElement]:
        """Process a single SVG element into a BIM element."""
        try:
            # Extract properties
            properties = extract_and_convert_properties(svg_element)
            
            # Create geometry
            geometry = create_geometry_from_svg(svg_element)
            
            # Determine BIM class
            bim_class_name = self._determine_bim_class_from_symbol(
                svg_element.get('symbol_metadata', {}), 
                svg_element
            )
            
            if bim_class_name not in BIM_CLASS_MAP:
                self.logger.warning(f"Unknown BIM class: {bim_class_name}")
                return None
            
            bim_class = BIM_CLASS_MAP[bim_class_name]
            
            # Create BIM element
            element = bim_class(
                id=svg_element.get('id', f"element_{len(self.elements)}"),
                name=svg_element.get('name', f"{bim_class_name}_{len(self.elements)}"),
                element_type=bim_class_name.lower(),
                geometry=geometry,
                properties=properties,
                symbol_metadata=svg_element.get('symbol_metadata', {}),
                tags=svg_element.get('tags', []),
                status=svg_element.get('status', 'active')
            )
            
            return element
            
        except Exception as e:
            self.logger.error(f"Failed to process SVG element: {e}")
            return None
    
    def _determine_bim_class_from_symbol(self, symbol_metadata: dict, svg_element: dict) -> str:
        """Determine BIM class from symbol metadata."""
        symbol_name = symbol_metadata.get('symbol_name', '').lower()
        element_type = svg_element.get('type', '').lower()
        
        # Map symbol names to BIM classes
        symbol_to_bim_map = {
            'room': 'Room',
            'wall': 'Wall',
            'door': 'Door',
            'window': 'Window',
            'ahu': 'AirHandler',
            'vav': 'VAVBox',
            'panel': 'ElectricalPanel',
            'outlet': 'ElectricalOutlet',
            'pipe': 'PlumbingSystem',
            'valve': 'Valve',
            'sprinkler': 'FireAlarmSystem',
            'smoke_detector': 'SmokeDetector',
            'camera': 'Camera'
        }
        
        # Check symbol name first
        if symbol_name in symbol_to_bim_map:
            return symbol_to_bim_map[symbol_name]
        
        # Check element type
        if element_type in symbol_to_bim_map:
            return symbol_to_bim_map[element_type]
        
        # Default to Device for unknown types
        return 'Device'
    
    def _classify_elements(self):
        """Classify elements into categories."""
        for element in self.elements:
            category = self._determine_element_category(element)
            element.properties['category'] = category
    
    def _determine_element_category(self, element: BIMElement) -> str:
        """Determine the category of a BIM element."""
        element_type = element.element_type.lower()
        
        # Structural elements
        if element_type in ['wall', 'column', 'beam', 'slab']:
            return 'structural'
        
        # Enclosure elements
        elif element_type in ['door', 'window', 'curtain_wall']:
            return 'enclosure'
        
        # Space elements
        elif element_type in ['room', 'space', 'zone']:
            return 'space'
        
        # HVAC elements
        elif element_type in ['ahu', 'vav', 'fcu', 'rtu', 'chiller', 'boiler', 'pump', 'fan', 'damper', 'thermostat']:
            return 'hvac'
        
        # Electrical elements
        elif element_type in ['panel', 'outlet', 'switch', 'light', 'transformer', 'ups']:
            return 'electrical'
        
        # Plumbing elements
        elif element_type in ['pipe', 'valve', 'fixture', 'pump', 'tank']:
            return 'plumbing'
        
        # Fire safety elements
        elif element_type in ['sprinkler', 'smoke_detector', 'heat_detector', 'pull_station', 'horn_strobe']:
            return 'fire_safety'
        
        # Security elements
        elif element_type in ['camera', 'access_control', 'motion_detector', 'door_contact']:
            return 'security'
        
        # Network elements
        elif element_type in ['router', 'switch', 'access_point', 'server']:
            return 'network'
        
        # Lighting elements
        elif element_type in ['light', 'emergency_light', 'exit_sign']:
            return 'lighting'
        
        else:
            return 'other'
    
    def _organize_spatial_structure(self):
        """Organize elements into spatial structure."""
        # Group elements by proximity
        element_groups = self._group_elements_by_proximity()
        
        # Create spaces from element groups
        for group_id, elements in element_groups.items():
            space = self._create_space_from_elements(group_id, elements)
            self.spaces.append(space)
    
    def _group_elements_by_proximity(self) -> Dict[str, List[BIMElement]]:
        """Group elements by spatial proximity."""
        groups = {}
        processed_elements = set()
        
        for element in self.elements:
            if element.id in processed_elements:
                continue
            
            # Find nearby elements
            nearby_elements = self._find_nearby_elements(element, max_distance=10.0)
            
            # Create group
            group_id = f"space_{len(groups)}"
            groups[group_id] = [element] + nearby_elements
            
            # Mark as processed
            processed_elements.add(element.id)
            for nearby in nearby_elements:
                processed_elements.add(nearby.id)
        
        return groups
    
    def _find_nearby_elements(self, reference_element: BIMElement, 
                             max_distance: float) -> List[BIMElement]:
        """Find elements within a certain distance of the reference element."""
        nearby_elements = []
        
        for element in self.elements:
            if element.id == reference_element.id:
                continue
            
            distance = self._calculate_element_distance(reference_element, element)
            if distance <= max_distance:
                nearby_elements.append(element)
        
        return nearby_elements
    
    def _calculate_element_distance(self, elem1: BIMElement, elem2: BIMElement) -> float:
        """Calculate distance between two elements."""
        if not elem1.geometry or not elem2.geometry:
            return float('inf')
        
        # Use centroids for distance calculation
        centroid1 = elem1.geometry.centroid
        centroid2 = elem2.geometry.centroid
        
        if not centroid1 or not centroid2:
            return float('inf')
        
        # Calculate Euclidean distance
        if len(centroid1) >= 2 and len(centroid2) >= 2:
            dx = centroid1[0] - centroid2[0]
            dy = centroid1[1] - centroid2[1]
            return (dx**2 + dy**2)**0.5
        
        return float('inf')
    
    def _create_space_from_elements(self, space_id: str, 
                                   elements: List[BIMElement]) -> BIMSpace:
        """Create a space from a group of elements."""
        # Calculate space boundaries
        boundaries = self._calculate_space_boundaries(elements)
        
        # Determine space type
        space_type = self._determine_space_type(elements)
        
        # Create space
        space = BIMSpace(
            space_id=space_id,
            space_type=space_type,
            name=f"Space {space_id}",
            description=f"Space containing {len(elements)} elements",
            elements=[elem.id for elem in elements],
            boundaries=boundaries,
            properties={'element_count': len(elements)}
        )
        
        return space
    
    def _calculate_space_boundaries(self, elements: List[BIMElement]) -> Dict[str, Any]:
        """Calculate boundaries of a space from its elements."""
        if not elements:
            return {}
        
        all_coords = []
        
        for element in elements:
            if element.geometry and element.geometry.coordinates:
                if element.geometry.type == GeometryType.POINT:
                    all_coords.extend(element.geometry.coordinates)
                elif element.geometry.type == GeometryType.LINESTRING:
                    all_coords.extend(element.geometry.coordinates)
                elif element.geometry.type == GeometryType.POLYGON:
                    # Flatten polygon coordinates
                    for ring in element.geometry.coordinates:
                        all_coords.extend(ring)
        
        if not all_coords:
            return {}
        
        # Calculate bounding box
        x_coords = [coord[0] for coord in all_coords if len(coord) >= 1]
        y_coords = [coord[1] for coord in all_coords if len(coord) >= 2]
        
        if not x_coords or not y_coords:
            return {}
        
        boundaries = {
            'min': [min(x_coords), min(y_coords)],
            'max': [max(x_coords), max(y_coords)],
            'center': [(min(x_coords) + max(x_coords)) / 2, (min(y_coords) + max(y_coords)) / 2]
        }
        
        return boundaries
    
    def _determine_space_type(self, elements: List[BIMElement]) -> str:
        """Determine the type of space based on its elements."""
        element_types = [elem.element_type.lower() for elem in elements]
        
        # Count element types
        type_counts = {}
        for elem_type in element_types:
            type_counts[elem_type] = type_counts.get(elem_type, 0) + 1
        
        # Determine space type based on dominant elements
        if 'room' in type_counts and type_counts['room'] > 0:
            return 'room'
        elif 'wall' in type_counts and type_counts['wall'] > 2:
            return 'enclosed_space'
        elif 'door' in type_counts and 'window' in type_counts:
            return 'accessible_space'
        elif any(t in type_counts for t in ['ahu', 'vav', 'duct']):
            return 'mechanical_space'
        elif any(t in type_counts for t in ['panel', 'outlet', 'switch']):
            return 'electrical_space'
        else:
            return 'general_space'
    
    def _integrate_systems(self):
        """Integrate elements into systems."""
        # Group elements by system type
        system_groups = defaultdict(list)
        
        for element in self.elements:
            system_type = self._determine_system_type(element)
            system_groups[system_type].append(element)
        
        # Create systems
        for system_type, elements in system_groups.items():
            if elements:  # Only create systems with elements
                system = self._create_system(system_type, elements)
                self.systems.append(system)
    
    def _determine_system_type(self, element: BIMElement) -> str:
        """Determine the system type for an element."""
        category = element.properties.get('category', 'other')
        
        system_mapping = {
            'hvac': 'HVAC',
            'electrical': 'Electrical',
            'plumbing': 'Plumbing',
            'fire_safety': 'FireSafety',
            'security': 'Security',
            'network': 'Network',
            'lighting': 'Lighting',
            'structural': 'Structural'
        }
        
        return system_mapping.get(category, 'Other')
    
    def _create_system(self, system_type: str, elements: List[BIMElement]) -> BIMSystem:
        """Create a BIM system from elements."""
        system = BIMSystem(
            id=f"system_{len(self.systems)}",
            name=f"{system_type} System",
            system_type=system_type,
            description=f"{system_type} system with {len(elements)} elements",
            elements=elements,
            properties={'element_count': len(elements)}
        )
        
        return system
    
    def _establish_relationships(self):
        """Establish relationships between elements."""
        self._establish_spatial_relationships()
        self._establish_system_relationships()
        self._establish_dependency_relationships()
    
    def _establish_spatial_relationships(self):
        """Establish spatial relationships between elements."""
        for i, elem1 in enumerate(self.elements):
            for j, elem2 in enumerate(self.elements[i+1:], i+1):
                if self._elements_intersect(elem1, elem2):
                    relationship = BIMRelationship(
                        id=f"spatial_{elem1.id}_{elem2.id}",
                        source_id=elem1.id,
                        target_id=elem2.id,
                        relationship_type="spatial_intersection",
                        properties={'intersection_type': 'geometric'}
                    )
                    self.relationships.append(relationship)
    
    def _establish_system_relationships(self):
        """Establish relationships within systems."""
        for system in self.systems:
            elements = system.elements
            for i, elem1 in enumerate(elements):
                for j, elem2 in enumerate(elements[i+1:], i+1):
                    relationship = BIMRelationship(
                        id=f"system_{elem1.id}_{elem2.id}",
                        source_id=elem1.id,
                        target_id=elem2.id,
                        relationship_type="system_membership",
                        properties={'system_id': system.id, 'system_type': system.system_type}
                    )
                    self.relationships.append(relationship)
    
    def _establish_dependency_relationships(self):
        """Establish dependency relationships between elements."""
        for element in self.elements:
            dependencies = self._find_element_dependencies(element)
            for dep_id in dependencies:
                relationship = BIMRelationship(
                    id=f"dependency_{element.id}_{dep_id}",
                    source_id=element.id,
                    target_id=dep_id,
                    relationship_type="dependency",
                    properties={'dependency_type': 'functional'}
                )
                self.relationships.append(relationship)
    
    def _find_element_dependencies(self, element: BIMElement) -> List[str]:
        """Find dependencies for an element."""
        dependencies = []
        element_type = element.element_type.lower()
        
        # Define dependency rules
        dependency_rules = {
            'outlet': ['panel'],  # Outlets depend on panels
            'switch': ['panel'],   # Switches depend on panels
            'vav': ['ahu'],        # VAV boxes depend on AHUs
            'thermostat': ['ahu', 'vav'],  # Thermostats depend on HVAC equipment
            'sprinkler': ['pipe'], # Sprinklers depend on pipes
            'camera': ['panel'],   # Cameras depend on electrical panels
        }
        
        if element_type in dependency_rules:
            for dep_type in dependency_rules[element_type]:
                # Find elements of dependency type
                for other_element in self.elements:
                    if other_element.element_type.lower() == dep_type:
                        dependencies.append(other_element.id)
        
        return dependencies
    
    def _elements_intersect(self, elem1: BIMElement, elem2: BIMElement) -> bool:
        """Check if two elements intersect spatially."""
        if not elem1.geometry or not elem2.geometry:
            return False
        
        # Simple bounding box intersection check
        def get_bounds(coordinates):
            if not coordinates:
                return None
            
            x_coords = []
            y_coords = []
            
            for coord in coordinates:
                if len(coord) >= 1:
                    x_coords.append(coord[0])
                if len(coord) >= 2:
                    y_coords.append(coord[1])
            
            if not x_coords or not y_coords:
                return None
            
            return {
                'min_x': min(x_coords),
                'max_x': max(x_coords),
                'min_y': min(y_coords),
                'max_y': max(y_coords)
            }
        
        bounds1 = get_bounds(elem1.geometry.coordinates)
        bounds2 = get_bounds(elem2.geometry.coordinates)
        
        if not bounds1 or not bounds2:
            return False
        
        # Check for intersection
        return not (bounds1['max_x'] < bounds2['min_x'] or 
                   bounds2['max_x'] < bounds1['min_x'] or
                   bounds1['max_y'] < bounds2['min_y'] or
                   bounds2['max_y'] < bounds1['min_y'])
    
    def _resolve_conflicts(self):
        """Resolve conflicts in the BIM model."""
        self._detect_geometric_conflicts()
        self._detect_spatial_conflicts()
        self._detect_system_conflicts()
        
        # Resolve detected conflicts
        for conflict in self.conflicts:
            if conflict.severity > self.config.conflict_threshold:
                self._resolve_conflict(conflict)
    
    def _detect_geometric_conflicts(self):
        """Detect geometric conflicts between elements."""
        for i, elem1 in enumerate(self.elements):
            for j, elem2 in enumerate(self.elements[i+1:], i+1):
                if self._elements_intersect(elem1, elem2):
                    conflict = AssemblyConflict(
                        conflict_id=f"geometric_{elem1.id}_{elem2.id}",
                        conflict_type=ConflictType.GEOMETRIC_OVERLAP,
                        elements=[elem1.id, elem2.id],
                        severity=0.8,  # High severity for geometric conflicts
                        description=f"Geometric overlap between {elem1.name} and {elem2.name}",
                        location=elem1.geometry.centroid if elem1.geometry else None,
                        resolution_suggestions=[
                            "Adjust element positions",
                            "Modify element geometry",
                            "Add clearance zones"
                        ]
                    )
                    self.conflicts.append(conflict)
    
    def _detect_spatial_conflicts(self):
        """Detect spatial conflicts between spaces."""
        for i, space1 in enumerate(self.spaces):
            for j, space2 in enumerate(self.spaces[i+1:], i+1):
                if self._spaces_overlap(space1, space2):
                    conflict = AssemblyConflict(
                        conflict_id=f"spatial_{space1.space_id}_{space2.space_id}",
                        conflict_type=ConflictType.SPATIAL_CONFLICT,
                        elements=space1.elements + space2.elements,
                        severity=0.6,
                        description=f"Spatial overlap between {space1.name} and {space2.name}",
                        location=space1.boundaries.get('center') if space1.boundaries else None,
                        resolution_suggestions=[
                            "Adjust space boundaries",
                            "Merge overlapping spaces",
                            "Define clear spatial hierarchy"
                        ]
                    )
                    self.conflicts.append(conflict)
    
    def _spaces_overlap(self, space1: BIMSpace, space2: BIMSpace) -> bool:
        """Check if two spaces overlap."""
        bounds1 = space1.boundaries
        bounds2 = space2.boundaries
        
        if not bounds1 or not bounds2:
            return False
        
        min1 = bounds1.get('min', [])
        max1 = bounds1.get('max', [])
        min2 = bounds2.get('min', [])
        max2 = bounds2.get('max', [])
        
        if len(min1) < 2 or len(max1) < 2 or len(min2) < 2 or len(max2) < 2:
            return False
        
        return not (max1[0] < min2[0] or max2[0] < min1[0] or
                   max1[1] < min2[1] or max2[1] < min1[1])
    
    def _detect_system_conflicts(self):
        """Detect conflicts within systems."""
        for system in self.systems:
            # Check for incompatible elements in the same system
            element_types = [elem.element_type for elem in system.elements]
            if len(set(element_types)) > 5:  # Too many different element types
                conflict = AssemblyConflict(
                    conflict_id=f"system_{system.id}",
                    conflict_type=ConflictType.SYSTEM_CONFLICT,
                    elements=[elem.id for elem in system.elements],
                    severity=0.4,
                    description=f"System {system.name} contains too many element types",
                    resolution_suggestions=[
                        "Split system into subsystems",
                        "Reclassify elements",
                        "Review system boundaries"
                    ]
                )
                self.conflicts.append(conflict)
    
    def _resolve_conflict(self, conflict: AssemblyConflict):
        """Resolve a specific conflict."""
        if conflict.conflict_type == ConflictType.GEOMETRIC_OVERLAP:
            self._resolve_geometric_conflict(conflict)
        elif conflict.conflict_type == ConflictType.SPATIAL_CONFLICT:
            self._resolve_spatial_conflict(conflict)
        elif conflict.conflict_type == ConflictType.SYSTEM_CONFLICT:
            self._resolve_system_conflict(conflict)
        
        conflict.resolved = True
    
    def _resolve_geometric_conflict(self, conflict: AssemblyConflict):
        """Resolve geometric conflict by adjusting element positions."""
        if len(conflict.elements) >= 2:
            # Simple resolution: move second element slightly
            elem1_id, elem2_id = conflict.elements[0], conflict.elements[1]
            elem1 = next((e for e in self.elements if e.id == elem1_id), None)
            elem2 = next((e for e in self.elements if e.id == elem2_id), None)
            
            if elem1 and elem2 and elem1.geometry and elem2.geometry:
                # Move elem2 by a small offset
                offset = 0.1  # 10cm offset
                if elem2.geometry.centroid and elem1.geometry.centroid:
                    new_centroid = [
                        elem2.geometry.centroid[0] + offset,
                        elem2.geometry.centroid[1] + offset
                    ]
                    elem2.geometry.centroid = new_centroid
    
    def _resolve_spatial_conflict(self, conflict: AssemblyConflict):
        """Resolve spatial conflict by adjusting space boundaries."""
        # Implementation would adjust space boundaries
        pass
    
    def _resolve_system_conflict(self, conflict: AssemblyConflict):
        """Resolve system conflict by splitting the system."""
        # Implementation would split the system into subsystems
        pass
    
    def _validate_consistency(self) -> Dict[str, Any]:
        """Validate the consistency of the BIM model."""
        validation_results = {
            'elements': self._validate_elements(),
            'systems': self._validate_systems(),
            'spatial_structure': self._validate_spatial_structure(),
            'relationships': self._validate_relationships(),
            'geometries': self._validate_geometries()
        }
        
        return validation_results
    
    def _validate_elements(self) -> Dict[str, Any]:
        """Validate BIM elements."""
        validation = {
            'total_elements': len(self.elements),
            'valid_elements': 0,
            'invalid_elements': 0,
            'errors': []
        }
        
        for element in self.elements:
            if element.id and element.name and element.element_type:
                validation['valid_elements'] += 1
            else:
                validation['invalid_elements'] += 1
                validation['errors'].append(f"Invalid element: {element.id}")
        
        return validation
    
    def _validate_systems(self) -> Dict[str, Any]:
        """Validate BIM systems."""
        validation = {
            'total_systems': len(self.systems),
            'valid_systems': 0,
            'invalid_systems': 0,
            'errors': []
        }
        
        for system in self.systems:
            if system.id and system.name and system.elements:
                validation['valid_systems'] += 1
            else:
                validation['invalid_systems'] += 1
                validation['errors'].append(f"Invalid system: {system.id}")
        
        return validation
    
    def _validate_spatial_structure(self) -> Dict[str, Any]:
        """Validate spatial structure."""
        validation = {
            'total_spaces': len(self.spaces),
            'valid_spaces': 0,
            'invalid_spaces': 0,
            'errors': []
        }
        
        for space in self.spaces:
            if space.space_id and space.elements:
                validation['valid_spaces'] += 1
            else:
                validation['invalid_spaces'] += 1
                validation['errors'].append(f"Invalid space: {space.space_id}")
        
        return validation
    
    def _validate_relationships(self) -> Dict[str, Any]:
        """Validate relationships."""
        validation = {
            'total_relationships': len(self.relationships),
            'valid_relationships': 0,
            'invalid_relationships': 0,
            'errors': []
        }
        
        for relationship in self.relationships:
            if relationship.id and relationship.source_id and relationship.target_id:
                validation['valid_relationships'] += 1
            else:
                validation['invalid_relationships'] += 1
                validation['errors'].append(f"Invalid relationship: {relationship.id}")
        
        return validation
    
    def _validate_geometries(self) -> Dict[str, Any]:
        """Validate geometries."""
        validation = {
            'total_geometries': 0,
            'valid_geometries': 0,
            'invalid_geometries': 0,
            'errors': []
        }
        
        for element in self.elements:
            if element.geometry:
                validation['total_geometries'] += 1
                if element.geometry.coordinates:
                    validation['valid_geometries'] += 1
                else:
                    validation['invalid_geometries'] += 1
                    validation['errors'].append(f"Invalid geometry for element: {element.id}")
        
        return validation
    
    def _optimize_performance(self):
        """Optimize performance of the BIM model."""
        # Batch process elements
        self._batch_process_elements()
        
        # Optimize geometries
        for element in self.elements:
            if element.geometry:
                element.geometry = self.geometry_optimizer.optimize_geometry(element.geometry)
        
        # Update performance metrics
        self.performance_metrics['total_elements'] = len(self.elements)
        self.performance_metrics['total_systems'] = len(self.systems)
        self.performance_metrics['total_spaces'] = len(self.spaces)
        self.performance_metrics['total_relationships'] = len(self.relationships)
    
    def _batch_process_elements(self):
        """Process elements in batches for performance optimization."""
        if len(self.elements) <= self.config.batch_size:
            return
        
        # Process elements in batches
        for i in range(0, len(self.elements), self.config.batch_size):
            batch = self.elements[i:i + self.config.batch_size]
            self._process_element_batch(batch)
    
    def _process_element_batch(self, elements: List[BIMElement]):
        """Process a batch of elements."""
        for element in elements:
            # Optimize element properties
            if element.properties:
                # Remove redundant properties
                element.properties = {k: v for k, v in element.properties.items() if v is not None}
            
            # Optimize geometry if present
            if element.geometry:
                element.geometry = self.geometry_processor.process_geometry(element.geometry)
    
    def _load_system_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load system templates for different building types."""
        return {
            "office": {
                "hvac": ["air_handler", "vav_box", "duct", "diffuser", "thermostat"],
                "electrical": ["panel", "circuit", "outlet", "switch", "lighting_fixture"],
                "plumbing": ["pipe", "valve", "fixture", "drain"],
                "fire_safety": ["sprinkler", "smoke_detector", "pull_station", "horn_strobe"],
                "security": ["camera", "access_control", "motion_detector"],
                "network": ["router", "switch", "access_point", "cable"],
                "lighting": ["light", "emergency_light", "exit_sign"]
            },
            "residential": {
                "hvac": ["air_handler", "duct", "diffuser", "thermostat"],
                "electrical": ["panel", "circuit", "outlet", "switch", "lighting_fixture"],
                "plumbing": ["pipe", "valve", "fixture", "drain"],
                "fire_safety": ["smoke_detector", "pull_station"],
                "security": ["camera", "motion_detector"],
                "network": ["router", "access_point", "cable"],
                "lighting": ["light", "emergency_light"]
            },
            "industrial": {
                "hvac": ["air_handler", "duct", "diffuser", "thermostat", "chiller", "boiler"],
                "electrical": ["panel", "circuit", "outlet", "switch", "transformer", "ups"],
                "plumbing": ["pipe", "valve", "pump", "tank", "fixture"],
                "fire_safety": ["sprinkler", "smoke_detector", "heat_detector", "pull_station"],
                "security": ["camera", "access_control", "motion_detector"],
                "network": ["router", "switch", "server", "cable"],
                "lighting": ["light", "emergency_light", "exit_sign"]
            }
        }
    
    def assemble_enhanced_bim(self, svg_content: str, options: Optional[Dict[str, Any]] = None) -> EnhancedBIMModel:
        """
        Assemble an enhanced BIM model from SVG content.
        
        Args:
            svg_content: SVG content to parse
            options: Assembly options
            
        Returns:
            Enhanced BIM model with multiple systems
        """
        try:
            options = options or {}
            building_type = options.get("building_type", "office")
            
            # Create base model
            model = EnhancedBIMModel(
                id=create_element_id(),
                name=options.get("name", "Enhanced BIM Model"),
                description=options.get("description", "Generated from SVG content"),
                properties=options.get("properties", {}),
                metadata=options.get("metadata", {})
            )
            
            # Recognize symbols
            symbol_matches = self.symbol_recognition.recognize_symbols(svg_content, options)
            self.logger.info(f"Recognized {len(symbol_matches)} symbols")
            
            # Create systems based on building type
            systems = self._create_systems_for_building_type(building_type, symbol_matches)
            
            # Add systems to model
            for system in systems:
                model.add_system(system)
            
            # Create elements from symbol matches
            elements = self._create_elements_from_symbols(symbol_matches, systems)
            
            # Add elements to model
            for element in elements:
                self._add_element_to_model(model, element)
            
            # Create connections between elements
            connections = self._create_connections(elements, symbol_matches)
            
            # Add connections to model
            for connection in connections:
                model.add_connection(connection)
            
            # Resolve geometry and spatial relationships
            self._resolve_geometry_and_spatial_relationships(model)
            
            self.logger.info(f"Enhanced BIM assembly completed: {model.get_statistics()}")
            return model
            
        except Exception as e:
            self.logger.error(f"Enhanced BIM assembly failed: {e}")
            raise
    
    def _create_systems_for_building_type(self, building_type: str, 
                                        symbol_matches: List[SymbolMatch]) -> List[System]:
        """Create systems based on building type and recognized symbols."""
        systems = []
        
        try:
            template = self.system_templates.get(building_type, self.system_templates["office"])
            
            # Create HVAC system
            hvac_system = System(
                id=create_system_id(),
                name="HVAC System",
                system_type=SystemType.HVAC,
                description="Heating, Ventilation, and Air Conditioning system",
                properties={"building_type": building_type}
            )
            systems.append(hvac_system)
            
            # Create Electrical system
            electrical_system = System(
                id=create_system_id(),
                name="Electrical System",
                system_type=SystemType.ELECTRICAL,
                description="Electrical power and distribution system",
                properties={"building_type": building_type}
            )
            systems.append(electrical_system)
            
            # Create Plumbing system
            plumbing_system = System(
                id=create_system_id(),
                name="Plumbing System",
                system_type=SystemType.PLUMBING,
                description="Water supply and drainage system",
                properties={"building_type": building_type}
            )
            systems.append(plumbing_system)
            
            # Create Fire Safety system
            fire_safety_system = System(
                id=create_system_id(),
                name="Fire Safety System",
                system_type=SystemType.FIRE_SAFETY,
                description="Fire detection and suppression system",
                properties={"building_type": building_type}
            )
            systems.append(fire_safety_system)
            
            # Create Security system
            security_system = System(
                id=create_system_id(),
                name="Security System",
                system_type=SystemType.SECURITY,
                description="Building security and access control system",
                properties={"building_type": building_type}
            )
            systems.append(security_system)
            
            # Create Network system
            network_system = System(
                id=create_system_id(),
                name="Network System",
                system_type=SystemType.NETWORK,
                description="IT and communication network system",
                properties={"building_type": building_type}
            )
            systems.append(network_system)
            
            # Create Lighting system
            lighting_system = System(
                id=create_system_id(),
                name="Lighting System",
                system_type=SystemType.LIGHTING,
                description="Building lighting and emergency lighting system",
                properties={"building_type": building_type}
            )
            systems.append(lighting_system)
            
        except Exception as e:
            self.logger.error(f"System creation failed: {e}")
        
        return systems
    
    def _create_elements_from_symbols(self, symbol_matches: List[SymbolMatch], 
                                    systems: List[System]) -> List[Any]:
        """Create BIM elements from recognized symbols."""
        elements = []
        
        try:
            # Group systems by type
            system_map = {system.system_type: system for system in systems}
            
            for match in symbol_matches:
                element = self._create_element_from_symbol(match, system_map)
                if element:
                    elements.append(element)
            
        except Exception as e:
            self.logger.error(f"Element creation failed: {e}")
        
        return elements
    
    def _create_element_from_symbol(self, symbol_match: SymbolMatch, 
                                  system_map: Dict[SystemType, System]) -> Optional[Any]:
        """Create a BIM element from a symbol match, mapping properties and connections."""
        try:
            symbol_type = symbol_match.symbol_type
            system = system_map.get(symbol_type)
            if not system:
                return None
            # Extract symbol properties and connections
            symbol_properties = symbol_match.symbol_metadata.get("properties", {})
            symbol_connections = symbol_match.symbol_metadata.get("connections", [])
            # Merge features and properties
            merged_properties = dict(symbol_match.features)
            merged_properties.update(symbol_properties)
            # Pass connections as a separate field if supported
            element = None
            if symbol_type == SystemType.HVAC:
                element = self._create_hvac_element(symbol_match, system, merged_properties, symbol_connections)
            elif symbol_type == SystemType.ELECTRICAL:
                element = self._create_electrical_element(symbol_match, system, merged_properties, symbol_connections)
            elif symbol_type == SystemType.PLUMBING:
                element = self._create_plumbing_element(symbol_match, system, merged_properties, symbol_connections)
            elif symbol_type == SystemType.FIRE_SAFETY:
                element = self._create_fire_safety_element(symbol_match, system, merged_properties, symbol_connections)
            elif symbol_type == SystemType.SECURITY:
                element = self._create_security_element(symbol_match, system, merged_properties, symbol_connections)
            elif symbol_type == SystemType.NETWORK:
                element = self._create_network_element(symbol_match, system, merged_properties, symbol_connections)
            elif symbol_type == SystemType.LIGHTING:
                element = self._create_lighting_element(symbol_match, system, merged_properties, symbol_connections)
            else:
                element = self._create_structural_element(symbol_match, system, merged_properties, symbol_connections)
            return element
        except Exception as e:
            self.logger.error(f"Element creation from symbol failed: {e}")
            return None

    def _create_hvac_element(self, symbol_match: SymbolMatch, system: System, properties: dict, connections: list) -> HVACElement:
        bounds = symbol_match.bounding_box
        location = {"x": bounds[0], "y": bounds[1], "z": 0}
        dimensions = {"width": bounds[2] - bounds[0], "height": bounds[3] - bounds[1], "depth": 0}
        category = self._determine_hvac_category(symbol_match.symbol_name)
        return HVACElement(
            id=create_element_id(),
            name=symbol_match.symbol_name,
            category=category,
            system_id=system.id,
            location=location,
            dimensions=dimensions,
            properties=properties,
            connections=connections,
            metadata=symbol_match.symbol_metadata
        )
    # Repeat for other element types:
    def _create_electrical_element(self, symbol_match: SymbolMatch, system: System, properties: dict, connections: list) -> ElectricalElement:
        bounds = symbol_match.bounding_box
        location = {"x": bounds[0], "y": bounds[1], "z": 0}
        dimensions = {"width": bounds[2] - bounds[0], "height": bounds[3] - bounds[1], "depth": 0}
        category = self._determine_electrical_category(symbol_match.symbol_name)
        return ElectricalElement(
            id=create_element_id(),
            name=symbol_match.symbol_name,
            category=category,
            system_id=system.id,
            location=location,
            dimensions=dimensions,
            properties=properties,
            connections=connections,
            metadata=symbol_match.symbol_metadata
        )
    def _create_plumbing_element(self, symbol_match: SymbolMatch, system: System, properties: dict, connections: list) -> PlumbingElement:
        bounds = symbol_match.bounding_box
        location = {"x": bounds[0], "y": bounds[1], "z": 0}
        dimensions = {"width": bounds[2] - bounds[0], "height": bounds[3] - bounds[1], "depth": 0}
        category = self._determine_plumbing_category(symbol_match.symbol_name)
        return PlumbingElement(
            id=create_element_id(),
            name=symbol_match.symbol_name,
            category=category,
            system_id=system.id,
            location=location,
            dimensions=dimensions,
            properties=properties,
            connections=connections,
            metadata=symbol_match.symbol_metadata
        )
    def _create_fire_safety_element(self, symbol_match: SymbolMatch, system: System, properties: dict, connections: list) -> FireSafetyElement:
        bounds = symbol_match.bounding_box
        location = {"x": bounds[0], "y": bounds[1], "z": 0}
        dimensions = {"width": bounds[2] - bounds[0], "height": bounds[3] - bounds[1], "depth": 0}
        category = self._determine_fire_safety_category(symbol_match.symbol_name)
        return FireSafetyElement(
            id=create_element_id(),
            name=symbol_match.symbol_name,
            category=category,
            system_id=system.id,
            location=location,
            dimensions=dimensions,
            properties=properties,
            connections=connections,
            metadata=symbol_match.symbol_metadata
        )
    def _create_security_element(self, symbol_match: SymbolMatch, system: System, properties: dict, connections: list) -> SecurityElement:
        bounds = symbol_match.bounding_box
        location = {"x": bounds[0], "y": bounds[1], "z": 0}
        dimensions = {"width": bounds[2] - bounds[0], "height": bounds[3] - bounds[1], "depth": 0}
        category = self._determine_security_category(symbol_match.symbol_name)
        return SecurityElement(
            id=create_element_id(),
            name=symbol_match.symbol_name,
            category=category,
            system_id=system.id,
            location=location,
            dimensions=dimensions,
            properties=properties,
            connections=connections,
            metadata=symbol_match.symbol_metadata
        )
    def _create_network_element(self, symbol_match: SymbolMatch, system: System, properties: dict, connections: list) -> NetworkElement:
        bounds = symbol_match.bounding_box
        location = {"x": bounds[0], "y": bounds[1], "z": 0}
        dimensions = {"width": bounds[2] - bounds[0], "height": bounds[3] - bounds[1], "depth": 0}
        category = self._determine_network_category(symbol_match.symbol_name)
        return NetworkElement(
            id=create_element_id(),
            name=symbol_match.symbol_name,
            category=category,
            system_id=system.id,
            location=location,
            dimensions=dimensions,
            properties=properties,
            connections=connections,
            metadata=symbol_match.symbol_metadata
        )
    def _create_lighting_element(self, symbol_match: SymbolMatch, system: System, properties: dict, connections: list) -> LightingElement:
        bounds = symbol_match.bounding_box
        location = {"x": bounds[0], "y": bounds[1], "z": 0}
        dimensions = {"width": bounds[2] - bounds[0], "height": bounds[3] - bounds[1], "depth": 0}
        category = self._determine_lighting_category(symbol_match.symbol_name)
        return LightingElement(
            id=create_element_id(),
            name=symbol_match.symbol_name,
            category=category,
            system_id=system.id,
            location=location,
            dimensions=dimensions,
            properties=properties,
            connections=connections,
            metadata=symbol_match.symbol_metadata
        )
    def _create_structural_element(self, symbol_match: SymbolMatch, system: System, properties: dict, connections: list) -> StructuralElement:
        bounds = symbol_match.bounding_box
        location = {"x": bounds[0], "y": bounds[1], "z": 0}
        dimensions = {"width": bounds[2] - bounds[0], "height": bounds[3] - bounds[1], "depth": 0}
        category = self._determine_structural_category(symbol_match.symbol_name)
        return StructuralElement(
            id=create_element_id(),
            name=symbol_match.symbol_name,
            category=category,
            system_id=system.id,
            location=location,
            dimensions=dimensions,
            properties=properties,
            connections=connections,
            metadata=symbol_match.symbol_metadata
        )
    
    def _determine_hvac_category(self, symbol_name: str) -> ElementCategory:
        """Determine HVAC element category from symbol name."""
        name_lower = symbol_name.lower()
        
        if "air" in name_lower and "handler" in name_lower:
            return ElementCategory.AIR_HANDLER
        elif "vav" in name_lower:
            return ElementCategory.VAV_BOX
        elif "duct" in name_lower:
            return ElementCategory.DUCT
        elif "diffuser" in name_lower:
            return ElementCategory.DIFFUSER
        elif "thermostat" in name_lower:
            return ElementCategory.THERMOSTAT
        elif "chiller" in name_lower:
            return ElementCategory.CHILLER
        elif "boiler" in name_lower:
            return ElementCategory.BOILER
        elif "cooling" in name_lower and "tower" in name_lower:
            return ElementCategory.COOLING_TOWER
        elif "heat" in name_lower and "exchanger" in name_lower:
            return ElementCategory.HEAT_EXCHANGER
        else:
            return ElementCategory.AIR_HANDLER
    
    def _determine_electrical_category(self, symbol_name: str) -> ElementCategory:
        """Determine electrical element category from symbol name."""
        name_lower = symbol_name.lower()
        
        if "panel" in name_lower:
            return ElementCategory.PANEL
        elif "circuit" in name_lower:
            return ElementCategory.CIRCUIT
        elif "outlet" in name_lower:
            return ElementCategory.OUTLET
        elif "switch" in name_lower:
            return ElementCategory.SWITCH
        elif "light" in name_lower:
            return ElementCategory.LIGHTING_FIXTURE
        elif "transformer" in name_lower:
            return ElementCategory.TRANSFORMER
        elif "generator" in name_lower:
            return ElementCategory.GENERATOR
        elif "ups" in name_lower:
            return ElementCategory.UPS
        else:
            return ElementCategory.OUTLET
    
    def _determine_plumbing_category(self, symbol_name: str) -> ElementCategory:
        """Determine plumbing element category from symbol name."""
        name_lower = symbol_name.lower()
        
        if "pipe" in name_lower:
            return ElementCategory.PIPE
        elif "valve" in name_lower:
            return ElementCategory.VALVE
        elif "pump" in name_lower:
            return ElementCategory.PUMP
        elif "tank" in name_lower:
            return ElementCategory.TANK
        elif "fixture" in name_lower:
            return ElementCategory.FIXTURE
        elif "drain" in name_lower:
            return ElementCategory.DRAIN
        elif "vent" in name_lower:
            return ElementCategory.VENT
        else:
            return ElementCategory.PIPE
    
    def _determine_fire_safety_category(self, symbol_name: str) -> ElementCategory:
        """Determine fire safety element category from symbol name."""
        name_lower = symbol_name.lower()
        
        if "sprinkler" in name_lower:
            return ElementCategory.SPRINKLER
        elif "smoke" in name_lower and "detector" in name_lower:
            return ElementCategory.SMOKE_DETECTOR
        elif "heat" in name_lower and "detector" in name_lower:
            return ElementCategory.HEAT_DETECTOR
        elif "pull" in name_lower and "station" in name_lower:
            return ElementCategory.PULL_STATION
        elif "horn" in name_lower and "strobe" in name_lower:
            return ElementCategory.HORN_STROBE
        elif "fire" in name_lower and "damper" in name_lower:
            return ElementCategory.FIRE_DAMPER
        else:
            return ElementCategory.SMOKE_DETECTOR
    
    def _determine_security_category(self, symbol_name: str) -> ElementCategory:
        """Determine security element category from symbol name."""
        name_lower = symbol_name.lower()
        
        if "camera" in name_lower:
            return ElementCategory.CAMERA
        elif "access" in name_lower and "control" in name_lower:
            return ElementCategory.ACCESS_CONTROL
        elif "motion" in name_lower and "detector" in name_lower:
            return ElementCategory.MOTION_DETECTOR
        elif "door" in name_lower and "contact" in name_lower:
            return ElementCategory.DOOR_CONTACT
        elif "glass" in name_lower and "break" in name_lower:
            return ElementCategory.GLASS_BREAK
        elif "card" in name_lower and "reader" in name_lower:
            return ElementCategory.CARD_READER
        else:
            return ElementCategory.CAMERA
    
    def _determine_network_category(self, symbol_name: str) -> ElementCategory:
        """Determine network element category from symbol name."""
        name_lower = symbol_name.lower()
        
        if "router" in name_lower:
            return ElementCategory.ROUTER
        elif "switch" in name_lower:
            return ElementCategory.SWITCH
        elif "server" in name_lower:
            return ElementCategory.SERVER
        elif "access" in name_lower and "point" in name_lower:
            return ElementCategory.ACCESS_POINT
        elif "cable" in name_lower:
            return ElementCategory.CABLE
        elif "patch" in name_lower and "panel" in name_lower:
            return ElementCategory.PATCH_PANEL
        else:
            return ElementCategory.SWITCH
    
    def _determine_lighting_category(self, symbol_name: str) -> ElementCategory:
        """Determine lighting element category from symbol name."""
        name_lower = symbol_name.lower()
        
        if "light" in name_lower and "emergency" in name_lower:
            return ElementCategory.EMERGENCY_LIGHT
        elif "exit" in name_lower and "sign" in name_lower:
            return ElementCategory.EXIT_SIGN
        elif "dimmer" in name_lower:
            return ElementCategory.DIMMER
        elif "sensor" in name_lower:
            return ElementCategory.SENSOR
        else:
            return ElementCategory.LIGHT
    
    def _determine_structural_category(self, symbol_name: str) -> ElementCategory:
        """Determine structural element category from symbol name."""
        name_lower = symbol_name.lower()
        
        if "wall" in name_lower:
            return ElementCategory.WALL
        elif "column" in name_lower:
            return ElementCategory.COLUMN
        elif "beam" in name_lower:
            return ElementCategory.BEAM
        elif "slab" in name_lower:
            return ElementCategory.SLAB
        elif "foundation" in name_lower:
            return ElementCategory.FOUNDATION
        elif "roof" in name_lower:
            return ElementCategory.ROOF
        else:
            return ElementCategory.WALL
    
    def _add_element_to_model(self, model: EnhancedBIMModel, element: Any) -> bool:
        """Add an element to the appropriate collection in the model."""
        try:
            if isinstance(element, HVACElement):
                return model.add_hvac_element(element)
            elif isinstance(element, ElectricalElement):
                return model.add_electrical_element(element)
            elif isinstance(element, PlumbingElement):
                return model.add_plumbing_element(element)
            elif isinstance(element, FireSafetyElement):
                return model.add_fire_safety_element(element)
            elif isinstance(element, SecurityElement):
                return model.add_security_element(element)
            elif isinstance(element, NetworkElement):
                return model.add_network_element(element)
            elif isinstance(element, StructuralElement):
                return model.add_structural_element(element)
            elif isinstance(element, LightingElement):
                return model.add_lighting_element(element)
            else:
                return False
        except Exception as e:
            self.logger.error(f"Failed to add element to model: {e}")
            return False
    
    def _create_connections(self, elements: List[Any], symbol_matches: List[SymbolMatch]) -> List[Connection]:
        """Create connections between elements based on spatial relationships."""
        connections = []
        
        try:
            # Create connections based on proximity and system relationships
            for i, element1 in enumerate(elements):
                for j, element2 in enumerate(elements):
                    if i != j and element1.system_id == element2.system_id:
                        # Check if elements should be connected
                        if self._should_connect_elements(element1, element2):
                            connection = Connection(
                                id=create_connection_id(),
                                source_element_id=element1.id,
                                target_element_id=element2.id,
                                connection_type=self._determine_connection_type(element1, element2),
                                properties={"distance": self._calculate_distance(element1, element2)},
                                metadata={"created_by": "enhanced_assembly"}
                            )
                            connections.append(connection)
            
        except Exception as e:
            self.logger.error(f"Connection creation failed: {e}")
        
        return connections
    
    def _should_connect_elements(self, element1: Any, element2: Any) -> bool:
        """Determine if two elements should be connected."""
        try:
            # Check distance
            distance = self._calculate_distance(element1, element2)
            if distance > 100:  # Maximum connection distance
                return False
            
            # Check if elements are of compatible types for connection
            return self._are_compatible_for_connection(element1, element2)
            
        except Exception:
            return False
    
    def _calculate_distance(self, element1: Any, element2: Any) -> float:
        """Calculate distance between two elements."""
        try:
            loc1 = element1.location
            loc2 = element2.location
            
            if not loc1 or not loc2:
                return float('inf')
            
            x1, y1 = loc1.get('x', 0), loc1.get('y', 0)
            x2, y2 = loc2.get('x', 0), loc2.get('y', 0)
            
            return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
            
        except Exception:
            return float('inf')
    
    def _are_compatible_for_connection(self, element1: Any, element2: Any) -> bool:
        """Check if two elements are compatible for connection."""
        try:
            # Simple compatibility check based on element types
            type1 = type(element1).__name__
            type2 = type(element2).__name__
            
            # Same type elements can connect
            if type1 == type2:
                return True
            
            # Cross-system connections (e.g., electrical to lighting)
            if (type1 == "ElectricalElement" and type2 == "LightingElement") or \
               (type1 == "LightingElement" and type2 == "ElectricalElement"):
                return True
            
            return False
            
        except Exception:
            return False
    
    def _determine_connection_type(self, element1: Any, element2: Any) -> ConnectionType:
        """Determine the type of connection between two elements."""
        try:
            type1 = type(element1).__name__
            type2 = type(element2).__name__
            
            if "Electrical" in type1 or "Electrical" in type2:
                return ConnectionType.ELECTRICAL
            elif "HVAC" in type1 or "HVAC" in type2:
                return ConnectionType.MECHANICAL
            elif "Plumbing" in type1 or "Plumbing" in type2:
                return ConnectionType.HYDRAULIC
            elif "Network" in type1 or "Network" in type2:
                return ConnectionType.DATA
            elif "Structural" in type1 or "Structural" in type2:
                return ConnectionType.STRUCTURAL
            else:
                return ConnectionType.SPATIAL
            
        except Exception:
            return ConnectionType.SPATIAL
    
    def _resolve_geometry_and_spatial_relationships(self, model: EnhancedBIMModel):
        """Resolve geometry and spatial relationships in the model."""
        try:
            # This would integrate with the geometry resolver service
            # to calculate proper 3D coordinates, volumes, and spatial relationships
            
            # For now, just update the model timestamp
            model.updated_at = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Geometry resolution failed: {e}")
    
    def get_assembly_statistics(self) -> Dict[str, Any]:
        """Get assembly service statistics."""
        try:
            return {
                "symbol_recognition": self.symbol_recognition.get_recognition_statistics(),
                "system_templates": len(self.system_templates),
                "supported_building_types": list(self.system_templates.keys())
            }
        except Exception as e:
            self.logger.error(f"Failed to get assembly statistics: {e}")
            return {}


# Global instance
enhanced_bim_assembly = EnhancedBIMAssembly() 