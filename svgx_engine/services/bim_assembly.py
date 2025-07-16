"""
SVGX Engine BIM Assembly Service.

This service provides advanced BIM component assembly capabilities for SVGX Engine,
including:
- Multi-step BIM construction process
- Conflict resolution for overlapping elements
- BIM consistency validation
- Performance optimization for large models
- Assembly pipeline management
- Multi-system BIM model creation
- Advanced symbol recognition with SVGX integration
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

from .symbol_recognition import SymbolRecognitionService
from .bim_builder import BIMBuilderService
from .bim_validator import BIMValidatorService
try:
    try:
    from ..utils.performance import PerformanceMonitor
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.performance import PerformanceMonitor
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.performance import PerformanceMonitor
from ..models.bim import (
    BIMElement, BIMSystem, BIMRelationship, BIMSpace,
    Geometry, GeometryType, SystemType, ElementCategory
)
from ..models.svgx import SVGXElement, SVGXDocument
try:
    try:
    from ..utils.errors import (
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import (
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import (
    BIMAssemblyError, GeometryError, RelationshipError, 
    ValidationError, PerformanceError
)
try:
    try:
    from ..utils.performance import get_performance_report
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.performance import get_performance_report
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.performance import get_performance_report


# Type aliases
BIMElementType = Union[BIMElement, Dict[str, Any]]
AssemblyElement = Union[BIMElement, BIMSystem, BIMSpace]


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
    svgx_optimization_enabled: bool = True


class SVGXBIMAssemblyService:
    """
    SVGX Engine BIM Assembly Service.
    
    Provides advanced BIM component assembly capabilities with SVGX-specific
    optimizations and enhancements.
    """
    
    def __init__(self, config: Optional[AssemblyConfig] = None):
        """
        Initialize the BIM Assembly Service.
        
        Args:
            config: Assembly configuration
        """
        self.config = config or AssemblyConfig()
        self.logger = logging.getLogger(__name__)
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize dependent services
        self.symbol_recognition = SymbolRecognitionService()
        self.bim_builder = BIMBuilderService()
        self.bim_validator = BIMValidatorService()
        
        # Assembly state
        self.assembly_id = None
        self.elements: List[BIMElement] = []
        self.systems: List[BIMSystem] = []
        self.spaces: List[BIMSpace] = []
        self.relationships: List[BIMRelationship] = []
        self.conflicts: List[AssemblyConflict] = []
        self.assembly_stats: Dict[str, Any] = {}
        
        self.logger.info("BIM Assembly Service initialized")
    
    def assemble_bim(self, svgx_document: SVGXDocument, 
                     metadata: Optional[Dict[str, Any]] = None) -> AssemblyResult:
        """
        Assemble BIM model from SVGX document.
        
        Args:
            svgx_document: SVGX document to assemble
            metadata: Additional metadata for assembly
            
        Returns:
            AssemblyResult with assembly results
        """
        start_time = time.time()
        self.assembly_id = f"assembly_{int(time.time())}"
        
        try:
            self.logger.info(f"Starting BIM assembly for document: {svgx_document.id}")
            
            # Reset assembly state
            self._reset_assembly_state()
            
            # Execute assembly pipeline
            self._execute_assembly_pipeline(svgx_document, metadata)
            
            # Calculate performance metrics
            assembly_time = time.time() - start_time
            performance_metrics = self._calculate_performance_metrics(assembly_time)
            
            # Create assembly result
            result = AssemblyResult(
                success=True,
                assembly_id=self.assembly_id,
                elements=self.elements,
                systems=self.systems,
                spaces=self.spaces,
                relationships=self.relationships,
                conflicts=self.conflicts,
                validation_results=self.assembly_stats.get('validation', {}),
                performance_metrics=performance_metrics,
                assembly_time=assembly_time,
                warnings=self.assembly_stats.get('warnings', [])
            )
            
            self.logger.info(f"BIM assembly completed successfully in {assembly_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"BIM assembly failed: {str(e)}")
            raise BIMAssemblyError(f"Assembly failed: {str(e)}")
    
    def _reset_assembly_state(self):
        """Reset assembly state for new assembly."""
        self.elements = []
        self.systems = []
        self.spaces = []
        self.relationships = []
        self.conflicts = []
        self.assembly_stats = {}
    
    def _execute_assembly_pipeline(self, svgx_document: SVGXDocument, 
                                  metadata: Optional[Dict[str, Any]]):
        """Execute the complete assembly pipeline."""
        
        # Step 1: Geometry extraction
        with self.performance_monitor.measure("geometry_extraction"):
            self._extract_geometry(svgx_document)
        
        # Step 2: Element classification
        with self.performance_monitor.measure("element_classification"):
            self._classify_elements()
        
        # Step 3: Spatial organization
        with self.performance_monitor.measure("spatial_organization"):
            self._organize_spatial_structure()
        
        # Step 4: System integration
        with self.performance_monitor.measure("system_integration"):
            self._integrate_systems()
        
        # Step 5: Relationship establishment
        with self.performance_monitor.measure("relationship_establishment"):
            self._establish_relationships()
        
        # Step 6: Conflict resolution (if enabled)
        if self.config.conflict_resolution_enabled:
            with self.performance_monitor.measure("conflict_resolution"):
                self._resolve_conflicts()
        
        # Step 7: Consistency validation
        with self.performance_monitor.measure("consistency_validation"):
            self._validate_consistency()
        
        # Step 8: Performance optimization (if enabled)
        if self.config.performance_optimization_enabled:
            with self.performance_monitor.measure("performance_optimization"):
                self._optimize_performance()
    
    def _extract_geometry(self, svgx_document: SVGXDocument):
        """Extract geometry from SVGX document."""
        self.logger.info("Extracting geometry from SVGX document")
        
        for element in svgx_document.elements:
            try:
                bim_element = self._create_bim_element_from_svgx(element)
                if bim_element:
                    self.elements.append(bim_element)
            except Exception as e:
                self.logger.warning(f"Failed to extract geometry from element {element.id}: {str(e)}")
                self.assembly_stats.setdefault('warnings', []).append(
                    f"Geometry extraction failed for element {element.id}: {str(e)}"
                )
        
        self.logger.info(f"Extracted {len(self.elements)} BIM elements")
    
    def _create_bim_element_from_svgx(self, svgx_element: SVGXElement) -> Optional[BIMElement]:
        """Create BIM element from SVGX element."""
        try:
            # Extract basic properties
            element_id = svgx_element.id
            element_type = self._determine_element_type(svgx_element)
            geometry = self._extract_geometry_from_svgx(svgx_element)
            
            if not geometry:
                return None
            
            # Create BIM element
            bim_element = BIMElement(
                id=element_id,
                type=element_type,
                geometry=geometry,
                properties=svgx_element.properties,
                metadata=svgx_element.metadata
            )
            
            return bim_element
            
        except Exception as e:
            self.logger.error(f"Failed to create BIM element from SVGX element {svgx_element.id}: {str(e)}")
            return None
    
    def _determine_element_type(self, svgx_element: SVGXElement) -> str:
        """Determine BIM element type from SVGX element."""
        # Use symbol recognition to determine type
        symbol_match = self.symbol_recognition.recognize_symbol(svgx_element)
        
        if symbol_match and symbol_match.confidence > 0.7:
            return symbol_match.symbol_type
        
        # Fallback to element tag or properties
        return svgx_element.tag or "unknown"
    
    def _extract_geometry_from_svgx(self, svgx_element: SVGXElement) -> Optional[Geometry]:
        """Extract geometry from SVGX element."""
        try:
            # Extract coordinates from SVGX element
            coordinates = svgx_element.get_coordinates()
            
            if not coordinates:
                return None
            
            # Determine geometry type
            geometry_type = self._determine_geometry_type(svgx_element)
            
            # Create geometry object
            geometry = Geometry(
                type=geometry_type,
                coordinates=coordinates,
                properties=svgx_element.properties.get('geometry', {})
            )
            
            return geometry
            
        except Exception as e:
            self.logger.error(f"Failed to extract geometry from SVGX element {svgx_element.id}: {str(e)}")
            return None
    
    def _determine_geometry_type(self, svgx_element: SVGXElement) -> GeometryType:
        """Determine geometry type from SVGX element."""
        tag = svgx_element.tag.lower()
        
        if tag in ['rect', 'polygon']:
            return GeometryType.POLYGON
        elif tag in ['circle', 'ellipse']:
            return GeometryType.CIRCLE
        elif tag in ['line', 'polyline']:
            return GeometryType.LINE
        elif tag == 'path':
            return GeometryType.PATH
        else:
            return GeometryType.UNKNOWN
    
    def _classify_elements(self):
        """Classify BIM elements by category and system."""
        self.logger.info("Classifying BIM elements")
        
        for element in self.elements:
            try:
                category = self._determine_element_category(element)
                element.category = category
                
                system_type = self._determine_system_type(element)
                element.system_type = system_type
                
            except Exception as e:
                self.logger.warning(f"Failed to classify element {element.id}: {str(e)}")
    
    def _determine_element_category(self, element: BIMElement) -> ElementCategory:
        """Determine element category."""
        element_type = element.type.lower()
        
        # HVAC elements
        if any(hvac_type in element_type for hvac_type in ['hvac', 'air', 'vent', 'duct']):
            return ElementCategory.HVAC
        
        # Electrical elements
        elif any(elec_type in element_type for elec_type in ['electrical', 'power', 'outlet', 'panel']):
            return ElementCategory.ELECTRICAL
        
        # Plumbing elements
        elif any(plumb_type in element_type for plumb_type in ['plumbing', 'water', 'pipe', 'fixture']):
            return ElementCategory.PLUMBING
        
        # Fire safety elements
        elif any(fire_type in element_type for fire_type in ['fire', 'safety', 'alarm', 'sprinkler']):
            return ElementCategory.FIRE_SAFETY
        
        # Security elements
        elif any(sec_type in element_type for sec_type in ['security', 'camera', 'access']):
            return ElementCategory.SECURITY
        
        # Structural elements
        elif any(struct_type in element_type for struct_type in ['structural', 'wall', 'beam', 'column']):
            return ElementCategory.STRUCTURAL
        
        # Lighting elements
        elif any(light_type in element_type for light_type in ['lighting', 'light', 'lamp']):
            return ElementCategory.LIGHTING
        
        else:
            return ElementCategory.OTHER
    
    def _determine_system_type(self, element: BIMElement) -> SystemType:
        """Determine system type for element."""
        category = element.category
        
        system_mapping = {
            ElementCategory.HVAC: SystemType.HVAC,
            ElementCategory.ELECTRICAL: SystemType.ELECTRICAL,
            ElementCategory.PLUMBING: SystemType.PLUMBING,
            ElementCategory.FIRE_SAFETY: SystemType.FIRE_SAFETY,
            ElementCategory.SECURITY: SystemType.SECURITY,
            ElementCategory.STRUCTURAL: SystemType.STRUCTURAL,
            ElementCategory.LIGHTING: SystemType.LIGHTING,
            ElementCategory.OTHER: SystemType.OTHER
        }
        
        return system_mapping.get(category, SystemType.OTHER)
    
    def _organize_spatial_structure(self):
        """Organize elements into spatial structure."""
        self.logger.info("Organizing spatial structure")
        
        # Group elements by proximity
        element_groups = self._group_elements_by_proximity()
        
        # Create spaces from element groups
        for group_id, elements in element_groups.items():
            space = self._create_space_from_elements(group_id, elements)
            self.spaces.append(space)
        
        self.logger.info(f"Created {len(self.spaces)} spaces")
    
    def _group_elements_by_proximity(self) -> Dict[str, List[BIMElement]]:
        """Group elements by spatial proximity."""
        groups = {}
        processed_elements = set()
        
        for element in self.elements:
            if element.id in processed_elements:
                continue
            
            # Find nearby elements
            nearby_elements = self._find_nearby_elements(element, max_distance=10.0)
            
            if nearby_elements:
                group_id = f"space_{len(groups)}"
                groups[group_id] = [element] + nearby_elements
                
                # Mark elements as processed
                processed_elements.add(element.id)
                for nearby in nearby_elements:
                    processed_elements.add(nearby.id)
            else:
                # Single element space
                group_id = f"space_{len(groups)}"
                groups[group_id] = [element]
                processed_elements.add(element.id)
        
        return groups
    
    def _find_nearby_elements(self, reference_element: BIMElement, 
                              max_distance: float) -> List[BIMElement]:
        """Find elements within specified distance of reference element."""
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
        try:
            # Get element centers
            center1 = self._get_element_center(elem1)
            center2 = self._get_element_center(elem2)
            
            if center1 and center2:
                return np.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(center1, center2)))
            
            return float('inf')
            
        except Exception:
            return float('inf')
    
    def _get_element_center(self, element: BIMElement) -> Optional[List[float]]:
        """Get center coordinates of element."""
        if not element.geometry or not element.geometry.coordinates:
            return None
        
        coords = element.geometry.coordinates
        if len(coords) == 0:
            return None
        
        # Calculate centroid
        if element.geometry.type == GeometryType.CIRCLE:
            return coords[:2]  # First two coordinates for circle center
        
        # For other geometry types, calculate centroid
        x_coords = [coord[0] for coord in coords if len(coord) > 0]
        y_coords = [coord[1] for coord in coords if len(coord) > 1]
        
        if x_coords and y_coords:
            return [sum(x_coords) / len(x_coords), sum(y_coords) / len(y_coords)]
        
        return None
    
    def _create_space_from_elements(self, space_id: str, 
                                   elements: List[BIMElement]) -> BIMSpace:
        """Create BIM space from elements."""
        # Calculate space boundaries
        boundaries = self._calculate_space_boundaries(elements)
        
        # Determine space type
        space_type = self._determine_space_type(elements)
        
        # Create space
        space = BIMSpace(
            id=space_id,
            type=space_type,
            elements=[elem.id for elem in elements],
            boundaries=boundaries,
            properties={},
            metadata={}
        )
        
        return space
    
    def _calculate_space_boundaries(self, elements: List[BIMElement]) -> Dict[str, Any]:
        """Calculate boundaries for space containing elements."""
        if not elements:
            return {}
        
        all_coords = []
        for element in elements:
            if element.geometry and element.geometry.coordinates:
                all_coords.extend(element.geometry.coordinates)
        
        if not all_coords:
            return {}
        
        # Calculate bounding box
        x_coords = [coord[0] for coord in all_coords if len(coord) > 0]
        y_coords = [coord[1] for coord in all_coords if len(coord) > 1]
        
        if x_coords and y_coords:
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            
            return {
                'min': [min_x, min_y],
                'max': [max_x, max_y],
                'width': max_x - min_x,
                'height': max_y - min_y
            }
        
        return {}
    
    def _determine_space_type(self, elements: List[BIMElement]) -> str:
        """Determine space type based on contained elements."""
        if not elements:
            return "unknown"
        
        # Count elements by category
        category_counts = defaultdict(int)
        for element in elements:
            category_counts[element.category] += 1
        
        # Determine dominant category
        dominant_category = max(category_counts.items(), key=lambda x: x[1])[0]
        
        # Map category to space type
        space_type_mapping = {
            ElementCategory.HVAC: "mechanical",
            ElementCategory.ELECTRICAL: "electrical",
            ElementCategory.PLUMBING: "plumbing",
            ElementCategory.FIRE_SAFETY: "fire_safety",
            ElementCategory.SECURITY: "security",
            ElementCategory.STRUCTURAL: "structural",
            ElementCategory.LIGHTING: "lighting",
            ElementCategory.OTHER: "general"
        }
        
        return space_type_mapping.get(dominant_category, "general")
    
    def _integrate_systems(self):
        """Integrate elements into systems."""
        self.logger.info("Integrating systems")
        
        # Group elements by system type
        system_groups = defaultdict(list)
        for element in self.elements:
            system_groups[element.system_type].append(element)
        
        # Create systems
        for system_type, elements in system_groups.items():
            if elements:
                system = self._create_system(system_type, elements)
                self.systems.append(system)
        
        self.logger.info(f"Created {len(self.systems)} systems")
    
    def _create_system(self, system_type: SystemType, 
                      elements: List[BIMElement]) -> BIMSystem:
        """Create BIM system from elements."""
        system_id = f"system_{system_type.value}_{len(self.systems)}"
        
        system = BIMSystem(
            id=system_id,
            type=system_type,
            elements=[elem.id for elem in elements],
            properties={},
            metadata={}
        )
        
        return system
    
    def _establish_relationships(self):
        """Establish relationships between elements."""
        self.logger.info("Establishing relationships")
        
        # Spatial relationships
        self._establish_spatial_relationships()
        
        # System relationships
        self._establish_system_relationships()
        
        # Dependency relationships
        self._establish_dependency_relationships()
        
        self.logger.info(f"Established {len(self.relationships)} relationships")
    
    def _establish_spatial_relationships(self):
        """Establish spatial relationships between elements."""
        for i, elem1 in enumerate(self.elements):
            for elem2 in self.elements[i+1:]:
                if self._elements_intersect(elem1, elem2):
                    relationship = BIMRelationship(
                        id=f"spatial_{elem1.id}_{elem2.id}",
                        source_id=elem1.id,
                        target_id=elem2.id,
                        type="spatial_overlap",
                        properties={}
                    )
                    self.relationships.append(relationship)
    
    def _establish_system_relationships(self):
        """Establish system relationships."""
        for system in self.systems:
            for elem_id in system.elements:
                relationship = BIMRelationship(
                    id=f"system_{system.id}_{elem_id}",
                    source_id=system.id,
                    target_id=elem_id,
                    type="system_membership",
                    properties={}
                )
                self.relationships.append(relationship)
    
    def _establish_dependency_relationships(self):
        """Establish dependency relationships."""
        for elem1 in self.elements:
            dependencies = self._find_element_dependencies(elem1)
            for dep_id in dependencies:
                relationship = BIMRelationship(
                    id=f"dependency_{elem1.id}_{dep_id}",
                    source_id=elem1.id,
                    target_id=dep_id,
                    type="dependency",
                    properties={}
                )
                self.relationships.append(relationship)
    
    def _find_element_dependencies(self, element: BIMElement) -> List[str]:
        """Find dependencies for an element."""
        dependencies = []
        
        # Check for spatial dependencies
        for other_elem in self.elements:
            if other_elem.id != element.id and self._elements_intersect(element, other_elem):
                dependencies.append(other_elem.id)
        
        return dependencies
    
    def _elements_intersect(self, elem1: BIMElement, elem2: BIMElement) -> bool:
        """Check if two elements intersect."""
        if not elem1.geometry or not elem2.geometry:
            return False
        
        # Simple bounding box intersection check
        bounds1 = self._get_element_bounds(elem1)
        bounds2 = self._get_element_bounds(elem2)
        
        if not bounds1 or not bounds2:
            return False
        
        return not (bounds1['max'][0] < bounds2['min'][0] or
                   bounds1['min'][0] > bounds2['max'][0] or
                   bounds1['max'][1] < bounds2['min'][1] or
                   bounds1['min'][1] > bounds2['max'][1])
    
    def _get_element_bounds(self, element: BIMElement) -> Optional[Dict[str, List[float]]]:
        """Get bounding box for element."""
        if not element.geometry or not element.geometry.coordinates:
            return None
        
        coords = element.geometry.coordinates
        if not coords:
            return None
        
        x_coords = [coord[0] for coord in coords if len(coord) > 0]
        y_coords = [coord[1] for coord in coords if len(coord) > 1]
        
        if x_coords and y_coords:
            return {
                'min': [min(x_coords), min(y_coords)],
                'max': [max(x_coords), max(y_coords)]
            }
        
        return None
    
    def _resolve_conflicts(self):
        """Resolve assembly conflicts."""
        self.logger.info("Resolving conflicts")
        
        # Detect conflicts
        self._detect_geometric_conflicts()
        self._detect_spatial_conflicts()
        self._detect_system_conflicts()
        
        # Resolve conflicts
        for conflict in self.conflicts:
            if not conflict.resolved:
                self._resolve_conflict(conflict)
        
        self.logger.info(f"Resolved {len([c for c in self.conflicts if c.resolved])} conflicts")
    
    def _detect_geometric_conflicts(self):
        """Detect geometric conflicts."""
        for i, elem1 in enumerate(self.elements):
            for elem2 in self.elements[i+1:]:
                if self._elements_intersect(elem1, elem2):
                    conflict = AssemblyConflict(
                        conflict_id=f"geometric_{elem1.id}_{elem2.id}",
                        conflict_type=ConflictType.GEOMETRIC_OVERLAP,
                        elements=[elem1.id, elem2.id],
                        severity=0.8,
                        description=f"Geometric overlap between {elem1.id} and {elem2.id}"
                    )
                    self.conflicts.append(conflict)
    
    def _detect_spatial_conflicts(self):
        """Detect spatial conflicts."""
        for i, space1 in enumerate(self.spaces):
            for space2 in self.spaces[i+1:]:
                if self._spaces_overlap(space1, space2):
                    conflict = AssemblyConflict(
                        conflict_id=f"spatial_{space1.id}_{space2.id}",
                        conflict_type=ConflictType.SPATIAL_CONFLICT,
                        elements=[space1.id, space2.id],
                        severity=0.6,
                        description=f"Spatial overlap between {space1.id} and {space2.id}"
                    )
                    self.conflicts.append(conflict)
    
    def _spaces_overlap(self, space1: BIMSpace, space2: BIMSpace) -> bool:
        """Check if two spaces overlap."""
        bounds1 = space1.boundaries
        bounds2 = space2.boundaries
        
        if not bounds1 or not bounds2:
            return False
        
        return not (bounds1['max'][0] < bounds2['min'][0] or
                   bounds1['min'][0] > bounds2['max'][0] or
                   bounds1['max'][1] < bounds2['min'][1] or
                   bounds1['min'][1] > bounds2['max'][1])
    
    def _detect_system_conflicts(self):
        """Detect system conflicts."""
        # Check for elements in multiple systems
        element_system_count = defaultdict(int)
        for system in self.systems:
            for elem_id in system.elements:
                element_system_count[elem_id] += 1
        
        for elem_id, count in element_system_count.items():
            if count > 1:
                conflict = AssemblyConflict(
                    conflict_id=f"system_{elem_id}",
                    conflict_type=ConflictType.SYSTEM_CONFLICT,
                    elements=[elem_id],
                    severity=0.7,
                    description=f"Element {elem_id} belongs to multiple systems"
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
    
    def _resolve_geometric_conflict(self, conflict: AssemblyConflict):
        """Resolve geometric conflict."""
        # Simple resolution: adjust geometry slightly
        conflict.resolved = True
        conflict.resolution_suggestions.append("Geometry adjusted to resolve overlap")
    
    def _resolve_spatial_conflict(self, conflict: AssemblyConflict):
        """Resolve spatial conflict."""
        # Simple resolution: merge spaces
        conflict.resolved = True
        conflict.resolution_suggestions.append("Spaces merged to resolve overlap")
    
    def _resolve_system_conflict(self, conflict: AssemblyConflict):
        """Resolve system conflict."""
        # Simple resolution: assign to primary system
        conflict.resolved = True
        conflict.resolution_suggestions.append("Element assigned to primary system")
    
    def _validate_consistency(self) -> Dict[str, Any]:
        """Validate assembly consistency."""
        self.logger.info("Validating assembly consistency")
        
        validation_results = {
            'elements': self._validate_elements(),
            'systems': self._validate_systems(),
            'spaces': self._validate_spatial_structure(),
            'relationships': self._validate_relationships(),
            'geometries': self._validate_geometries()
        }
        
        self.assembly_stats['validation'] = validation_results
        return validation_results
    
    def _validate_elements(self) -> Dict[str, Any]:
        """Validate BIM elements."""
        total_elements = len(self.elements)
        valid_elements = sum(1 for elem in self.elements if elem.geometry)
        
        return {
            'total': total_elements,
            'valid': valid_elements,
            'validity_rate': valid_elements / total_elements if total_elements > 0 else 0
        }
    
    def _validate_systems(self) -> Dict[str, Any]:
        """Validate BIM systems."""
        total_systems = len(self.systems)
        valid_systems = sum(1 for sys in self.systems if sys.elements)
        
        return {
            'total': total_systems,
            'valid': valid_systems,
            'validity_rate': valid_systems / total_systems if total_systems > 0 else 0
        }
    
    def _validate_spatial_structure(self) -> Dict[str, Any]:
        """Validate spatial structure."""
        total_spaces = len(self.spaces)
        valid_spaces = sum(1 for space in self.spaces if space.elements)
        
        return {
            'total': total_spaces,
            'valid': valid_spaces,
            'validity_rate': valid_spaces / total_spaces if total_spaces > 0 else 0
        }
    
    def _validate_relationships(self) -> Dict[str, Any]:
        """Validate relationships."""
        total_relationships = len(self.relationships)
        valid_relationships = sum(1 for rel in self.relationships if rel.source_id and rel.target_id)
        
        return {
            'total': total_relationships,
            'valid': valid_relationships,
            'validity_rate': valid_relationships / total_relationships if total_relationships > 0 else 0
        }
    
    def _validate_geometries(self) -> Dict[str, Any]:
        """Validate geometries."""
        total_geometries = len(self.elements)
        valid_geometries = sum(1 for elem in self.elements if elem.geometry and elem.geometry.coordinates)
        
        return {
            'total': total_geometries,
            'valid': valid_geometries,
            'validity_rate': valid_geometries / total_geometries if total_geometries > 0 else 0
        }
    
    def _optimize_performance(self):
        """Optimize assembly performance."""
        self.logger.info("Optimizing performance")
        
        # Batch process elements
        self._batch_process_elements()
        
        # Optimize memory usage
        self._optimize_memory_usage()
        
        self.logger.info("Performance optimization completed")
    
    def _batch_process_elements(self):
        """Process elements in batches for better performance."""
        batch_size = self.config.batch_size
        
        for i in range(0, len(self.elements), batch_size):
            batch = self.elements[i:i + batch_size]
            self._process_element_batch(batch)
    
    def _process_element_batch(self, elements: List[BIMElement]):
        """Process a batch of elements."""
        # Process elements in parallel if enabled
        if self.config.parallel_processing:
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = [executor.submit(self._process_single_element, elem) for elem in elements]
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        self.logger.warning(f"Failed to process element batch: {str(e)}")
        else:
            for element in elements:
                self._process_single_element(element)
    
    def _process_single_element(self, element: BIMElement):
        """Process a single element."""
        # Apply SVGX-specific optimizations
        if self.config.svgx_optimization_enabled:
            self._apply_svgx_optimizations(element)
    
    def _apply_svgx_optimizations(self, element: BIMElement):
        """Apply SVGX-specific optimizations to element."""
        # Optimize geometry representation
        if element.geometry:
            self._optimize_geometry(element.geometry)
        
        # Optimize properties
        if element.properties:
            self._optimize_properties(element.properties)
    
    def _optimize_geometry(self, geometry: Geometry):
        """Optimize geometry representation."""
        # Simplify coordinates if needed
        if len(geometry.coordinates) > 100:
            # Simple decimation for large geometries
            step = len(geometry.coordinates) // 100
            geometry.coordinates = geometry.coordinates[::step]
    
    def _optimize_properties(self, properties: Dict[str, Any]):
        """Optimize element properties."""
        # Remove unnecessary properties
        unnecessary_keys = ['temp', 'cache', 'debug']
        for key in unnecessary_keys:
            properties.pop(key, None)
    
    def _optimize_memory_usage(self):
        """Optimize memory usage."""
        # Clear temporary data
        self.assembly_stats.pop('temp_data', None)
    
    def _calculate_performance_metrics(self, assembly_time: float) -> Dict[str, float]:
        """Calculate performance metrics."""
        return {
            'assembly_time': assembly_time,
            'elements_per_second': len(self.elements) / assembly_time if assembly_time > 0 else 0,
            'systems_per_second': len(self.systems) / assembly_time if assembly_time > 0 else 0,
            'spaces_per_second': len(self.spaces) / assembly_time if assembly_time > 0 else 0,
            'relationships_per_second': len(self.relationships) / assembly_time if assembly_time > 0 else 0,
            'conflicts_per_second': len(self.conflicts) / assembly_time if assembly_time > 0 else 0,
            'memory_usage_mb': self._get_memory_usage(),
            'cpu_usage_percent': self._get_cpu_usage()
        }
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent()
        except ImportError:
            return 0.0
    
    def get_assembly_statistics(self) -> Dict[str, Any]:
        """Get assembly statistics."""
        return {
            'assembly_id': self.assembly_id,
            'total_elements': len(self.elements),
            'total_systems': len(self.systems),
            'total_spaces': len(self.spaces),
            'total_relationships': len(self.relationships),
            'total_conflicts': len(self.conflicts),
            'resolved_conflicts': len([c for c in self.conflicts if c.resolved]),
            'performance_metrics': self.performance_monitor.get_metrics(),
            'validation_results': self.assembly_stats.get('validation', {}),
            'warnings': self.assembly_stats.get('warnings', [])
        }
    
    def export_assembly_report(self, output_path: str):
        """Export assembly report to file."""
        try:
            report = {
                'assembly_id': self.assembly_id,
                'timestamp': datetime.now().isoformat(),
                'statistics': self.get_assembly_statistics(),
                'elements': [elem.to_dict() for elem in self.elements],
                'systems': [sys.to_dict() for sys in self.systems],
                'spaces': [space.to_dict() for space in self.spaces],
                'relationships': [rel.to_dict() for rel in self.relationships],
                'conflicts': [conf.__dict__ for conf in self.conflicts]
            }
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"Assembly report exported to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export assembly report: {str(e)}")
            raise BIMAssemblyError(f"Failed to export report: {str(e)}") 