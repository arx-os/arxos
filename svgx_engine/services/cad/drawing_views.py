"""
SVGX Engine - Drawing Views System

This module implements the drawing views system for CAD-parity functionality,
providing multiple view generation for technical drawings.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import math
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .precision_drawing_system import PrecisionPoint, PrecisionVector, PrecisionLevel

logger = logging.getLogger(__name__)


class ViewType(Enum):
    """Types of drawing views."""
    FRONT = "front"
    TOP = "top"
    SIDE = "side"
    ISOMETRIC = "isometric"
    SECTION = "section"
    DETAIL = "detail"
    AUXILIARY = "auxiliary"
    BROKEN = "broken"


class ProjectionType(Enum):
    """Types of projections."""
    FIRST_ANGLE = "first_angle"
    THIRD_ANGLE = "third_angle"


class ViewScale(Enum):
    """Standard view scales."""
    SCALE_1_1 = "1:1"
    SCALE_1_2 = "1:2"
    SCALE_1_5 = "1:5"
    SCALE_1_10 = "1:10"
    SCALE_2_1 = "2:1"
    SCALE_5_1 = "5:1"
    SCALE_10_1 = "10:1"
    CUSTOM = "custom"


@dataclass
class ViewConfig:
    """Configuration for a drawing view."""
    view_type: ViewType
    scale: Union[ViewScale, Decimal] = ViewScale.SCALE_1_1
    show_hidden_lines: bool = True
    show_center_lines: bool = True
    show_dimensions: bool = True
    show_annotations: bool = True
    show_grid: bool = False
    show_axes: bool = False
    background_color: str = "#FFFFFF"
    border_color: str = "#000000"
    border_width: Decimal = Decimal("0.5")


@dataclass
class DrawingView:
    """A drawing view with configuration and content."""
    view_id: str
    name: str
    config: ViewConfig
    origin: PrecisionPoint = field(default_factory=lambda: PrecisionPoint(0, 0))
    width: Decimal = Decimal("297")  # A4 width in mm
    height: Decimal = Decimal("210")  # A4 height in mm
    rotation: Decimal = Decimal("0")  # Rotation in degrees
    visible: bool = True
    locked: bool = False
    content: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate view after initialization."""
        self._validate_view()
    
    def _validate_view(self) -> None:
        """Validate view parameters."""
        if not self.view_id:
            raise ValueError("View ID cannot be empty")
        if not self.name:
            raise ValueError("View name cannot be empty")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("View dimensions must be positive")
    
    def get_transform_matrix(self) -> List[List[Decimal]]:
        """Get transformation matrix for the view."""
        # Convert rotation to radians
        angle_rad = self.rotation * Decimal(str(math.pi)) / Decimal("180")
        cos_angle = Decimal(str(math.cos(float(angle_rad))))
        sin_angle = Decimal(str(math.sin(float(angle_rad))))
        
        # Get scale factor
        if isinstance(self.config.scale, ViewScale):
            scale_factor = self._get_scale_factor(self.config.scale)
        else:
            scale_factor = self.config.scale
        
        return [
            [scale_factor * cos_angle, -scale_factor * sin_angle, self.origin.x],
            [scale_factor * sin_angle, scale_factor * cos_angle, self.origin.y],
            [Decimal("0"), Decimal("0"), Decimal("1")]
        ]
    
    def _get_scale_factor(self, scale: ViewScale) -> Decimal:
        """Get scale factor from ViewScale enum."""
        scale_map = {
            ViewScale.SCALE_1_1: Decimal("1"),
            ViewScale.SCALE_1_2: Decimal("0.5"),
            ViewScale.SCALE_1_5: Decimal("0.2"),
            ViewScale.SCALE_1_10: Decimal("0.1"),
            ViewScale.SCALE_2_1: Decimal("2"),
            ViewScale.SCALE_5_1: Decimal("5"),
            ViewScale.SCALE_10_1: Decimal("10")
        }
        return scale_map.get(scale, Decimal("1"))
    
    def transform_point(self, point: PrecisionPoint) -> PrecisionPoint:
        """Transform a point using the view's transformation."""
        matrix = self.get_transform_matrix()
        
        x = point.x * matrix[0][0] + point.y * matrix[0][1] + matrix[0][2]
        y = point.x * matrix[1][0] + point.y * matrix[1][1] + matrix[1][2]
        
        return PrecisionPoint(x, y, precision_level=point.precision_level)
    
    def is_point_in_view(self, point: PrecisionPoint) -> bool:
        """Check if a point is within the view boundaries."""
        transformed_point = self.transform_point(point)
        
        return (0 <= transformed_point.x <= self.width and 
                0 <= transformed_point.y <= self.height)
    
    def get_view_center(self) -> PrecisionPoint:
        """Get the center point of the view."""
        return PrecisionPoint(
            self.origin.x + self.width / 2,
            self.origin.y + self.height / 2,
            precision_level=self.origin.precision_level
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert view to dictionary representation."""
        return {
            "view_id": self.view_id,
            "name": self.name,
            "view_type": self.config.view_type.value,
            "scale": self.config.scale.value if isinstance(self.config.scale, ViewScale) else float(self.config.scale),
            "origin": self.origin.to_dict(),
            "width": float(self.width),
            "height": float(self.height),
            "rotation": float(self.rotation),
            "visible": self.visible,
            "locked": self.locked,
            "config": {
                "show_hidden_lines": self.config.show_hidden_lines,
                "show_center_lines": self.config.show_center_lines,
                "show_dimensions": self.config.show_dimensions,
                "show_annotations": self.config.show_annotations,
                "show_grid": self.config.show_grid,
                "show_axes": self.config.show_axes,
                "background_color": self.config.background_color,
                "border_color": self.config.border_color,
                "border_width": float(self.config.border_width)
            }
        }


class ViewGenerator:
    """Generates different types of drawing views."""
    
    def __init__(self):
        """Initialize view generator."""
        logger.info("View generator initialized")
    
    def generate_front_view(self, assembly_data: Dict[str, Any], 
                           config: ViewConfig) -> DrawingView:
        """Generate a front view of an assembly."""
        view = DrawingView(
            view_id="front_view",
            name="Front View",
            config=config
        )
        
        # Simplified front view generation
        # In practice, this would project 3D geometry to 2D
        view.content = {
            "type": "front_projection",
            "assembly_data": assembly_data,
            "projection_matrix": self._get_front_projection_matrix()
        }
        
        logger.debug("Generated front view")
        return view
    
    def generate_top_view(self, assembly_data: Dict[str, Any], 
                         config: ViewConfig) -> DrawingView:
        """Generate a top view of an assembly."""
        view = DrawingView(
            view_id="top_view",
            name="Top View",
            config=config
        )
        
        view.content = {
            "type": "top_projection",
            "assembly_data": assembly_data,
            "projection_matrix": self._get_top_projection_matrix()
        }
        
        logger.debug("Generated top view")
        return view
    
    def generate_side_view(self, assembly_data: Dict[str, Any], 
                          config: ViewConfig) -> DrawingView:
        """Generate a side view of an assembly."""
        view = DrawingView(
            view_id="side_view",
            name="Side View",
            config=config
        )
        
        view.content = {
            "type": "side_projection",
            "assembly_data": assembly_data,
            "projection_matrix": self._get_side_projection_matrix()
        }
        
        logger.debug("Generated side view")
        return view
    
    def generate_isometric_view(self, assembly_data: Dict[str, Any], 
                              config: ViewConfig) -> DrawingView:
        """Generate an isometric view of an assembly."""
        view = DrawingView(
            view_id="isometric_view",
            name="Isometric View",
            config=config
        )
        
        view.content = {
            "type": "isometric_projection",
            "assembly_data": assembly_data,
            "projection_matrix": self._get_isometric_projection_matrix()
        }
        
        logger.debug("Generated isometric view")
        return view
    
    def generate_section_view(self, assembly_data: Dict[str, Any], 
                            section_plane: Dict[str, Any], config: ViewConfig) -> DrawingView:
        """Generate a section view of an assembly."""
        view = DrawingView(
            view_id="section_view",
            name="Section View",
            config=config
        )
        
        view.content = {
            "type": "section_projection",
            "assembly_data": assembly_data,
            "section_plane": section_plane,
            "projection_matrix": self._get_section_projection_matrix(section_plane)
        }
        
        logger.debug("Generated section view")
        return view
    
    def _get_front_projection_matrix(self) -> List[List[Decimal]]:
        """Get front projection matrix."""
        return [
            [Decimal("1"), Decimal("0"), Decimal("0")],
            [Decimal("0"), Decimal("1"), Decimal("0")],
            [Decimal("0"), Decimal("0"), Decimal("0")]
        ]
    
    def _get_top_projection_matrix(self) -> List[List[Decimal]]:
        """Get top projection matrix."""
        return [
            [Decimal("1"), Decimal("0"), Decimal("0")],
            [Decimal("0"), Decimal("0"), Decimal("0")],
            [Decimal("0"), Decimal("1"), Decimal("0")]
        ]
    
    def _get_side_projection_matrix(self) -> List[List[Decimal]]:
        """Get side projection matrix."""
        return [
            [Decimal("0"), Decimal("0"), Decimal("0")],
            [Decimal("0"), Decimal("1"), Decimal("0")],
            [Decimal("1"), Decimal("0"), Decimal("0")]
        ]
    
    def _get_isometric_projection_matrix(self) -> List[List[Decimal]]:
        """Get isometric projection matrix."""
        # Standard isometric projection
        cos_30 = Decimal(str(math.cos(math.radians(30))))
        sin_30 = Decimal(str(math.sin(math.radians(30))))
        
        return [
            [cos_30, -sin_30, Decimal("0")],
            [sin_30, cos_30, Decimal("0")],
            [Decimal("0"), Decimal("0"), Decimal("0")]
        ]
    
    def _get_section_projection_matrix(self, section_plane: Dict[str, Any]) -> List[List[Decimal]]:
        """Get section projection matrix."""
        # Simplified section projection
        # In practice, this would be calculated based on the section plane
        return [
            [Decimal("1"), Decimal("0"), Decimal("0")],
            [Decimal("0"), Decimal("1"), Decimal("0")],
            [Decimal("0"), Decimal("0"), Decimal("0")]
        ]


class DrawingViewManager:
    """Main drawing view management system for CAD operations."""
    
    def __init__(self):
        """Initialize drawing view manager."""
        self.views: Dict[str, DrawingView] = {}
        self.view_generator = ViewGenerator()
        self.next_view_id = 1
        self.projection_type = ProjectionType.THIRD_ANGLE
        logger.info("Drawing view manager initialized")
    
    def create_view(self, name: str, view_type: ViewType, 
                   config: Optional[ViewConfig] = None) -> str:
        """Create a new drawing view."""
        view_id = f"view_{self.next_view_id}"
        
        if config is None:
            config = ViewConfig(view_type=view_type)
        
        view = DrawingView(
            view_id=view_id,
            name=name,
            config=config
        )
        
        self.views[view_id] = view
        self.next_view_id += 1
        
        logger.info(f"Created drawing view: {name} (ID: {view_id})")
        return view_id
    
    def generate_standard_views(self, assembly_data: Dict[str, Any]) -> Dict[str, str]:
        """Generate standard views (front, top, side) for an assembly."""
        view_ids = {}
        
        # Generate front view
        front_config = ViewConfig(view_type=ViewType.FRONT)
        front_view = self.view_generator.generate_front_view(assembly_data, front_config)
        front_view.view_id = f"front_{self.next_view_id}"
        self.views[front_view.view_id] = front_view
        view_ids["front"] = front_view.view_id
        self.next_view_id += 1
        
        # Generate top view
        top_config = ViewConfig(view_type=ViewType.TOP)
        top_view = self.view_generator.generate_top_view(assembly_data, top_config)
        top_view.view_id = f"top_{self.next_view_id}"
        self.views[top_view.view_id] = top_view
        view_ids["top"] = top_view.view_id
        self.next_view_id += 1
        
        # Generate side view
        side_config = ViewConfig(view_type=ViewType.SIDE)
        side_view = self.view_generator.generate_side_view(assembly_data, side_config)
        side_view.view_id = f"side_{self.next_view_id}"
        self.views[side_view.view_id] = side_view
        view_ids["side"] = side_view.view_id
        self.next_view_id += 1
        
        logger.info("Generated standard views for assembly")
        return view_ids
    
    def generate_isometric_view(self, assembly_data: Dict[str, Any]) -> str:
        """Generate an isometric view for an assembly."""
        isometric_config = ViewConfig(view_type=ViewType.ISOMETRIC)
        isometric_view = self.view_generator.generate_isometric_view(assembly_data, isometric_config)
        isometric_view.view_id = f"isometric_{self.next_view_id}"
        self.views[isometric_view.view_id] = isometric_view
        self.next_view_id += 1
        
        logger.info("Generated isometric view for assembly")
        return isometric_view.view_id
    
    def generate_section_view(self, assembly_data: Dict[str, Any], 
                            section_plane: Dict[str, Any]) -> str:
        """Generate a section view for an assembly."""
        section_config = ViewConfig(view_type=ViewType.SECTION)
        section_view = self.view_generator.generate_section_view(assembly_data, section_plane, section_config)
        section_view.view_id = f"section_{self.next_view_id}"
        self.views[section_view.view_id] = section_view
        self.next_view_id += 1
        
        logger.info("Generated section view for assembly")
        return section_view.view_id
    
    def get_view(self, view_id: str) -> Optional[DrawingView]:
        """Get a view by ID."""
        return self.views.get(view_id)
    
    def remove_view(self, view_id: str) -> bool:
        """Remove a view."""
        if view_id in self.views:
            del self.views[view_id]
            logger.info(f"Removed drawing view: {view_id}")
            return True
        return False
    
    def update_view_config(self, view_id: str, config: ViewConfig) -> bool:
        """Update view configuration."""
        view = self.views.get(view_id)
        if view:
            view.config = config
            logger.debug(f"Updated view configuration: {view_id}")
            return True
        return False
    
    def update_view_position(self, view_id: str, origin: PrecisionPoint) -> bool:
        """Update view position."""
        view = self.views.get(view_id)
        if view and not view.locked:
            view.origin = origin
            logger.debug(f"Updated view position: {view_id}")
            return True
        return False
    
    def update_view_scale(self, view_id: str, scale: Union[ViewScale, Decimal]) -> bool:
        """Update view scale."""
        view = self.views.get(view_id)
        if view and not view.locked:
            view.config.scale = scale
            logger.debug(f"Updated view scale: {view_id}")
            return True
        return False
    
    def get_views_by_type(self, view_type: ViewType) -> List[DrawingView]:
        """Get all views of a specific type."""
        return [view for view in self.views.values() if view.config.view_type == view_type]
    
    def get_visible_views(self) -> List[DrawingView]:
        """Get all visible views."""
        return [view for view in self.views.values() if view.visible]
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get drawing view manager statistics."""
        view_types = {}
        for view in self.views.values():
            view_type = view.config.view_type.value
            view_types[view_type] = view_types.get(view_type, 0) + 1
        
        return {
            "total_views": len(self.views),
            "visible_views": len(self.get_visible_views()),
            "view_types": view_types,
            "projection_type": self.projection_type.value
        }
    
    def export_data(self) -> Dict[str, Any]:
        """Export drawing view manager data."""
        return {
            "views": {
                view_id: view.to_dict()
                for view_id, view in self.views.items()
            },
            "projection_type": self.projection_type.value,
            "next_view_id": self.next_view_id
        }


# Factory functions for easy instantiation
def create_view_config(view_type: ViewType, scale: Union[ViewScale, Decimal] = ViewScale.SCALE_1_1,
                      show_hidden_lines: bool = True, show_center_lines: bool = True,
                      show_dimensions: bool = True) -> ViewConfig:
    """Create a view configuration."""
    return ViewConfig(
        view_type=view_type,
        scale=scale,
        show_hidden_lines=show_hidden_lines,
        show_center_lines=show_center_lines,
        show_dimensions=show_dimensions
    )


def create_drawing_view(view_id: str, name: str, view_type: ViewType,
                       config: Optional[ViewConfig] = None) -> DrawingView:
    """Create a drawing view."""
    if config is None:
        config = ViewConfig(view_type=view_type)
    
    return DrawingView(
        view_id=view_id,
        name=name,
        config=config
    )


def create_view_generator() -> ViewGenerator:
    """Create a new view generator."""
    return ViewGenerator()


def create_drawing_view_manager() -> DrawingViewManager:
    """Create a new drawing view manager."""
    return DrawingViewManager() 