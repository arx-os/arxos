"""
Dimensioning System for SVGX Engine

Provides CAD-style dimensioning including linear, radial, angular, aligned,
ordinate dimensioning and auto-dimensioning capabilities.

CTO Directives:
- Enterprise-grade dimensioning system
- Professional CAD dimensioning functionality
- Comprehensive dimension types
- Auto-dimensioning capabilities
- Dimension style management
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal
import logging

from .precision_system import PrecisionPoint, PrecisionLevel

logger = logging.getLogger(__name__)

class DimensionType(Enum):
    """Dimension Types"""
    LINEAR_HORIZONTAL = "linear_horizontal"
    LINEAR_VERTICAL = "linear_vertical"
    LINEAR_ALIGNED = "linear_aligned"
    RADIAL = "radial"
    DIAMETER = "diameter"
    ANGULAR = "angular"
    ORDINATE = "ordinate"
    LEADER = "leader"
    CHAIN = "chain"
    BASELINE = "baseline"

class DimensionStyle(Enum):
    """Dimension Style Types"""
    STANDARD = "standard"
    ARCHITECTURAL = "architectural"
    ENGINEERING = "engineering"
    METRIC = "metric"
    IMPERIAL = "imperial"
    CUSTOM = "custom"

@dataclass
class DimensionStyleConfig:
    """Dimension style configuration"""
    style_name: str
    text_height: Decimal = Decimal('2.5')  # mm
    text_color: str = "#000000"
    line_color: str = "#000000"
    line_width: Decimal = Decimal('0.25')  # mm
    arrow_size: Decimal = Decimal('2.0')  # mm
    extension_offset: Decimal = Decimal('1.0')  # mm
    text_offset: Decimal = Decimal('0.5')  # mm
    precision: int = 3  # Decimal places
    units: str = "mm"
    show_units: bool = True
    tolerance_plus: Optional[Decimal] = None
    tolerance_minus: Optional[Decimal] = None

@dataclass
class Dimension:
    """Base dimension class"""
    dimension_id: str
    dimension_type: DimensionType
    start_point: PrecisionPoint
    end_point: PrecisionPoint
    dimension_value: Decimal
    style: DimensionStyleConfig
    text_position: Optional[PrecisionPoint] = None
    leader_points: List[PrecisionPoint] = field(default_factory=list)
    tolerance_plus: Optional[Decimal] = None
    tolerance_minus: Optional[Decimal] = None
    precision_level: PrecisionLevel = PrecisionLevel.SUB_MILLIMETER

    def calculate_value(self) -> Decimal:
        """Calculate dimension value"""
        raise NotImplementedError

    def format_text(self) -> str:
        """Format dimension text"""
        raise NotImplementedError

    def get_leader_points(self) -> List[PrecisionPoint]:
        """Get leader points for dimension"""
        raise NotImplementedError

@dataclass
class LinearDimension(Dimension):
    """Linear dimension (horizontal, vertical, aligned)"""

    def calculate_value(self) -> Decimal:
        """Calculate linear dimension value"""
        dx = self.end_point.x - self.start_point.x
        dy = self.end_point.y - self.start_point.y
        return Decimal(str(math.sqrt(float(dx**2 + dy**2))))

    def format_text(self) -> str:
        """Format linear dimension text"""
        value = self.calculate_value()
        formatted_value = f"{float(value):.{self.style.precision}f}"

        if self.style.show_units:
            formatted_value += f" {self.style.units}"

        # Add tolerance if specified
        if self.tolerance_plus is not None or self.tolerance_minus is not None:
            tolerance_text = ""
            if self.tolerance_plus is not None:
                tolerance_text += f"+{float(self.tolerance_plus):.{self.style.precision}f}"
            if self.tolerance_minus is not None:
                tolerance_text += f"-{float(self.tolerance_minus):.{self.style.precision}f}"
            formatted_value += f" ±{tolerance_text}"

        return formatted_value

    def get_leader_points(self) -> List[PrecisionPoint]:
        """Get leader points for linear dimension"""
        # Calculate dimension line points
        mid_x = (self.start_point.x + self.end_point.x) / 2
        mid_y = (self.start_point.y + self.end_point.y) / 2

        # Calculate offset for dimension line
        offset_distance = self.style.extension_offset + self.style.text_offset

        # Calculate perpendicular direction
        dx = self.end_point.x - self.start_point.x
        dy = self.end_point.y - self.start_point.y
        length = Decimal(str(math.sqrt(float(dx**2 + dy**2))))

        if length > 0:
            perp_x = -dy / length
            perp_y = dx / length
        else:
            perp_x = Decimal('0')
            perp_y = Decimal('1')

        # Calculate leader points
        leader_start = PrecisionPoint(
            mid_x + perp_x * offset_distance,
            mid_y + perp_y * offset_distance
        )

        leader_end = PrecisionPoint(
            mid_x + perp_x * (offset_distance + self.style.text_offset),
            mid_y + perp_y * (offset_distance + self.style.text_offset)
        )

        return [leader_start, leader_end]

@dataclass
class RadialDimension(Dimension):
    """Radial dimension for circles and arcs"""

    def calculate_value(self) -> Decimal:
        """Calculate radial dimension value"""
        # For radial dimension, dimension_value is the radius
        return self.dimension_value

    def format_text(self) -> str:
        """Format radial dimension text"""
        radius = self.calculate_value()
        formatted_value = f"R{float(radius):.{self.style.precision}f}"

        if self.style.show_units:
            formatted_value += f" {self.style.units}"

        return formatted_value

    def get_leader_points(self) -> List[PrecisionPoint]:
        """Get leader points for radial dimension"""
        # Calculate leader from center to circumference
        center = self.start_point
        circumference_point = self.end_point

        # Calculate leader direction
        dx = circumference_point.x - center.x
        dy = circumference_point.y - center.y
        length = Decimal(str(math.sqrt(float(dx**2 + dy**2))))

        if length > 0:
            unit_x = dx / length
            unit_y = dy / length
        else:
            unit_x = Decimal('1')
            unit_y = Decimal('0')

        # Calculate leader points
        leader_start = PrecisionPoint(
            center.x + unit_x * (length + self.style.extension_offset),
            center.y + unit_y * (length + self.style.extension_offset)
        )

        leader_end = PrecisionPoint(
            center.x + unit_x * (length + self.style.extension_offset + self.style.text_offset),
            center.y + unit_y * (length + self.style.extension_offset + self.style.text_offset)
        )

        return [leader_start, leader_end]

@dataclass
class AngularDimension(Dimension):
    """Angular dimension for angles"""

    def calculate_value(self) -> Decimal:
        """Calculate angular dimension value"""
        # Calculate angle between three points
        # start_point = vertex, end_point = first line end, text_position = second line end
        if self.text_position is None:
            return self.dimension_value

        # Calculate vectors
        v1x = self.end_point.x - self.start_point.x
        v1y = self.end_point.y - self.start_point.y
        v2x = self.text_position.x - self.start_point.x
        v2y = self.text_position.y - self.start_point.y

        # Calculate angle
        dot_product = v1x * v2x + v1y * v2y
        mag1 = Decimal(str(math.sqrt(float(v1x**2 + v1y**2))))
        mag2 = Decimal(str(math.sqrt(float(v2x**2 + v2y**2))))

        if mag1 > 0 and mag2 > 0:
            cos_angle = dot_product / (mag1 * mag2)
            cos_angle = max(-1, min(1, float(cos_angle)))  # Clamp to [-1, 1]
            angle_rad = math.acos(cos_angle)
            return Decimal(str(math.degrees(angle_rad)))

        return self.dimension_value

    def format_text(self) -> str:
        """Format angular dimension text"""
        angle = self.calculate_value()
        formatted_value = f"{float(angle):.{self.style.precision}f}°"
        return formatted_value

    def get_leader_points(self) -> List[PrecisionPoint]:
        """Get leader points for angular dimension"""
        # Calculate arc center and radius for angular dimension
        center = self.start_point

        # Calculate arc radius (average distance from center)
        radius1 = center.distance_to(self.end_point)
        radius2 = center.distance_to(self.text_position) if self.text_position else radius1
        radius = (radius1 + radius2) / 2

        # Calculate arc points
        arc_center = center
        arc_radius = radius + self.style.extension_offset

        return [arc_center, PrecisionPoint(
            arc_center.x + arc_radius,
            arc_center.y
        )]

@dataclass
class OrdinateDimension(Dimension):
    """Ordinate dimension for coordinate measurements"""

    def calculate_value(self) -> Decimal:
        """Calculate ordinate dimension value"""
        if self.dimension_type == DimensionType.LINEAR_HORIZONTAL:
            return self.end_point.x - self.start_point.x
        else:  # LINEAR_VERTICAL
            return self.end_point.y - self.start_point.y

    def format_text(self) -> str:
        """Format ordinate dimension text"""
        value = self.calculate_value()
        formatted_value = f"{float(value):.{self.style.precision}f}"

        if self.style.show_units:
            formatted_value += f" {self.style.units}"

        return formatted_value

    def get_leader_points(self) -> List[PrecisionPoint]:
        """Get leader points for ordinate dimension"""
        # Ordinate dimensions have simple leader lines
        leader_start = self.start_point
        leader_end = PrecisionPoint(
            self.start_point.x + self.style.text_offset,
            self.start_point.y + self.style.text_offset
        )

        return [leader_start, leader_end]

class DimensionManager:
    """Manager for dimension operations"""

    def __init__(self):
        pass
    """
    Perform __init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.dimensions: List[Dimension] = []
        self.styles: Dict[str, DimensionStyleConfig] = {}
        self.default_style = self._create_default_style()

        logger.info("Dimension manager initialized")

    def _create_default_style(self) -> DimensionStyleConfig:
        """Create default dimension style"""
        return DimensionStyleConfig(
            style_name="default",
            text_height=Decimal('2.5'),
            text_color="#000000",
            line_color="#000000",
            line_width=Decimal('0.25'),
            arrow_size=Decimal('2.0'),
            extension_offset=Decimal('1.0'),
            text_offset=Decimal('0.5'),
            precision=3,
            units="mm",
            show_units=True
        )

    def add_style(self, style: DimensionStyleConfig):
        """Add dimension style"""
        self.styles[style.style_name] = style
        logger.info(f"Added dimension style: {style.style_name}")

    def get_style(self, style_name: str) -> DimensionStyleConfig:
        """Get dimension style"""
        return self.styles.get(style_name, self.default_style)

    def create_linear_dimension(self,
                               start_point: PrecisionPoint,
                               end_point: PrecisionPoint,
                               dimension_type: DimensionType = DimensionType.LINEAR_ALIGNED,
                               style_name: str = "default") -> LinearDimension:
        """Create linear dimension"""
        style = self.get_style(style_name)

        dimension = LinearDimension(
            dimension_id=f"linear_{len(self.dimensions)}",
            dimension_type=dimension_type,
            start_point=start_point,
            end_point=end_point,
            dimension_value=Decimal('0'),  # Will be calculated
            style=style
        )

        self.dimensions.append(dimension)
        logger.info(f"Created linear dimension: {dimension.dimension_id}")
        return dimension

    def create_radial_dimension(self,
                               center_point: PrecisionPoint,
                               circumference_point: PrecisionPoint,
                               radius: Decimal,
                               style_name: str = "default") -> RadialDimension:
        """Create radial dimension"""
        style = self.get_style(style_name)

        dimension = RadialDimension(
            dimension_id=f"radial_{len(self.dimensions)}",
            dimension_type=DimensionType.RADIAL,
            start_point=center_point,
            end_point=circumference_point,
            dimension_value=radius,
            style=style
        )

        self.dimensions.append(dimension)
        logger.info(f"Created radial dimension: {dimension.dimension_id}")
        return dimension

    def create_angular_dimension(self,
                                vertex_point: PrecisionPoint,
                                first_line_end: PrecisionPoint,
                                second_line_end: PrecisionPoint,
                                angle: Decimal,
                                style_name: str = "default") -> AngularDimension:
        """Create angular dimension"""
        style = self.get_style(style_name)

        dimension = AngularDimension(
            dimension_id=f"angular_{len(self.dimensions)}",
            dimension_type=DimensionType.ANGULAR,
            start_point=vertex_point,
            end_point=first_line_end,
            dimension_value=angle,
            style=style,
            text_position=second_line_end
        )

        self.dimensions.append(dimension)
        logger.info(f"Created angular dimension: {dimension.dimension_id}")
        return dimension

    def create_ordinate_dimension(self,
                                 start_point: PrecisionPoint,
                                 end_point: PrecisionPoint,
                                 dimension_type: DimensionType,
                                 style_name: str = "default") -> OrdinateDimension:
        """Create ordinate dimension"""
        style = self.get_style(style_name)

        dimension = OrdinateDimension(
            dimension_id=f"ordinate_{len(self.dimensions)}",
            dimension_type=dimension_type,
            start_point=start_point,
            end_point=end_point,
            dimension_value=Decimal('0'),  # Will be calculated
            style=style
        )

        self.dimensions.append(dimension)
        logger.info(f"Created ordinate dimension: {dimension.dimension_id}")
        return dimension

    def auto_dimension(self, entities: List[Any]) -> List[Dimension]:
        """Auto-dimension entities"""
        auto_dimensions = []

        for entity in entities:
            # Analyze entity and create appropriate dimensions
            if hasattr(entity, 'get_dimensions'):
                entity_dimensions = entity.get_dimensions()
                for dim_data in entity_dimensions:
                    dimension = self._create_dimension_from_data(dim_data)
                    if dimension:
                        auto_dimensions.append(dimension)

        logger.info(f"Auto-dimensioned {len(auto_dimensions)} dimensions")
        return auto_dimensions

    def _create_dimension_from_data(self, dim_data: Dict[str, Any]) -> Optional[Dimension]:
        """Create dimension from data"""
        try:
            dim_type = DimensionType(dim_data['type'])
            style_name = dim_data.get('style', 'default')

            if dim_type in [DimensionType.LINEAR_HORIZONTAL, DimensionType.LINEAR_VERTICAL, DimensionType.LINEAR_ALIGNED]:
                return self.create_linear_dimension(
                    dim_data['start_point'],
                    dim_data['end_point'],
                    dim_type,
                    style_name
                )
            elif dim_type == DimensionType.RADIAL:
                return self.create_radial_dimension(
                    dim_data['center_point'],
                    dim_data['circumference_point'],
                    dim_data['radius'],
                    style_name
                )
            elif dim_type == DimensionType.ANGULAR:
                return self.create_angular_dimension(
                    dim_data['vertex_point'],
                    dim_data['first_line_end'],
                    dim_data['second_line_end'],
                    dim_data['angle'],
                    style_name
                )

            return None

        except Exception as e:
            logger.error(f"Error creating dimension from data: {e}")
            return None

    def get_dimension_info(self) -> Dict[str, Any]:
        """Get dimension system information"""
        return {
            'total_dimensions': len(self.dimensions),
            'styles_count': len(self.styles),
            'default_style': self.default_style.style_name,
            'dimension_types': [d.dimension_type.value for d in self.dimensions]
        }

    def validate_system(self) -> bool:
        """Validate dimension system"""
        try:
            # Validate all dimensions
            for dimension in self.dimensions:
                if not hasattr(dimension, 'calculate_value'):
                    logger.error(f"Invalid dimension: {dimension.dimension_id}")
                    return False

            # Validate styles
            for style_name, style in self.styles.items():
                if style.text_height <= 0 or style.line_width <= 0:
                    logger.error(f"Invalid style: {style_name}")
                    return False

            logger.info("Dimension system validation passed")
            return True

        except Exception as e:
            logger.error(f"Dimension system validation failed: {e}")
            return False

# Global instance for easy access
dimension_manager = DimensionManager()
