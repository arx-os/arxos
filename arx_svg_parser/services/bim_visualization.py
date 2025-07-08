"""
BIM Visualization Components

This module provides comprehensive BIM visualization functionality:
- 2D and 3D rendering
- Interactive visualization
- Multiple visualization styles
- Real-time updates
- Performance optimization
- Export capabilities
"""

import logging
import json
import math
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict

from models.bim import (
    BIMElementBase, BIMSystem, BIMRelationship, Geometry, GeometryType,
    Room, Wall, Door, Window, Device, SystemType, DeviceCategory
)
from services.bim_validator import BIMValidator, ValidationLevel

logger = logging.getLogger(__name__)


class VisualizationType(Enum):
    """BIM visualization types"""
    TWO_D = "2d"
    THREE_D = "3d"
    WIREFRAME = "wireframe"
    SOLID = "solid"
    TRANSPARENT = "transparent"
    TEXTURED = "textured"


class ViewMode(Enum):
    """BIM view modes"""
    PLAN = "plan"
    ELEVATION = "elevation"
    SECTION = "section"
    ISOMETRIC = "isometric"
    PERSPECTIVE = "perspective"


class ColorScheme(Enum):
    """BIM color schemes"""
    SYSTEM_BASED = "system_based"
    TYPE_BASED = "type_based"
    STATUS_BASED = "status_based"
    CUSTOM = "custom"


@dataclass
class ViewportConfig:
    """Viewport configuration"""
    width: int = 800
    height: int = 600
    background_color: str = "#ffffff"
    grid_enabled: bool = True
    grid_size: float = 1.0
    grid_color: str = "#cccccc"
    axes_enabled: bool = True
    axes_color: str = "#000000"


@dataclass
class CameraConfig:
    """Camera configuration"""
    position: Tuple[float, float, float] = (0.0, 0.0, 10.0)
    target: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    up: Tuple[float, float, float] = (0.0, 1.0, 0.0)
    fov: float = 60.0
    near: float = 0.1
    far: float = 1000.0


@dataclass
class VisualizationStyle:
    """Visualization style configuration"""
    visualization_type: VisualizationType = VisualizationType.SOLID
    color_scheme: ColorScheme = ColorScheme.SYSTEM_BASED
    opacity: float = 1.0
    line_width: float = 1.0
    point_size: float = 3.0
    show_labels: bool = True
    show_annotations: bool = True
    highlight_selected: bool = True


@dataclass
class RenderingResult:
    """BIM rendering result"""
    success: bool
    image_data: Optional[bytes] = None
    svg_data: Optional[str] = None
    json_data: Optional[Dict[str, Any]] = None
    rendering_time: float = 0.0
    elements_rendered: int = 0
    errors: List[str] = field(default_factory=list)


class BIMVisualizer:
    """Comprehensive BIM visualizer"""
    
    def __init__(self):
        self.viewport_config = ViewportConfig()
        self.camera_config = CameraConfig()
        self.visualization_style = VisualizationStyle()
        self.color_palette = self._load_color_palette()
        self.element_styles = self._load_element_styles()
        
    def _load_color_palette(self) -> Dict[str, str]:
        """Load color palette for different element types."""
        return {
            # System-based colors
            'hvac': '#ff6b6b',
            'electrical': '#4ecdc4',
            'plumbing': '#45b7d1',
            'fire_alarm': '#ffa726',
            'security': '#ab47bc',
            'structural': '#8d6e63',
            
            # Type-based colors
            'room': '#e8f5e8',
            'wall': '#d7ccc8',
            'door': '#8d6e63',
            'window': '#90caf9',
            'device': '#ffcc02',
            
            # Status-based colors
            'active': '#4caf50',
            'inactive': '#9e9e9e',
            'maintenance': '#ff9800',
            'error': '#f44336',
            
            # Default colors
            'default': '#cccccc',
            'background': '#ffffff',
            'grid': '#e0e0e0',
            'axes': '#000000'
        }
    
    def _load_element_styles(self) -> Dict[str, Dict[str, Any]]:
        """Load element-specific visualization styles."""
        return {
            'Room': {
                'fill_color': '#e8f5e8',
                'stroke_color': '#4caf50',
                'stroke_width': 2,
                'opacity': 0.8
            },
            'Wall': {
                'fill_color': '#d7ccc8',
                'stroke_color': '#8d6e63',
                'stroke_width': 1,
                'opacity': 1.0
            },
            'Door': {
                'fill_color': '#8d6e63',
                'stroke_color': '#5d4037',
                'stroke_width': 1,
                'opacity': 1.0
            },
            'Window': {
                'fill_color': '#90caf9',
                'stroke_color': '#1976d2',
                'stroke_width': 1,
                'opacity': 0.7
            },
            'Device': {
                'fill_color': '#ffcc02',
                'stroke_color': '#f57f17',
                'stroke_width': 1,
                'opacity': 1.0
            }
        }
    
    def render_2d_view(self, bim_elements: List[BIMElementBase], 
                       view_mode: ViewMode = ViewMode.PLAN,
                       style: Optional[VisualizationStyle] = None) -> RenderingResult:
        """
        Render 2D view of BIM elements.
        
        Args:
            bim_elements: List of BIM elements to render
            view_mode: View mode (plan, elevation, section)
            style: Visualization style
            
        Returns:
            RenderingResult with SVG data
        """
        start_time = time.time()
        
        try:
            style = style or self.visualization_style
            
            # Create SVG content
            svg_content = self._create_svg_header()
            
            # Add grid if enabled
            if self.viewport_config.grid_enabled:
                svg_content += self._create_svg_grid()
            
            # Add axes if enabled
            if self.viewport_config.axes_enabled:
                svg_content += self._create_svg_axes()
            
            # Render elements
            for element in bim_elements:
                element_svg = self._render_element_2d(element, style, view_mode)
                if element_svg:
                    svg_content += element_svg
            
            # Close SVG
            svg_content += "</svg>"
            
            rendering_time = time.time() - start_time
            
            return RenderingResult(
                success=True,
                svg_data=svg_content,
                rendering_time=rendering_time,
                elements_rendered=len(bim_elements)
            )
            
        except Exception as e:
            logger.error(f"2D rendering failed: {e}")
            return RenderingResult(
                success=False,
                errors=[str(e)]
            )
    
    def render_3d_view(self, bim_elements: List[BIMElementBase],
                       style: Optional[VisualizationStyle] = None) -> RenderingResult:
        """
        Render 3D view of BIM elements.
        
        Args:
            bim_elements: List of BIM elements to render
            style: Visualization style
            
        Returns:
            RenderingResult with JSON data for 3D viewer
        """
        start_time = time.time()
        
        try:
            style = style or self.visualization_style
            
            # Create 3D scene data
            scene_data = {
                'metadata': {
                    'type': '3d_scene',
                    'version': '1.0',
                    'camera': {
                        'position': self.camera_config.position,
                        'target': self.camera_config.target,
                        'up': self.camera_config.up,
                        'fov': self.camera_config.fov,
                        'near': self.camera_config.near,
                        'far': self.camera_config.far
                    },
                    'viewport': {
                        'width': self.viewport_config.width,
                        'height': self.viewport_config.height,
                        'background_color': self.viewport_config.background_color
                    }
                },
                'elements': []
            }
            
            # Render elements
            for element in bim_elements:
                element_data = self._render_element_3d(element, style)
                if element_data:
                    scene_data['elements'].append(element_data)
            
            rendering_time = time.time() - start_time
            
            return RenderingResult(
                success=True,
                json_data=scene_data,
                rendering_time=rendering_time,
                elements_rendered=len(bim_elements)
            )
            
        except Exception as e:
            logger.error(f"3D rendering failed: {e}")
            return RenderingResult(
                success=False,
                errors=[str(e)]
            )
    
    def _create_svg_header(self) -> str:
        """Create SVG header with viewport configuration."""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{self.viewport_config.width}" height="{self.viewport_config.height}" 
     viewBox="0 0 {self.viewport_config.width} {self.viewport_config.height}"
     xmlns="http://www.w3.org/2000/svg">
<defs>
    <style>
        .element {{ stroke-width: 1; fill-opacity: 0.8; }}
        .room {{ fill: #e8f5e8; stroke: #4caf50; }}
        .wall {{ fill: #d7ccc8; stroke: #8d6e63; }}
        .door {{ fill: #8d6e63; stroke: #5d4037; }}
        .window {{ fill: #90caf9; stroke: #1976d2; }}
        .device {{ fill: #ffcc02; stroke: #f57f17; }}
        .grid {{ stroke: {self.viewport_config.grid_color}; stroke-width: 0.5; opacity: 0.3; }}
        .axes {{ stroke: {self.viewport_config.axes_color}; stroke-width: 2; }}
        .label {{ font-family: Arial, sans-serif; font-size: 12px; fill: #333; }}
    </style>
</defs>
<rect width="100%" height="100%" fill="{self.viewport_config.background_color}"/>
'''
    
    def _create_svg_grid(self) -> str:
        """Create SVG grid."""
        grid_size = self.viewport_config.grid_size
        width = self.viewport_config.width
        height = self.viewport_config.height
        
        grid_lines = []
        
        # Vertical lines
        for x in range(0, int(width), int(grid_size * 10)):
            grid_lines.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{height}" class="grid"/>')
        
        # Horizontal lines
        for y in range(0, int(height), int(grid_size * 10)):
            grid_lines.append(f'<line x1="0" y1="{y}" x2="{width}" y2="{y}" class="grid"/>')
        
        return '\n'.join(grid_lines)
    
    def _create_svg_axes(self) -> str:
        """Create SVG coordinate axes."""
        width = self.viewport_config.width
        height = self.viewport_config.height
        center_x = width / 2
        center_y = height / 2
        
        return f'''
<g class="axes">
    <line x1="{center_x}" y1="0" x2="{center_x}" y2="{height}" stroke="red"/>
    <line x1="0" y1="{center_y}" x2="{width}" y2="{center_y}" stroke="green"/>
    <text x="{center_x + 10}" y="20" class="label">Y</text>
    <text x="{width - 20}" y="{center_y - 10}" class="label">X</text>
</g>
'''
    
    def _render_element_2d(self, element: BIMElementBase, 
                          style: VisualizationStyle,
                          view_mode: ViewMode) -> Optional[str]:
        """Render a single element in 2D."""
        try:
            if not hasattr(element, 'geometry') or not element.geometry:
                return None
            
            geometry = element.geometry
            element_type = element.__class__.__name__
            
            # Get element style
            element_style = self.element_styles.get(element_type, self.element_styles['Device'])
            
            # Convert geometry to SVG path
            svg_path = self._geometry_to_svg_path(geometry, view_mode)
            if not svg_path:
                return None
            
            # Create SVG element
            element_id = getattr(element, 'id', 'unknown')
            element_name = getattr(element, 'name', element_id)
            
            svg_element = f'''
<g id="{element_id}" class="element {element_type.lower()}">
    <path d="{svg_path}" 
          fill="{element_style['fill_color']}" 
          stroke="{element_style['stroke_color']}" 
          stroke-width="{element_style['stroke_width']}" 
          opacity="{element_style['opacity']}"/>
'''
            
            # Add label if enabled
            if style.show_labels:
                label_pos = self._calculate_label_position(geometry, view_mode)
                svg_element += f'''
    <text x="{label_pos[0]}" y="{label_pos[1]}" class="label">{element_name}</text>
'''
            
            svg_element += '</g>'
            return svg_element
            
        except Exception as e:
            logger.warning(f"Failed to render element {getattr(element, 'id', 'unknown')}: {e}")
            return None
    
    def _geometry_to_svg_path(self, geometry: Geometry, view_mode: ViewMode) -> Optional[str]:
        """Convert geometry to SVG path."""
        try:
            if not geometry.coordinates:
                return None
            
            coords = geometry.coordinates
            geom_type = geometry.type
            
            if geom_type == GeometryType.POLYGON:
                return self._polygon_to_svg_path(coords, view_mode)
            elif geom_type == GeometryType.LINESTRING:
                return self._linestring_to_svg_path(coords, view_mode)
            elif geom_type == GeometryType.POINT:
                return self._point_to_svg_path(coords, view_mode)
            else:
                return None
                
        except Exception as e:
            logger.warning(f"Failed to convert geometry to SVG path: {e}")
            return None
    
    def _polygon_to_svg_path(self, coords: List, view_mode: ViewMode) -> str:
        """Convert polygon coordinates to SVG path."""
        if not coords or len(coords) < 3:
            return ""
        
        # Flatten coordinates for 2D view
        flat_coords = []
        for coord in coords:
            if isinstance(coord, (list, tuple)):
                if view_mode == ViewMode.PLAN:
                    flat_coords.extend([coord[0], coord[1]])
                else:
                    flat_coords.extend([coord[0], coord[2]])  # X-Z for elevation
            else:
                flat_coords.append(coord)
        
        if len(flat_coords) < 4:
            return ""
        
        # Create SVG path
        path = f"M {flat_coords[0]} {flat_coords[1]}"
        for i in range(2, len(flat_coords), 2):
            if i + 1 < len(flat_coords):
                path += f" L {flat_coords[i]} {flat_coords[i+1]}"
        
        path += " Z"  # Close polygon
        return path
    
    def _linestring_to_svg_path(self, coords: List, view_mode: ViewMode) -> str:
        """Convert linestring coordinates to SVG path."""
        if not coords or len(coords) < 2:
            return ""
        
        # Flatten coordinates
        flat_coords = []
        for coord in coords:
            if isinstance(coord, (list, tuple)):
                if view_mode == ViewMode.PLAN:
                    flat_coords.extend([coord[0], coord[1]])
                else:
                    flat_coords.extend([coord[0], coord[2]])
            else:
                flat_coords.append(coord)
        
        if len(flat_coords) < 2:
            return ""
        
        # Create SVG path
        path = f"M {flat_coords[0]} {flat_coords[1]}"
        for i in range(2, len(flat_coords), 2):
            if i + 1 < len(flat_coords):
                path += f" L {flat_coords[i]} {flat_coords[i+1]}"
        
        return path
    
    def _point_to_svg_path(self, coords: List, view_mode: ViewMode) -> str:
        """Convert point coordinates to SVG path."""
        if not coords or len(coords) < 2:
            return ""
        
        # Get point coordinates
        if isinstance(coords[0], (list, tuple)):
            if view_mode == ViewMode.PLAN:
                x, y = coords[0][0], coords[0][1]
            else:
                x, y = coords[0][0], coords[0][2]
        else:
            x, y = coords[0], coords[1]
        
        # Create circle for point
        radius = 3
        return f"M {x-radius} {y} A {radius} {radius} 0 1 1 {x+radius} {y} A {radius} {radius} 0 1 1 {x-radius} {y}"
    
    def _calculate_label_position(self, geometry: Geometry, view_mode: ViewMode) -> Tuple[float, float]:
        """Calculate label position for geometry."""
        try:
            coords = geometry.coordinates
            
            if geometry.type == GeometryType.POLYGON and coords:
                # Use centroid of polygon
                if isinstance(coords[0], (list, tuple)):
                    if view_mode == ViewMode.PLAN:
                        x_coords = [coord[0] for coord in coords]
                        y_coords = [coord[1] for coord in coords]
                    else:
                        x_coords = [coord[0] for coord in coords]
                        y_coords = [coord[2] for coord in coords]
                    
                    centroid_x = sum(x_coords) / len(x_coords)
                    centroid_y = sum(y_coords) / len(y_coords)
                    return (centroid_x, centroid_y)
            
            elif geometry.type == GeometryType.LINESTRING and coords:
                # Use midpoint of linestring
                if isinstance(coords[0], (list, tuple)):
                    if view_mode == ViewMode.PLAN:
                        x, y = coords[0][0], coords[0][1]
                    else:
                        x, y = coords[0][0], coords[0][2]
                else:
                    x, y = coords[0], coords[1]
                return (x, y)
            
            elif geometry.type == GeometryType.POINT and coords:
                # Use point coordinates
                if isinstance(coords[0], (list, tuple)):
                    if view_mode == ViewMode.PLAN:
                        x, y = coords[0][0], coords[0][1]
                    else:
                        x, y = coords[0][0], coords[0][2]
                else:
                    x, y = coords[0], coords[1]
                return (x, y)
            
            return (0, 0)
            
        except Exception as e:
            logger.warning(f"Failed to calculate label position: {e}")
            return (0, 0)
    
    def _render_element_3d(self, element: BIMElementBase, 
                          style: VisualizationStyle) -> Optional[Dict[str, Any]]:
        """Render a single element in 3D."""
        try:
            if not hasattr(element, 'geometry') or not element.geometry:
                return None
            
            geometry = element.geometry
            element_type = element.__class__.__name__
            element_id = getattr(element, 'id', 'unknown')
            element_name = getattr(element, 'name', element_id)
            
            # Get element style
            element_style = self.element_styles.get(element_type, self.element_styles['Device'])
            
            # Convert geometry to 3D mesh data
            mesh_data = self._geometry_to_3d_mesh(geometry)
            if not mesh_data:
                return None
            
            # Create 3D element data
            element_data = {
                'id': element_id,
                'name': element_name,
                'type': element_type,
                'geometry': mesh_data,
                'material': {
                    'color': element_style['fill_color'],
                    'opacity': element_style['opacity'],
                    'wireframe': style.visualization_type == VisualizationType.WIREFRAME
                },
                'properties': getattr(element, 'properties', {}),
                'metadata': getattr(element, 'metadata', {})
            }
            
            return element_data
            
        except Exception as e:
            logger.warning(f"Failed to render 3D element {getattr(element, 'id', 'unknown')}: {e}")
            return None
    
    def _geometry_to_3d_mesh(self, geometry: Geometry) -> Optional[Dict[str, Any]]:
        """Convert geometry to 3D mesh data."""
        try:
            coords = geometry.coordinates
            geom_type = geometry.type
            
            if geom_type == GeometryType.POLYGON:
                return self._polygon_to_3d_mesh(coords)
            elif geom_type == GeometryType.LINESTRING:
                return self._linestring_to_3d_mesh(coords)
            elif geom_type == GeometryType.POINT:
                return self._point_to_3d_mesh(coords)
            else:
                return None
                
        except Exception as e:
            logger.warning(f"Failed to convert geometry to 3D mesh: {e}")
            return None
    
    def _polygon_to_3d_mesh(self, coords: List) -> Dict[str, Any]:
        """Convert polygon coordinates to 3D mesh."""
        if not coords or len(coords) < 3:
            return None
        
        # Extract vertices
        vertices = []
        for coord in coords:
            if isinstance(coord, (list, tuple)):
                if len(coord) >= 3:
                    vertices.append([coord[0], coord[1], coord[2]])
                else:
                    vertices.append([coord[0], coord[1], 0.0])
            else:
                vertices.append([coord, 0.0, 0.0])
        
        # Create faces (triangulate polygon)
        faces = self._triangulate_polygon(vertices)
        
        return {
            'type': 'mesh',
            'vertices': vertices,
            'faces': faces,
            'normals': self._calculate_normals(vertices, faces)
        }
    
    def _linestring_to_3d_mesh(self, coords: List) -> Dict[str, Any]:
        """Convert linestring coordinates to 3D mesh."""
        if not coords or len(coords) < 2:
            return None
        
        # Extract vertices
        vertices = []
        for coord in coords:
            if isinstance(coord, (list, tuple)):
                if len(coord) >= 3:
                    vertices.append([coord[0], coord[1], coord[2]])
                else:
                    vertices.append([coord[0], coord[1], 0.0])
            else:
                vertices.append([coord, 0.0, 0.0])
        
        return {
            'type': 'line',
            'vertices': vertices
        }
    
    def _point_to_3d_mesh(self, coords: List) -> Dict[str, Any]:
        """Convert point coordinates to 3D mesh."""
        if not coords:
            return None
        
        # Extract vertex
        if isinstance(coords[0], (list, tuple)):
            if len(coords[0]) >= 3:
                vertex = [coords[0][0], coords[0][1], coords[0][2]]
            else:
                vertex = [coords[0][0], coords[0][1], 0.0]
        else:
            vertex = [coords[0], coords[1], 0.0]
        
        return {
            'type': 'point',
            'vertices': [vertex]
        }
    
    def _triangulate_polygon(self, vertices: List[List[float]]) -> List[List[int]]:
        """Simple polygon triangulation."""
        # This is a simplified triangulation
        # In a real implementation, you'd use a proper triangulation algorithm
        faces = []
        num_vertices = len(vertices)
        
        if num_vertices < 3:
            return faces
        
        # Fan triangulation (works for convex polygons)
        for i in range(1, num_vertices - 1):
            faces.append([0, i, i + 1])
        
        return faces
    
    def _calculate_normals(self, vertices: List[List[float]], 
                          faces: List[List[int]]) -> List[List[float]]:
        """Calculate face normals."""
        normals = []
        
        for face in faces:
            if len(face) >= 3:
                v1 = vertices[face[0]]
                v2 = vertices[face[1]]
                v3 = vertices[face[2]]
                
                # Calculate normal
                u = [v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]]
                v = [v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]]
                
                normal = [
                    u[1] * v[2] - u[2] * v[1],
                    u[2] * v[0] - u[0] * v[2],
                    u[0] * v[1] - u[1] * v[0]
                ]
                
                # Normalize
                length = math.sqrt(sum(n * n for n in normal))
                if length > 0:
                    normal = [n / length for n in normal]
                
                normals.append(normal)
            else:
                normals.append([0, 0, 1])
        
        return normals
    
    def create_interactive_viewer(self, bim_elements: List[BIMElementBase],
                                 view_mode: ViewMode = ViewMode.PLAN) -> Dict[str, Any]:
        """
        Create interactive viewer data.
        
        Args:
            bim_elements: List of BIM elements
            view_mode: View mode
            
        Returns:
            Dictionary with interactive viewer configuration
        """
        try:
            viewer_data = {
                'type': 'interactive_viewer',
                'version': '1.0',
                'viewport': {
                    'width': self.viewport_config.width,
                    'height': self.viewport_config.height,
                    'background_color': self.viewport_config.background_color
                },
                'camera': {
                    'position': self.camera_config.position,
                    'target': self.camera_config.target,
                    'up': self.camera_config.up,
                    'fov': self.camera_config.fov
                },
                'elements': [],
                'interactions': {
                    'pan': True,
                    'zoom': True,
                    'rotate': True,
                    'select': True,
                    'highlight': True
                },
                'controls': {
                    'show_grid': self.viewport_config.grid_enabled,
                    'show_axes': self.viewport_config.axes_enabled,
                    'show_labels': self.visualization_style.show_labels,
                    'show_annotations': self.visualization_style.show_annotations
                }
            }
            
            # Add elements
            for element in bim_elements:
                element_data = self._create_interactive_element(element, view_mode)
                if element_data:
                    viewer_data['elements'].append(element_data)
            
            return viewer_data
            
        except Exception as e:
            logger.error(f"Failed to create interactive viewer: {e}")
            return {'error': str(e)}
    
    def _create_interactive_element(self, element: BIMElementBase, 
                                  view_mode: ViewMode) -> Optional[Dict[str, Any]]:
        """Create interactive element data."""
        try:
            element_id = getattr(element, 'id', 'unknown')
            element_name = getattr(element, 'name', element_id)
            element_type = element.__class__.__name__
            
            # Get element style
            element_style = self.element_styles.get(element_type, self.element_styles['Device'])
            
            # Create interactive element data
            interactive_element = {
                'id': element_id,
                'name': element_name,
                'type': element_type,
                'style': {
                    'fill_color': element_style['fill_color'],
                    'stroke_color': element_style['stroke_color'],
                    'stroke_width': element_style['stroke_width'],
                    'opacity': element_style['opacity']
                },
                'properties': getattr(element, 'properties', {}),
                'metadata': getattr(element, 'metadata', {}),
                'geometry': self._geometry_to_interactive_data(element.geometry, view_mode)
            }
            
            return interactive_element
            
        except Exception as e:
            logger.warning(f"Failed to create interactive element {getattr(element, 'id', 'unknown')}: {e}")
            return None
    
    def _geometry_to_interactive_data(self, geometry: Geometry, 
                                    view_mode: ViewMode) -> Optional[Dict[str, Any]]:
        """Convert geometry to interactive data."""
        try:
            if not geometry or not geometry.coordinates:
                return None
            
            coords = geometry.coordinates
            geom_type = geometry.type
            
            if geom_type == GeometryType.POLYGON:
                return self._polygon_to_interactive_data(coords, view_mode)
            elif geom_type == GeometryType.LINESTRING:
                return self._linestring_to_interactive_data(coords, view_mode)
            elif geom_type == GeometryType.POINT:
                return self._point_to_interactive_data(coords, view_mode)
            else:
                return None
                
        except Exception as e:
            logger.warning(f"Failed to convert geometry to interactive data: {e}")
            return None
    
    def _polygon_to_interactive_data(self, coords: List, view_mode: ViewMode) -> Dict[str, Any]:
        """Convert polygon to interactive data."""
        # Flatten coordinates for 2D view
        flat_coords = []
        for coord in coords:
            if isinstance(coord, (list, tuple)):
                if view_mode == ViewMode.PLAN:
                    flat_coords.extend([coord[0], coord[1]])
                else:
                    flat_coords.extend([coord[0], coord[2]])
            else:
                flat_coords.append(coord)
        
        return {
            'type': 'polygon',
            'coordinates': flat_coords,
            'bounds': self._calculate_bounds(flat_coords)
        }
    
    def _linestring_to_interactive_data(self, coords: List, view_mode: ViewMode) -> Dict[str, Any]:
        """Convert linestring to interactive data."""
        # Flatten coordinates
        flat_coords = []
        for coord in coords:
            if isinstance(coord, (list, tuple)):
                if view_mode == ViewMode.PLAN:
                    flat_coords.extend([coord[0], coord[1]])
                else:
                    flat_coords.extend([coord[0], coord[2]])
            else:
                flat_coords.append(coord)
        
        return {
            'type': 'linestring',
            'coordinates': flat_coords,
            'bounds': self._calculate_bounds(flat_coords)
        }
    
    def _point_to_interactive_data(self, coords: List, view_mode: ViewMode) -> Dict[str, Any]:
        """Convert point to interactive data."""
        if isinstance(coords[0], (list, tuple)):
            if view_mode == ViewMode.PLAN:
                x, y = coords[0][0], coords[0][1]
            else:
                x, y = coords[0][0], coords[0][2]
        else:
            x, y = coords[0], coords[1]
        
        return {
            'type': 'point',
            'coordinates': [x, y],
            'bounds': {'min': [x, y], 'max': [x, y]}
        }
    
    def _calculate_bounds(self, coords: List[float]) -> Dict[str, List[float]]:
        """Calculate bounds of coordinates."""
        if len(coords) < 2:
            return {'min': [0, 0], 'max': [0, 0]}
        
        x_coords = [coords[i] for i in range(0, len(coords), 2)]
        y_coords = [coords[i] for i in range(1, len(coords), 2)]
        
        return {
            'min': [min(x_coords), min(y_coords)],
            'max': [max(x_coords), max(y_coords)]
        } 