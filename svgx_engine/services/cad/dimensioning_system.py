"""
Dimensioning System for Arxos CAD Components

This module provides CAD-style dimensioning functionality including:
- Linear dimensioning (horizontal and vertical)
- Radial dimensioning (circle and arc measurements)
- Angular dimensioning (angle measurements)
- Aligned dimensioning (aligned measurement lines)
- Ordinate dimensioning (ordinate dimension systems)
- Auto-dimensioning capabilities
- Dimension style management
"""

import math
import decimal
from typing import List, Dict, Optional, Union, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from .precision_drawing import PrecisionPoint, PrecisionVector, PrecisionLevel

logger = logging.getLogger(__name__)


class DimensionType(Enum):
    """Types of dimensions available."""
    LINEAR = "linear"
    RADIAL = "radial"
    ANGULAR = "angular"
    ALIGNED = "aligned"
    ORDINATE = "ordinate"
    DIAMETER = "diameter"
    ARC_LENGTH = "arc_length"
    CHORD_LENGTH = "chord_length"


class DimensionStyle(Enum):
    """Dimension display styles."""
    STANDARD = "standard"
    ARCHITECTURAL = "architectural"
    ENGINEERING = "engineering"
    METRIC = "metric"
    IMPERIAL = "imperial"


@dataclass
class DimensionStyle:
    """Dimension style configuration."""
    name: str
    dimension_type: DimensionType
    text_height: decimal.Decimal = decimal.Decimal('2.5')
    text_color: str = "#000000"
    line_color: str = "#000000"
    line_width: decimal.Decimal = decimal.Decimal('0.25')
    arrow_size: decimal.Decimal = decimal.Decimal('2.5')
    extension_offset: decimal.Decimal = decimal.Decimal('1.0')
    text_offset: decimal.Decimal = decimal.Decimal('1.0')
    precision: int = 2
    units: str = "mm"
    show_units: bool = True
    show_tolerance: bool = False
    tolerance_plus: decimal.Decimal = decimal.Decimal('0.0')
    tolerance_minus: decimal.Decimal = decimal.Decimal('0.0')


@dataclass
class Dimension:
    """Base dimension class."""
    dimension_type: DimensionType
    style: DimensionStyle
    measurement: decimal.Decimal
    precision: PrecisionLevel = PrecisionLevel.MICRO
    tolerance_plus: Optional[decimal.Decimal] = None
    tolerance_minus: Optional[decimal.Decimal] = None
    
    def get_display_text(self) -> str:
        """Get formatted dimension text."""
        formatted_value = f"{self.measurement:.{self.style.precision}f}"
        if self.style.show_units:
            formatted_value += f" {self.style.units}"
        
        if self.style.show_tolerance and (self.tolerance_plus or self.tolerance_minus):
            tolerance_text = ""
            if self.tolerance_plus:
                tolerance_text += f"+{self.tolerance_plus:.{self.style.precision}f}"
            if self.tolerance_minus:
                tolerance_text += f"-{self.tolerance_minus:.{self.style.precision}f}"
            formatted_value += f" ±{tolerance_text}"
        
        return formatted_value


@dataclass
class LinearDimension(Dimension):
    """Linear dimension between two points."""
    start_point: PrecisionPoint
    end_point: PrecisionPoint
    dimension_line_offset: decimal.Decimal = decimal.Decimal('10.0')
    text_position: Optional[PrecisionPoint] = None
    
    def __post_init__(self):
        """Initialize linear dimension."""
        self.dimension_type = DimensionType.LINEAR
        self.measurement = self.start_point.distance_to(self.end_point)
    
    def get_dimension_line_points(self) -> List[PrecisionPoint]:
        """Get points for dimension line."""
        # Calculate direction vector
        direction = PrecisionVector(
            self.end_point.x - self.start_point.x,
            self.end_point.y - self.start_point.y
        ).normalize()
        
        # Calculate perpendicular vector for offset
        perp_direction = PrecisionVector(-direction.dy, direction.dx)
        
        # Calculate offset points
        offset_start = PrecisionPoint(
            self.start_point.x + perp_direction.dx * self.dimension_line_offset,
            self.start_point.y + perp_direction.dy * self.dimension_line_offset
        )
        offset_end = PrecisionPoint(
            self.end_point.x + perp_direction.dx * self.dimension_line_offset,
            self.end_point.y + perp_direction.dy * self.dimension_line_offset
        )
        
        return [offset_start, offset_end]
    
    def get_extension_lines(self) -> List[Tuple[PrecisionPoint, PrecisionPoint]]:
        """Get extension lines from object to dimension line."""
        dim_line_points = self.get_dimension_line_points()
        
        extension_lines = [
            (self.start_point, dim_line_points[0]),
            (self.end_point, dim_line_points[1])
        ]
        
        return extension_lines
    
    def get_arrow_points(self) -> List[PrecisionPoint]:
        """Get arrow points for dimension line."""
        dim_line_points = self.get_dimension_line_points()
        start = dim_line_points[0]
        end = dim_line_points[1]
        
        # Calculate arrow direction
        direction = PrecisionVector(end.x - start.x, end.y - start.y).normalize()
        
        # Calculate arrow size
        arrow_length = self.style.arrow_size
        arrow_angle = decimal.Decimal(str(math.pi)) / 6  # 30 degrees
        
        # Calculate arrow points
        arrow_point1 = PrecisionPoint(
            end.x - arrow_length * math.cos(float(direction.angle_to(PrecisionVector(1, 0)) + arrow_angle)),
            end.y - arrow_length * math.sin(float(direction.angle_to(PrecisionVector(1, 0)) + arrow_angle))
        )
        arrow_point2 = PrecisionPoint(
            end.x - arrow_length * math.cos(float(direction.angle_to(PrecisionVector(1, 0)) - arrow_angle)),
            end.y - arrow_length * math.sin(float(direction.angle_to(PrecisionVector(1, 0)) - arrow_angle))
        )
        
        return [arrow_point1, arrow_point2]


@dataclass
class RadialDimension(Dimension):
    """Radial dimension for circles and arcs."""
    center_point: PrecisionPoint
    radius: decimal.Decimal
    angle: decimal.Decimal = decimal.Decimal('0.0')  # For arcs
    
    def __post_init__(self):
        """Initialize radial dimension."""
        self.dimension_type = DimensionType.RADIAL
        self.measurement = self.radius
    
    def get_dimension_line_points(self) -> List[PrecisionPoint]:
        """Get points for radial dimension line."""
        # Calculate point on circle
        point_on_circle = PrecisionPoint(
            self.center_point.x + self.radius * math.cos(float(self.angle)),
            self.center_point.y + self.radius * math.sin(float(self.angle))
        )
        
        # Calculate dimension line offset
        offset_distance = self.style.extension_offset
        
        # Calculate offset point
        direction = PrecisionVector(
            point_on_circle.x - self.center_point.x,
            point_on_circle.y - self.center_point.y
        ).normalize()
        
        offset_point = PrecisionPoint(
            point_on_circle.x + direction.dx * offset_distance,
            point_on_circle.y + direction.dy * offset_distance
        )
        
        return [self.center_point, point_on_circle, offset_point]
    
    def get_arrow_points(self) -> List[PrecisionPoint]:
        """Get arrow points for radial dimension."""
        dim_line_points = self.get_dimension_line_points()
        point_on_circle = dim_line_points[1]
        
        # Calculate arrow direction (from center to circle)
        direction = PrecisionVector(
            point_on_circle.x - self.center_point.x,
            point_on_circle.y - self.center_point.y
        ).normalize()
        
        # Calculate arrow size
        arrow_length = self.style.arrow_size
        arrow_angle = decimal.Decimal(str(math.pi)) / 6  # 30 degrees
        
        # Calculate arrow points
        arrow_point1 = PrecisionPoint(
            point_on_circle.x - arrow_length * math.cos(float(direction.angle_to(PrecisionVector(1, 0)) + arrow_angle)),
            point_on_circle.y - arrow_length * math.sin(float(direction.angle_to(PrecisionVector(1, 0)) + arrow_angle))
        )
        arrow_point2 = PrecisionPoint(
            point_on_circle.x - arrow_length * math.cos(float(direction.angle_to(PrecisionVector(1, 0)) - arrow_angle)),
            point_on_circle.y - arrow_length * math.sin(float(direction.angle_to(PrecisionVector(1, 0)) - arrow_angle))
        )
        
        return [arrow_point1, arrow_point2]


@dataclass
class AngularDimension(Dimension):
    """Angular dimension between three points."""
    center_point: PrecisionPoint
    start_point: PrecisionPoint
    end_point: PrecisionPoint
    arc_radius: decimal.Decimal = decimal.Decimal('20.0')
    
    def __post_init__(self):
        """Initialize angular dimension."""
        self.dimension_type = DimensionType.ANGULAR
        
        # Calculate angle between vectors
        vector1 = PrecisionVector(
            self.start_point.x - self.center_point.x,
            self.start_point.y - self.center_point.y
        )
        vector2 = PrecisionVector(
            self.end_point.x - self.center_point.x,
            self.end_point.y - self.center_point.y
        )
        
        self.measurement = vector1.angle_to(vector2)
    
    def get_arc_points(self) -> List[PrecisionPoint]:
        """Get points for angular dimension arc."""
        # Calculate unit vectors
        vector1 = PrecisionVector(
            self.start_point.x - self.center_point.x,
            self.start_point.y - self.center_point.y
        ).normalize()
        vector2 = PrecisionVector(
            self.end_point.x - self.center_point.x,
            self.end_point.y - self.center_point.y
        ).normalize()
        
        # Calculate arc points
        arc_points = []
        num_points = 20  # Number of points to approximate arc
        
        for i in range(num_points + 1):
            t = i / num_points
            angle = t * float(self.measurement)
            
            # Interpolate between vectors
            cos_angle = math.cos(angle)
            sin_angle = math.sin(angle)
            
            # Rotate vector1 by angle
            rotated_x = vector1.dx * cos_angle - vector1.dy * sin_angle
            rotated_y = vector1.dx * sin_angle + vector1.dy * cos_angle
            
            arc_point = PrecisionPoint(
                self.center_point.x + rotated_x * self.arc_radius,
                self.center_point.y + rotated_y * self.arc_radius
            )
            arc_points.append(arc_point)
        
        return arc_points
    
    def get_extension_lines(self) -> List[Tuple[PrecisionPoint, PrecisionPoint]]:
        """Get extension lines for angular dimension."""
        arc_points = self.get_arc_points()
        
        extension_lines = [
            (self.start_point, arc_points[0]),
            (self.end_point, arc_points[-1])
        ]
        
        return extension_lines


@dataclass
class AlignedDimension(Dimension):
    """Aligned dimension parallel to measured object."""
    start_point: PrecisionPoint
    end_point: PrecisionPoint
    dimension_line_offset: decimal.Decimal = decimal.Decimal('10.0')
    
    def __post_init__(self):
        """Initialize aligned dimension."""
        self.dimension_type = DimensionType.ALIGNED
        self.measurement = self.start_point.distance_to(self.end_point)
    
    def get_dimension_line_points(self) -> List[PrecisionPoint]:
        """Get points for aligned dimension line."""
        # Calculate direction vector
        direction = PrecisionVector(
            self.end_point.x - self.start_point.x,
            self.end_point.y - self.start_point.y
        ).normalize()
        
        # Calculate perpendicular vector for offset
        perp_direction = PrecisionVector(-direction.dy, direction.dx)
        
        # Calculate offset points
        offset_start = PrecisionPoint(
            self.start_point.x + perp_direction.dx * self.dimension_line_offset,
            self.start_point.y + perp_direction.dy * self.dimension_line_offset
        )
        offset_end = PrecisionPoint(
            self.end_point.x + perp_direction.dx * self.dimension_line_offset,
            self.end_point.y + perp_direction.dy * self.dimension_line_offset
        )
        
        return [offset_start, offset_end]


@dataclass
class OrdinateDimension(Dimension):
    """Ordinate dimension system."""
    origin_point: PrecisionPoint
    measured_point: PrecisionPoint
    is_x_coordinate: bool = True  # True for X, False for Y
    
    def __post_init__(self):
        """Initialize ordinate dimension."""
        self.dimension_type = DimensionType.ORDINATE
        
        if self.is_x_coordinate:
            self.measurement = self.measured_point.x - self.origin_point.x
        else:
            self.measurement = self.measured_point.y - self.origin_point.y
    
    def get_dimension_line_points(self) -> List[PrecisionPoint]:
        """Get points for ordinate dimension line."""
        if self.is_x_coordinate:
            # X coordinate - vertical line
            line_start = PrecisionPoint(self.measured_point.x, self.origin_point.y)
            line_end = PrecisionPoint(self.measured_point.x, self.measured_point.y)
        else:
            # Y coordinate - horizontal line
            line_start = PrecisionPoint(self.origin_point.x, self.measured_point.y)
            line_end = PrecisionPoint(self.measured_point.x, self.measured_point.y)
        
        return [line_start, line_end]


class DimensionManager:
    """Manages dimension styles and creation."""
    
    def __init__(self):
        """Initialize dimension manager."""
        self.styles: Dict[str, DimensionStyle] = {}
        self.dimensions: List[Dimension] = []
        self._create_default_styles()
    
    def _create_default_styles(self):
        """Create default dimension styles."""
        # Standard style
        self.styles["standard"] = DimensionStyle(
            name="standard",
            dimension_type=DimensionType.LINEAR,
            text_height=decimal.Decimal('2.5'),
            text_color="#000000",
            line_color="#000000",
            line_width=decimal.Decimal('0.25'),
            arrow_size=decimal.Decimal('2.5'),
            extension_offset=decimal.Decimal('1.0'),
            text_offset=decimal.Decimal('1.0'),
            precision=2,
            units="mm",
            show_units=True
        )
        
        # Architectural style
        self.styles["architectural"] = DimensionStyle(
            name="architectural",
            dimension_type=DimensionType.LINEAR,
            text_height=decimal.Decimal('3.0'),
            text_color="#000000",
            line_color="#000000",
            line_width=decimal.Decimal('0.35'),
            arrow_size=decimal.Decimal('3.0'),
            extension_offset=decimal.Decimal('1.5'),
            text_offset=decimal.Decimal('1.5'),
            precision=0,
            units="mm",
            show_units=True
        )
        
        # Engineering style
        self.styles["engineering"] = DimensionStyle(
            name="engineering",
            dimension_type=DimensionType.LINEAR,
            text_height=decimal.Decimal('2.0'),
            text_color="#000000",
            line_color="#000000",
            line_width=decimal.Decimal('0.18'),
            arrow_size=decimal.Decimal('2.0'),
            extension_offset=decimal.Decimal('0.8'),
            text_offset=decimal.Decimal('0.8'),
            precision=3,
            units="mm",
            show_units=True
        )
    
    def create_linear_dimension(self, start_point: PrecisionPoint, end_point: PrecisionPoint,
                               style_name: str = "standard") -> LinearDimension:
        """Create a linear dimension."""
        style = self.styles.get(style_name, self.styles["standard"])
        dimension = LinearDimension(
            dimension_type=DimensionType.LINEAR,
            style=style,
            measurement=start_point.distance_to(end_point),
            start_point=start_point,
            end_point=end_point
        )
        self.dimensions.append(dimension)
        return dimension
    
    def create_radial_dimension(self, center_point: PrecisionPoint, radius: decimal.Decimal,
                               angle: decimal.Decimal = decimal.Decimal('0.0'),
                               style_name: str = "standard") -> RadialDimension:
        """Create a radial dimension."""
        style = self.styles.get(style_name, self.styles["standard"])
        dimension = RadialDimension(
            dimension_type=DimensionType.RADIAL,
            style=style,
            measurement=radius,
            center_point=center_point,
            radius=radius,
            angle=angle
        )
        self.dimensions.append(dimension)
        return dimension
    
    def create_angular_dimension(self, center_point: PrecisionPoint, start_point: PrecisionPoint,
                                end_point: PrecisionPoint, style_name: str = "standard") -> AngularDimension:
        """Create an angular dimension."""
        style = self.styles.get(style_name, self.styles["standard"])
        dimension = AngularDimension(
            dimension_type=DimensionType.ANGULAR,
            style=style,
            measurement=decimal.Decimal('0.0'),  # Will be calculated in __post_init__
            center_point=center_point,
            start_point=start_point,
            end_point=end_point
        )
        self.dimensions.append(dimension)
        return dimension
    
    def create_aligned_dimension(self, start_point: PrecisionPoint, end_point: PrecisionPoint,
                                style_name: str = "standard") -> AlignedDimension:
        """Create an aligned dimension."""
        style = self.styles.get(style_name, self.styles["standard"])
        dimension = AlignedDimension(
            dimension_type=DimensionType.ALIGNED,
            style=style,
            measurement=start_point.distance_to(end_point),
            start_point=start_point,
            end_point=end_point
        )
        self.dimensions.append(dimension)
        return dimension
    
    def create_ordinate_dimension(self, origin_point: PrecisionPoint, measured_point: PrecisionPoint,
                                 is_x_coordinate: bool = True, style_name: str = "standard") -> OrdinateDimension:
        """Create an ordinate dimension."""
        style = self.styles.get(style_name, self.styles["standard"])
        dimension = OrdinateDimension(
            dimension_type=DimensionType.ORDINATE,
            style=style,
            measurement=decimal.Decimal('0.0'),  # Will be calculated in __post_init__
            origin_point=origin_point,
            measured_point=measured_point,
            is_x_coordinate=is_x_coordinate
        )
        self.dimensions.append(dimension)
        return dimension
    
    def add_style(self, style: DimensionStyle):
        """Add a custom dimension style."""
        self.styles[style.name] = style
    
    def get_style(self, name: str) -> Optional[DimensionStyle]:
        """Get a dimension style by name."""
        return self.styles.get(name)
    
    def get_all_styles(self) -> List[str]:
        """Get all available style names."""
        return list(self.styles.keys())
    
    def remove_dimension(self, dimension: Dimension):
        """Remove a dimension."""
        if dimension in self.dimensions:
            self.dimensions.remove(dimension)
    
    def get_dimensions(self) -> List[Dimension]:
        """Get all dimensions."""
        return self.dimensions.copy()
    
    def clear_dimensions(self):
        """Clear all dimensions."""
        self.dimensions.clear()


class AutoDimensioner:
    """Automatic dimensioning capabilities."""
    
    def __init__(self, dimension_manager: DimensionManager):
        """Initialize auto dimensioner."""
        self.dimension_manager = dimension_manager
    
    def auto_dimension_rectangle(self, points: List[PrecisionPoint], style_name: str = "standard"):
        """Automatically dimension a rectangle."""
        if len(points) != 4:
            raise ValueError("Rectangle must have exactly 4 points")
        
        # Sort points to get corners in order
        sorted_points = self._sort_rectangle_points(points)
        
        # Create linear dimensions for width and height
        width_dim = self.dimension_manager.create_linear_dimension(
            sorted_points[0], sorted_points[1], style_name
        )
        height_dim = self.dimension_manager.create_linear_dimension(
            sorted_points[1], sorted_points[2], style_name
        )
        
        return [width_dim, height_dim]
    
    def auto_dimension_circle(self, center_point: PrecisionPoint, radius: decimal.Decimal,
                             style_name: str = "standard"):
        """Automatically dimension a circle."""
        # Create diameter dimension
        diameter_dim = self.dimension_manager.create_radial_dimension(
            center_point, radius * 2, decimal.Decimal('0.0'), style_name
        )
        
        return [diameter_dim]
    
    def auto_dimension_polygon(self, points: List[PrecisionPoint], style_name: str = "standard"):
        """Automatically dimension a polygon."""
        dimensions = []
        
        # Create linear dimensions for each edge
        for i in range(len(points)):
            start_point = points[i]
            end_point = points[(i + 1) % len(points)]
            
            dim = self.dimension_manager.create_linear_dimension(
                start_point, end_point, style_name
            )
            dimensions.append(dim)
        
        return dimensions
    
    def _sort_rectangle_points(self, points: List[PrecisionPoint]) -> List[PrecisionPoint]:
        """Sort rectangle points in clockwise order starting from bottom-left."""
        # Find centroid
        centroid_x = sum(p.x for p in points) / len(points)
        centroid_y = sum(p.y for p in points) / len(points)
        centroid = PrecisionPoint(centroid_x, centroid_y)
        
        # Sort by angle from centroid
        def angle_from_centroid(point):
            return math.atan2(float(point.y - centroid.y), float(point.x - centroid.x))
        
        sorted_points = sorted(points, key=angle_from_centroid)
        return sorted_points


class DimensioningSystem:
    """
    Complete dimensioning system for CAD drawings.
    
    Provides comprehensive dimensioning functionality including:
    - Linear, radial, angular, aligned, and ordinate dimensions
    - Dimension style management
    - Auto-dimensioning capabilities
    - Dimension validation and optimization
    """
    
    def __init__(self):
        """Initialize dimensioning system."""
        self.dimension_manager = DimensionManager()
        self.auto_dimensioner = AutoDimensioner(self.dimension_manager)
    
    def create_linear_dimension(self, start_point: PrecisionPoint, end_point: PrecisionPoint,
                               style_name: str = "standard") -> LinearDimension:
        """Create a linear dimension."""
        return self.dimension_manager.create_linear_dimension(start_point, end_point, style_name)
    
    def create_radial_dimension(self, center_point: PrecisionPoint, radius: decimal.Decimal,
                               angle: decimal.Decimal = decimal.Decimal('0.0'),
                               style_name: str = "standard") -> RadialDimension:
        """Create a radial dimension."""
        return self.dimension_manager.create_radial_dimension(center_point, radius, angle, style_name)
    
    def create_angular_dimension(self, center_point: PrecisionPoint, start_point: PrecisionPoint,
                                end_point: PrecisionPoint, style_name: str = "standard") -> AngularDimension:
        """Create an angular dimension."""
        return self.dimension_manager.create_angular_dimension(center_point, start_point, end_point, style_name)
    
    def create_aligned_dimension(self, start_point: PrecisionPoint, end_point: PrecisionPoint,
                                style_name: str = "standard") -> AlignedDimension:
        """Create an aligned dimension."""
        return self.dimension_manager.create_aligned_dimension(start_point, end_point, style_name)
    
    def create_ordinate_dimension(self, origin_point: PrecisionPoint, measured_point: PrecisionPoint,
                                 is_x_coordinate: bool = True, style_name: str = "standard") -> OrdinateDimension:
        """Create an ordinate dimension."""
        return self.dimension_manager.create_ordinate_dimension(origin_point, measured_point, is_x_coordinate, style_name)
    
    def auto_dimension_rectangle(self, points: List[PrecisionPoint], style_name: str = "standard"):
        """Automatically dimension a rectangle."""
        return self.auto_dimensioner.auto_dimension_rectangle(points, style_name)
    
    def auto_dimension_circle(self, center_point: PrecisionPoint, radius: decimal.Decimal,
                             style_name: str = "standard"):
        """Automatically dimension a circle."""
        return self.auto_dimensioner.auto_dimension_circle(center_point, radius, style_name)
    
    def auto_dimension_polygon(self, points: List[PrecisionPoint], style_name: str = "standard"):
        """Automatically dimension a polygon."""
        return self.auto_dimensioner.auto_dimension_polygon(points, style_name)
    
    def add_style(self, style: DimensionStyle):
        """Add a custom dimension style."""
        self.dimension_manager.add_style(style)
    
    def get_style(self, name: str) -> Optional[DimensionStyle]:
        """Get a dimension style by name."""
        return self.dimension_manager.get_style(name)
    
    def get_all_styles(self) -> List[str]:
        """Get all available style names."""
        return self.dimension_manager.get_all_styles()
    
    def get_dimensions(self) -> List[Dimension]:
        """Get all dimensions."""
        return self.dimension_manager.get_dimensions()
    
    def remove_dimension(self, dimension: Dimension):
        """Remove a dimension."""
        self.dimension_manager.remove_dimension(dimension)
    
    def clear_dimensions(self):
        """Clear all dimensions."""
        self.dimension_manager.clear_dimensions()
    
    def get_dimension_statistics(self) -> Dict[str, Any]:
        """Get dimension system statistics."""
        dimensions = self.get_dimensions()
        type_counts = {}
        
        for dim in dimensions:
            dim_type = dim.dimension_type.value
            type_counts[dim_type] = type_counts.get(dim_type, 0) + 1
        
        return {
            "total_dimensions": len(dimensions),
            "dimension_types": type_counts,
            "available_styles": len(self.dimension_manager.styles),
            "style_names": self.get_all_styles()
        }


# Factory functions for easy usage
def create_dimensioning_system() -> DimensioningSystem:
    """Create a dimensioning system."""
    return DimensioningSystem()


def create_dimension_style(name: str, text_height: Union[float, decimal.Decimal] = 2.5,
                          precision: int = 2, units: str = "mm") -> DimensionStyle:
    """Create a dimension style."""
    return DimensionStyle(
        name=name,
        dimension_type=DimensionType.LINEAR,
        text_height=decimal.Decimal(str(text_height)),
        precision=precision,
        units=units
    ) 