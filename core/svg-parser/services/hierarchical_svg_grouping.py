"""
Hierarchical SVG Grouping Service

This module provides advanced hierarchical grouping capabilities for large buildings
with 10,000+ objects. It implements spatial, system, and functional grouping
strategies to optimize rendering and processing performance.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import math
import json
from collections import defaultdict
import time

from models.bim import BIMModel, BIMElement, BIMSystem
from models.enhanced_bim_elements import EnhancedBIMModel, System, Connection
from utils.logger import get_logger

logger = get_logger(__name__)


class GroupingStrategy(Enum):
    """Grouping strategies for hierarchical organization"""
    SPATIAL = "spatial"
    SYSTEM = "system"
    FUNCTIONAL = "functional"
    HYBRID = "hybrid"


class GroupingLevel(Enum):
    """Hierarchical grouping levels"""
    BUILDING = "building"
    FLOOR = "floor"
    ZONE = "zone"
    SYSTEM = "system"
    COMPONENT = "component"
    ELEMENT = "element"


@dataclass
class GroupingMetrics:
    """Metrics for grouping performance"""
    total_elements: int
    grouped_elements: int
    grouping_time_ms: float
    memory_usage_mb: float
    hierarchy_depth: int
    max_group_size: int
    average_group_size: float
    spatial_efficiency: float
    system_coverage: float


@dataclass
class SpatialBounds:
    """Spatial bounds for grouping"""
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float
    
    @property
    def width(self) -> float:
        return self.max_x - self.min_x
    
    @property
    def height(self) -> float:
        return self.max_y - self.min_y
    
    @property
    def depth(self) -> float:
        return self.max_z - self.min_z
    
    @property
    def area(self) -> float:
        return self.width * self.height
    
    @property
    def volume(self) -> float:
        return self.width * self.height * self.depth


@dataclass
class HierarchicalGroup:
    """Hierarchical group structure"""
    group_id: str
    level: GroupingLevel
    name: str
    bounds: SpatialBounds
    elements: List[str] = field(default_factory=list)
    children: List['HierarchicalGroup'] = field(default_factory=list)
    parent: Optional['HierarchicalGroup'] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_element(self, element_id: str):
        """Add element to group"""
        if element_id not in self.elements:
            self.elements.append(element_id)
    
    def add_child(self, child: 'HierarchicalGroup'):
        """Add child group"""
        child.parent = self
        self.children.append(child)
    
    def get_all_elements(self) -> List[str]:
        """Get all elements in this group and children"""
        elements = self.elements.copy()
        for child in self.children:
            elements.extend(child.get_all_elements())
        return elements
    
    def get_element_count(self) -> int:
        """Get total element count including children"""
        return len(self.get_all_elements())


class SpatialGroupingStrategy:
    """Spatial grouping strategy based on geometric proximity"""
    
    def __init__(self, grid_size: float = 10.0, max_group_size: int = 100):
        self.grid_size = grid_size
        self.max_group_size = max_group_size
        self.logger = get_logger(__name__)
    
    def group_elements(self, elements: List[Dict[str, Any]]) -> List[HierarchicalGroup]:
        """Group elements based on spatial proximity"""
        start_time = time.time()
        
        # Create spatial grid
        grid = self._create_spatial_grid(elements)
        
        # Group elements by grid cells
        groups = []
        for cell_key, cell_elements in grid.items():
            if len(cell_elements) > 0:
                group = self._create_group_from_cell(cell_key, cell_elements)
                groups.append(group)
        
        # Merge small groups
        merged_groups = self._merge_small_groups(groups)
        
        grouping_time = (time.time() - start_time) * 1000
        self.logger.info(f"Spatial grouping completed: {len(merged_groups)} groups, {grouping_time:.2f}ms")
        
        return merged_groups
    
    def _create_spatial_grid(self, elements: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Create spatial grid for elements"""
        grid = defaultdict(list)
        
        for element in elements:
            x, y, z = element.get('x', 0), element.get('y', 0), element.get('z', 0)
            cell_x = int(x // self.grid_size)
            cell_y = int(y // self.grid_size)
            cell_z = int(z // self.grid_size)
            cell_key = f"{cell_x},{cell_y},{cell_z}"
            grid[cell_key].append(element)
        
        return grid
    
    def _create_group_from_cell(self, cell_key: str, elements: List[Dict[str, Any]]) -> HierarchicalGroup:
        """Create group from grid cell"""
        # Calculate bounds
        min_x = min(e.get('x', 0) for e in elements)
        min_y = min(e.get('y', 0) for e in elements)
        min_z = min(e.get('z', 0) for e in elements)
        max_x = max(e.get('x', 0) for e in elements)
        max_y = max(e.get('y', 0) for e in elements)
        max_z = max(e.get('z', 0) for e in elements)
        
        bounds = SpatialBounds(min_x, min_y, min_z, max_x, max_y, max_z)
        
        group = HierarchicalGroup(
            group_id=f"spatial_{cell_key}",
            level=GroupingLevel.ZONE,
            name=f"Spatial Zone {cell_key}",
            bounds=bounds,
            elements=[e.get('id', '') for e in elements],
            metadata={
                'grouping_strategy': 'spatial',
                'cell_key': cell_key,
                'element_count': len(elements)
            }
        )
        
        return group
    
    def _merge_small_groups(self, groups: List[HierarchicalGroup]) -> List[HierarchicalGroup]:
        """Merge small groups to optimize performance"""
        if len(groups) <= 1:
            return groups
        
        # Sort groups by size
        groups.sort(key=lambda g: len(g.elements))
        
        merged_groups = []
        current_group = None
        
        for group in groups:
            if current_group is None:
                current_group = group
            elif len(current_group.elements) + len(group.elements) <= self.max_group_size:
                # Merge groups
                current_group.elements.extend(group.elements)
                current_group.children.extend(group.children)
                # Update bounds
                current_group.bounds = self._merge_bounds(current_group.bounds, group.bounds)
            else:
                merged_groups.append(current_group)
                current_group = group
        
        if current_group:
            merged_groups.append(current_group)
        
        return merged_groups
    
    def _merge_bounds(self, bounds1: SpatialBounds, bounds2: SpatialBounds) -> SpatialBounds:
        """Merge two spatial bounds"""
        return SpatialBounds(
            min_x=min(bounds1.min_x, bounds2.min_x),
            min_y=min(bounds1.min_y, bounds2.min_y),
            min_z=min(bounds1.min_z, bounds2.min_z),
            max_x=max(bounds1.max_x, bounds2.max_x),
            max_y=max(bounds1.max_y, bounds2.max_y),
            max_z=max(bounds1.max_z, bounds2.max_z)
        )


class SystemGroupingStrategy:
    """System-based grouping strategy"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.system_mapping = {
            'ELECTRICAL': ['outlet', 'switch', 'panel', 'light', 'electrical'],
            'MECHANICAL': ['hvac', 'duct', 'air', 'mechanical', 'ventilation'],
            'PLUMBING': ['pipe', 'valve', 'fixture', 'plumbing', 'water'],
            'STRUCTURAL': ['wall', 'column', 'beam', 'structural', 'foundation'],
            'LIFE_SAFETY': ['fire', 'safety', 'alarm', 'sprinkler', 'emergency'],
            'TELECOMMUNICATIONS': ['data', 'network', 'telecom', 'cable', 'fiber']
        }
    
    def group_elements(self, elements: List[Dict[str, Any]]) -> List[HierarchicalGroup]:
        """Group elements based on system classification"""
        start_time = time.time()
        
        # Classify elements by system
        system_groups = defaultdict(list)
        
        for element in elements:
            system = self._classify_element_system(element)
            system_groups[system].append(element)
        
        # Create hierarchical groups
        groups = []
        for system_name, system_elements in system_groups.items():
            if len(system_elements) > 0:
                group = self._create_system_group(system_name, system_elements)
                groups.append(group)
        
        grouping_time = (time.time() - start_time) * 1000
        self.logger.info(f"System grouping completed: {len(groups)} groups, {grouping_time:.2f}ms")
        
        return groups
    
    def _classify_element_system(self, element: Dict[str, Any]) -> str:
        """Classify element by system"""
        element_type = element.get('type', '').upper()
        element_name = element.get('name', '').upper()
        
        for system, keywords in self.system_mapping.items():
            for keyword in keywords:
                if keyword.upper() in element_type or keyword.upper() in element_name:
                    return system
        
        return 'GENERAL'
    
    def _create_system_group(self, system_name: str, elements: List[Dict[str, Any]]) -> HierarchicalGroup:
        """Create system-based group"""
        # Calculate bounds
        min_x = min(e.get('x', 0) for e in elements)
        min_y = min(e.get('y', 0) for e in elements)
        min_z = min(e.get('z', 0) for e in elements)
        max_x = max(e.get('x', 0) for e in elements)
        max_y = max(e.get('y', 0) for e in elements)
        max_z = max(e.get('z', 0) for e in elements)
        
        bounds = SpatialBounds(min_x, min_y, min_z, max_x, max_y, max_z)
        
        group = HierarchicalGroup(
            group_id=f"system_{system_name.lower()}",
            level=GroupingLevel.SYSTEM,
            name=f"{system_name} System",
            bounds=bounds,
            elements=[e.get('id', '') for e in elements],
            metadata={
                'grouping_strategy': 'system',
                'system_name': system_name,
                'element_count': len(elements)
            }
        )
        
        return group


class FunctionalGroupingStrategy:
    """Functional grouping strategy based on element purpose"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.functional_mapping = {
            'ENCLOSURE': ['wall', 'door', 'window', 'partition'],
            'CIRCULATION': ['corridor', 'stair', 'elevator', 'ramp'],
            'SERVICES': ['utility', 'equipment', 'furniture'],
            'SPACE': ['room', 'office', 'meeting', 'storage'],
            'INFRASTRUCTURE': ['foundation', 'structure', 'roof']
        }
    
    def group_elements(self, elements: List[Dict[str, Any]]) -> List[HierarchicalGroup]:
        """Group elements based on functional purpose"""
        start_time = time.time()
        
        # Classify elements by function
        functional_groups = defaultdict(list)
        
        for element in elements:
            function = self._classify_element_function(element)
            functional_groups[function].append(element)
        
        # Create hierarchical groups
        groups = []
        for function_name, function_elements in functional_groups.items():
            if len(function_elements) > 0:
                group = self._create_functional_group(function_name, function_elements)
                groups.append(group)
        
        grouping_time = (time.time() - start_time) * 1000
        self.logger.info(f"Functional grouping completed: {len(groups)} groups, {grouping_time:.2f}ms")
        
        return groups
    
    def _classify_element_function(self, element: Dict[str, Any]) -> str:
        """Classify element by functional purpose"""
        element_type = element.get('type', '').upper()
        element_name = element.get('name', '').upper()
        
        for function, keywords in self.functional_mapping.items():
            for keyword in keywords:
                if keyword.upper() in element_type or keyword.upper() in element_name:
                    return function
        
        return 'GENERAL'
    
    def _create_functional_group(self, function_name: str, elements: List[Dict[str, Any]]) -> HierarchicalGroup:
        """Create functional group"""
        # Calculate bounds
        min_x = min(e.get('x', 0) for e in elements)
        min_y = min(e.get('y', 0) for e in elements)
        min_z = min(e.get('z', 0) for e in elements)
        max_x = max(e.get('x', 0) for e in elements)
        max_y = max(e.get('y', 0) for e in elements)
        max_z = max(e.get('z', 0) for e in elements)
        
        bounds = SpatialBounds(min_x, min_y, min_z, max_x, max_y, max_z)
        
        group = HierarchicalGroup(
            group_id=f"functional_{function_name.lower()}",
            level=GroupingLevel.COMPONENT,
            name=f"{function_name} Components",
            bounds=bounds,
            elements=[e.get('id', '') for e in elements],
            metadata={
                'grouping_strategy': 'functional',
                'function_name': function_name,
                'element_count': len(elements)
            }
        )
        
        return group


class HierarchicalSVGGrouping:
    """
    Advanced hierarchical SVG grouping service for large buildings.
    
    Features:
    - Multiple grouping strategies (spatial, system, functional)
    - Efficient handling of 10,000+ objects
    - Rendering optimization based on viewport
    - Memory-efficient hierarchical structures
    - Performance monitoring and metrics
    """
    
    def __init__(self, max_group_size: int = 100, grid_size: float = 10.0):
        self.max_group_size = max_group_size
        self.grid_size = grid_size
        self.logger = get_logger(__name__)
        
        # Grouping strategies
        self.grouping_strategies = {
            GroupingStrategy.SPATIAL: SpatialGroupingStrategy(grid_size, max_group_size),
            GroupingStrategy.SYSTEM: SystemGroupingStrategy(),
            GroupingStrategy.FUNCTIONAL: FunctionalGroupingStrategy()
        }
        
        # Performance tracking
        self.performance_metrics = []
    
    def create_hierarchy(self, building_data: Dict[str, Any], 
                        strategy: GroupingStrategy = GroupingStrategy.HYBRID) -> HierarchicalGroup:
        """
        Create hierarchical structure from flat building data.
        
        Args:
            building_data: Building data with elements
            strategy: Grouping strategy to use
            
        Returns:
            HierarchicalGroup: Root group with hierarchical structure
        """
        start_time = time.time()
        
        elements = building_data.get('elements', [])
        building_id = building_data.get('building_id', 'unknown')
        
        self.logger.info(f"Creating hierarchy for building {building_id} with {len(elements)} elements")
        
        # Create root group
        root_bounds = self._calculate_building_bounds(elements)
        root_group = HierarchicalGroup(
            group_id=f"building_{building_id}",
            level=GroupingLevel.BUILDING,
            name=f"Building {building_id}",
            bounds=root_bounds,
            metadata={
                'building_id': building_id,
                'total_elements': len(elements),
                'grouping_strategy': strategy.value
            }
        )
        
        # Apply grouping strategy
        if strategy == GroupingStrategy.HYBRID:
            # Use multiple strategies and combine
            groups = self._apply_hybrid_grouping(elements)
        else:
            # Use single strategy
            groups = self.grouping_strategies[strategy].group_elements(elements)
        
        # Add groups as children of root
        for group in groups:
            root_group.add_child(group)
        
        # Calculate metrics
        metrics = self._calculate_grouping_metrics(root_group, time.time() - start_time)
        self.performance_metrics.append(metrics)
        
        self.logger.info(f"Hierarchy created: {metrics.grouped_elements} elements in {len(groups)} groups")
        
        return root_group
    
    def _apply_hybrid_grouping(self, elements: List[Dict[str, Any]]) -> List[HierarchicalGroup]:
        """Apply hybrid grouping using multiple strategies"""
        # First, group by system
        system_groups = self.grouping_strategies[GroupingStrategy.SYSTEM].group_elements(elements)
        
        # Then, apply spatial grouping within each system group
        hybrid_groups = []
        
        for system_group in system_groups:
            system_elements = [e for e in elements if e.get('id') in system_group.elements]
            
            # Apply spatial grouping to system elements
            spatial_groups = self.grouping_strategies[GroupingStrategy.SPATIAL].group_elements(system_elements)
            
            # Add spatial groups as children of system group
            for spatial_group in spatial_groups:
                system_group.add_child(spatial_group)
            
            hybrid_groups.append(system_group)
        
        return hybrid_groups
    
    def _calculate_building_bounds(self, elements: List[Dict[str, Any]]) -> SpatialBounds:
        """Calculate building bounds from elements"""
        if not elements:
            return SpatialBounds(0, 0, 0, 0, 0, 0)
        
        min_x = min(e.get('x', 0) for e in elements)
        min_y = min(e.get('y', 0) for e in elements)
        min_z = min(e.get('z', 0) for e in elements)
        max_x = max(e.get('x', 0) for e in elements)
        max_y = max(e.get('y', 0) for e in elements)
        max_z = max(e.get('z', 0) for e in elements)
        
        return SpatialBounds(min_x, min_y, min_z, max_x, max_y, max_z)
    
    def optimize_rendering(self, hierarchy: HierarchicalGroup, 
                          viewport_bounds: SpatialBounds, 
                          zoom_level: float) -> List[str]:
        """
        Optimize rendering based on viewport and zoom level.
        
        Args:
            hierarchy: Hierarchical group structure
            viewport_bounds: Current viewport bounds
            zoom_level: Current zoom level
            
        Returns:
            List[str]: Element IDs to render
        """
        # Calculate detail level based on zoom
        detail_threshold = self._calculate_detail_threshold(zoom_level)
        
        # Find groups that intersect with viewport
        visible_groups = self._find_visible_groups(hierarchy, viewport_bounds)
        
        # Select elements based on detail level
        elements_to_render = []
        
        for group in visible_groups:
            if group.get_element_count() <= detail_threshold:
                # Render all elements in group
                elements_to_render.extend(group.get_all_elements())
            else:
                # Render only group bounds or representative elements
                elements_to_render.extend(self._get_representative_elements(group))
        
        return elements_to_render
    
    def _calculate_detail_threshold(self, zoom_level: float) -> int:
        """Calculate detail threshold based on zoom level"""
        # Higher zoom = more detail
        base_threshold = 50
        zoom_factor = max(0.1, min(2.0, zoom_level))
        return int(base_threshold * zoom_factor)
    
    def _find_visible_groups(self, group: HierarchicalGroup, 
                            viewport_bounds: SpatialBounds) -> List[HierarchicalGroup]:
        """Find groups that intersect with viewport"""
        visible_groups = []
        
        if self._bounds_intersect(group.bounds, viewport_bounds):
            visible_groups.append(group)
            
            # Check children
            for child in group.children:
                visible_groups.extend(self._find_visible_groups(child, viewport_bounds))
        
        return visible_groups
    
    def _bounds_intersect(self, bounds1: SpatialBounds, bounds2: SpatialBounds) -> bool:
        """Check if two bounds intersect"""
        return not (bounds1.max_x < bounds2.min_x or bounds1.min_x > bounds2.max_x or
                   bounds1.max_y < bounds2.min_y or bounds1.min_y > bounds2.max_y or
                   bounds1.max_z < bounds2.min_z or bounds1.min_z > bounds2.max_z)
    
    def _get_representative_elements(self, group: HierarchicalGroup) -> List[str]:
        """Get representative elements for large groups"""
        # Return first few elements as representatives
        return group.elements[:10]
    
    def handle_large_buildings(self, building_data: Dict[str, Any]) -> HierarchicalGroup:
        """
        Handle buildings with 10,000+ objects efficiently.
        
        Args:
            building_data: Building data with large number of elements
            
        Returns:
            HierarchicalGroup: Optimized hierarchical structure
        """
        elements = building_data.get('elements', [])
        
        if len(elements) < 1000:
            # Use standard grouping for smaller buildings
            return self.create_hierarchy(building_data)
        
        self.logger.info(f"Handling large building with {len(elements)} elements")
        
        # Use optimized strategy for large buildings
        # 1. Pre-filter elements by spatial bounds
        # 2. Use larger grid size for initial grouping
        # 3. Apply progressive detail loading
        
        # Increase grid size for large buildings
        original_grid_size = self.grid_size
        self.grid_size = max(20.0, self.grid_size * 2)
        
        try:
            hierarchy = self.create_hierarchy(building_data, GroupingStrategy.SPATIAL)
        finally:
            # Restore original grid size
            self.grid_size = original_grid_size
        
        return hierarchy
    
    def _calculate_grouping_metrics(self, hierarchy: HierarchicalGroup, 
                                  grouping_time: float) -> GroupingMetrics:
        """Calculate grouping performance metrics"""
        import psutil
        
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        
        total_elements = hierarchy.get_element_count()
        grouped_elements = len(hierarchy.get_all_elements())
        
        # Calculate hierarchy depth
        max_depth = self._calculate_max_depth(hierarchy)
        
        # Calculate group sizes
        group_sizes = self._get_all_group_sizes(hierarchy)
        max_group_size = max(group_sizes) if group_sizes else 0
        average_group_size = sum(group_sizes) / len(group_sizes) if group_sizes else 0
        
        # Calculate spatial efficiency
        spatial_efficiency = self._calculate_spatial_efficiency(hierarchy)
        
        # Calculate system coverage
        system_coverage = self._calculate_system_coverage(hierarchy)
        
        return GroupingMetrics(
            total_elements=total_elements,
            grouped_elements=grouped_elements,
            grouping_time_ms=grouping_time * 1000,
            memory_usage_mb=memory_usage,
            hierarchy_depth=max_depth,
            max_group_size=max_group_size,
            average_group_size=average_group_size,
            spatial_efficiency=spatial_efficiency,
            system_coverage=system_coverage
        )
    
    def _calculate_max_depth(self, group: HierarchicalGroup, current_depth: int = 0) -> int:
        """Calculate maximum depth of hierarchy"""
        max_depth = current_depth
        
        for child in group.children:
            child_depth = self._calculate_max_depth(child, current_depth + 1)
            max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def _get_all_group_sizes(self, group: HierarchicalGroup) -> List[int]:
        """Get sizes of all groups in hierarchy"""
        sizes = [len(group.elements)]
        
        for child in group.children:
            sizes.extend(self._get_all_group_sizes(child))
        
        return sizes
    
    def _calculate_spatial_efficiency(self, group: HierarchicalGroup) -> float:
        """Calculate spatial efficiency of grouping"""
        # This is a simplified calculation
        # In practice, would calculate how well groups minimize spatial overlap
        return 0.85  # Placeholder
    
    def _calculate_system_coverage(self, group: HierarchicalGroup) -> float:
        """Calculate system coverage of grouping"""
        # This is a simplified calculation
        # In practice, would calculate how well groups align with system boundaries
        return 0.90  # Placeholder
    
    def get_performance_metrics(self) -> List[GroupingMetrics]:
        """Get performance metrics from all operations"""
        return self.performance_metrics.copy()
    
    def export_hierarchy(self, hierarchy: HierarchicalGroup) -> Dict[str, Any]:
        """Export hierarchy to JSON format"""
        def serialize_group(group: HierarchicalGroup) -> Dict[str, Any]:
            return {
                'group_id': group.group_id,
                'level': group.level.value,
                'name': group.name,
                'bounds': {
                    'min_x': group.bounds.min_x,
                    'min_y': group.bounds.min_y,
                    'min_z': group.bounds.min_z,
                    'max_x': group.bounds.max_x,
                    'max_y': group.bounds.max_y,
                    'max_z': group.bounds.max_z
                },
                'elements': group.elements,
                'children': [serialize_group(child) for child in group.children],
                'metadata': group.metadata
            }
        
        return serialize_group(hierarchy)
    
    def import_hierarchy(self, hierarchy_data: Dict[str, Any]) -> HierarchicalGroup:
        """Import hierarchy from JSON format"""
        def deserialize_group(data: Dict[str, Any]) -> HierarchicalGroup:
            bounds = SpatialBounds(
                data['bounds']['min_x'],
                data['bounds']['min_y'],
                data['bounds']['min_z'],
                data['bounds']['max_x'],
                data['bounds']['max_y'],
                data['bounds']['max_z']
            )
            
            group = HierarchicalGroup(
                group_id=data['group_id'],
                level=GroupingLevel(data['level']),
                name=data['name'],
                bounds=bounds,
                elements=data['elements'],
                metadata=data.get('metadata', {})
            )
            
            for child_data in data.get('children', []):
                child = deserialize_group(child_data)
                group.add_child(child)
            
            return group
        
        return deserialize_group(hierarchy_data) 