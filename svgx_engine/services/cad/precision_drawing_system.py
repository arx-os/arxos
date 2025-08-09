"""
SVGX Engine - Precision Drawing System

This module implements the core precision drawing system for CAD-parity functionality,
providing sub-millimeter precision (0.001mm accuracy) with high-precision coordinate
systems and validation.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import math
import logging
from dataclasses import dataclass, field
from decimal import Decimal, getcontext
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

# Configure decimal precision for sub-millimeter accuracy
getcontext().prec = 6  # 0.001mm precision

logger = logging.getLogger(__name__)


class PrecisionLevel(Enum):
    """Precision levels for different CAD operations."""
    UI = "ui"  # 0.1mm precision for UI interactions
    EDIT = "edit"  # 0.01mm precision for editing operations
    COMPUTE = "compute"  # 0.001mm precision for computational accuracy


class PrecisionUnit(Enum):
    """Supported precision units."""
    MILLIMETERS = "mm"
    METERS = "m"
    INCHES = "in"
    FEET = "ft"


@dataclass
class PrecisionConfig:
    """Configuration for precision drawing system."""
    default_precision: PrecisionLevel = PrecisionLevel.COMPUTE
    ui_precision: Decimal = Decimal("0.1")  # 0.1mm
    edit_precision: Decimal = Decimal("0.01")  # 0.01mm
    compute_precision: Decimal = Decimal("0.001")  # 0.001mm
    display_precision: int = 3  # Decimal places for display
    validation_enabled: bool = True
    auto_rounding: bool = True


@dataclass
class PrecisionPoint:
    """High-precision point with sub-millimeter accuracy."""
    x: Decimal
    y: Decimal
    z: Optional[Decimal] = None
    precision_level: PrecisionLevel = PrecisionLevel.COMPUTE
    unit: PrecisionUnit = PrecisionUnit.MILLIMETERS

    def __post_init__(self):
        """Validate and normalize point coordinates."""
        if self.validation_enabled:
            self._validate_coordinates()
        if self.auto_rounding:
            self._round_to_precision()

    @property
def validation_enabled(self) -> bool:
        """Check if validation is enabled for this point."""
        return True

    def _validate_coordinates(self) -> None:
        """Validate coordinate values."""
        if not isinstance(self.x, (Decimal, int, float)):
            raise ValueError(f"Invalid x coordinate: {self.x}")
        if not isinstance(self.y, (Decimal, int, float)):
            raise ValueError(f"Invalid y coordinate: {self.y}")
        if self.z is not None and not isinstance(self.z, (Decimal, int, float)):
            raise ValueError(f"Invalid z coordinate: {self.z}")

    def _round_to_precision(self) -> None:
        """Round coordinates to appropriate precision level."""
        precision = self._get_precision_value()
        self.x = Decimal(str(self.x)).quantize(precision)
        self.y = Decimal(str(self.y)).quantize(precision)
        if self.z is not None:
            self.z = Decimal(str(self.z)).quantize(precision)

    def _get_precision_value(self) -> Decimal:
        """Get precision value for current level."""
        precision_map = {
            PrecisionLevel.UI: Decimal("0.1"),
            PrecisionLevel.EDIT: Decimal("0.01"),
            PrecisionLevel.COMPUTE: Decimal("0.001")
        }
        return precision_map.get(self.precision_level, Decimal("0.001")
    def to_dict(self) -> Dict[str, Any]:
        """Convert point to dictionary representation."""
        result = {
            "x": float(self.x),
            "y": float(self.y),
            "precision_level": self.precision_level.value,
            "unit": self.unit.value
        }
        if self.z is not None:
            result["z"] = float(self.z)
        return result

    @classmethod
def from_dict(cls, data: Dict[str, Any]) -> "PrecisionPoint":
        """Create point from dictionary representation."""
        return cls(
            x=Decimal(str(data["x"])),
            y=Decimal(str(data["y"])),
            z=Decimal(str(data["z"])) if "z" in data else None,
            precision_level=PrecisionLevel(data["precision_level"]),
            unit=PrecisionUnit(data["unit"])
    def distance_to(self, other: "PrecisionPoint") -> Decimal:
        """Calculate distance to another point."""
        dx = self.x - other.x
        dy = self.y - other.y
        if self.z is not None and other.z is not None:
            dz = self.z - other.z
            return (dx * dx + dy * dy + dz * dz).sqrt()
        return (dx * dx + dy * dy).sqrt()

    def __str__(self) -> str:
        """String representation with precision display."""
        precision = self._get_precision_value()
        x_str = f"{float(self.x):.{self.display_precision}f}"
        y_str = f"{float(self.y):.{self.display_precision}f}"
        if self.z is not None:
            z_str = f"{float(self.z):.{self.display_precision}f}"
            return f"Point({x_str}, {y_str}, {z_str}) {self.unit.value}"
        return f"Point({x_str}, {y_str}) {self.unit.value}"


@dataclass
class PrecisionVector:
    """High-precision vector with sub-millimeter accuracy."""
    dx: Decimal
    dy: Decimal
    dz: Optional[Decimal] = None
    precision_level: PrecisionLevel = PrecisionLevel.COMPUTE
    unit: PrecisionUnit = PrecisionUnit.MILLIMETERS

    def __post_init__(self):
        """Validate and normalize vector components."""
        if self.auto_rounding:
            self._round_to_precision()

    @property
def auto_rounding(self) -> bool:
        """Check if auto-rounding is enabled."""
        return True

    def _round_to_precision(self) -> None:
        """Round vector components to appropriate precision level."""
        precision = self._get_precision_value()
        self.dx = Decimal(str(self.dx)).quantize(precision)
        self.dy = Decimal(str(self.dy)).quantize(precision)
        if self.dz is not None:
            self.dz = Decimal(str(self.dz)).quantize(precision)

    def _get_precision_value(self) -> Decimal:
        """Get precision value for current level."""
        precision_map = {
            PrecisionLevel.UI: Decimal("0.1"),
            PrecisionLevel.EDIT: Decimal("0.01"),
            PrecisionLevel.COMPUTE: Decimal("0.001")
        }
        return precision_map.get(self.precision_level, Decimal("0.001")
    def magnitude(self) -> Decimal:
        """Calculate vector magnitude."""
        if self.dz is not None:
            return (self.dx * self.dx + self.dy * self.dy + self.dz * self.dz).sqrt()
        return (self.dx * self.dx + self.dy * self.dy).sqrt()

    def normalize(self) -> "PrecisionVector":
        """Normalize vector to unit length."""
        mag = self.magnitude()
        if mag == 0:
            return PrecisionVector(0, 0, 0, self.precision_level, self.unit)
        return PrecisionVector(
            self.dx / mag,
            self.dy / mag,
            self.dz / mag if self.dz is not None else None,
            self.precision_level,
            self.unit
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert vector to dictionary representation."""
        result = {
            "dx": float(self.dx),
            "dy": float(self.dy),
            "precision_level": self.precision_level.value,
            "unit": self.unit.value
        }
        if self.dz is not None:
            result["dz"] = float(self.dz)
        return result


class PrecisionCoordinateSystem:
    """High-precision coordinate system for CAD operations."""

    def __init__(self, config: Optional[PrecisionConfig] = None):
        """Initialize coordinate system with precision configuration."""
        self.config = config or PrecisionConfig()
        self.origin = PrecisionPoint(0, 0, 0, PrecisionLevel.COMPUTE)
        self.unit_vectors = {
            'x': PrecisionVector(1, 0, 0, PrecisionLevel.COMPUTE),
            'y': PrecisionVector(0, 1, 0, PrecisionLevel.COMPUTE),
            'z': PrecisionVector(0, 0, 1, PrecisionLevel.COMPUTE)
        }
        self.transform_matrix = self._create_identity_matrix()
        logger.info("Precision coordinate system initialized")

    def _create_identity_matrix(self) -> List[List[Decimal]]:
        """Create identity transformation matrix."""
        return [
            [Decimal("1"), Decimal("0"), Decimal("0"), Decimal("0")],
            [Decimal("0"), Decimal("1"), Decimal("0"), Decimal("0")],
            [Decimal("0"), Decimal("0"), Decimal("1"), Decimal("0")],
            [Decimal("0"), Decimal("0"), Decimal("0"), Decimal("1")]
        ]

    def set_precision_level(self, level: PrecisionLevel) -> None:
        """Set precision level for coordinate system."""
        self.config.default_precision = level
        logger.info(f"Precision level set to: {level.value}")

    def transform_point(self, point: PrecisionPoint) -> PrecisionPoint:
        """Transform point using current transformation matrix."""
        # Apply transformation matrix to point
        x = point.x * self.transform_matrix[0][0] + point.y * self.transform_matrix[0][1]
        y = point.x * self.transform_matrix[1][0] + point.y * self.transform_matrix[1][1]
        z = None
        if point.z is not None:
            z = point.x * self.transform_matrix[2][0] + point.y * self.transform_matrix[2][1] + point.z * self.transform_matrix[2][2]

        return PrecisionPoint(x, y, z, point.precision_level, point.unit)

    def validate_point(self, point: PrecisionPoint) -> bool:
        """Validate point coordinates."""
        try:
            point._validate_coordinates()
            return True
        except ValueError:
            return False

    def get_precision_value(self, level: PrecisionLevel) -> Decimal:
        """Get precision value for specified level."""
        precision_map = {
            PrecisionLevel.UI: self.config.ui_precision,
            PrecisionLevel.EDIT: self.config.edit_precision,
            PrecisionLevel.COMPUTE: self.config.compute_precision
        }
        return precision_map.get(level, self.config.compute_precision)


class PrecisionDrawingSystem:
    """Main precision drawing system for CAD operations."""

    def __init__(self, config: Optional[PrecisionConfig] = None):
        """Initialize precision drawing system."""
        self.config = config or PrecisionConfig()
        self.coordinate_system = PrecisionCoordinateSystem(config)
        self.active_precision_level = PrecisionLevel.COMPUTE
        self.points: List[PrecisionPoint] = []
        self.vectors: List[PrecisionVector] = []
        logger.info("Precision drawing system initialized")

    def set_precision_level(self, level: PrecisionLevel) -> None:
        """Set active precision level."""
        self.active_precision_level = level
        self.coordinate_system.set_precision_level(level)
        logger.info(f"Active precision level set to: {level.value}")

    def create_point(self, x: Union[float, Decimal], y: Union[float, Decimal],
                    z: Optional[Union[float, Decimal]] = None) -> PrecisionPoint:
        """Create a new precision point."""
        point = PrecisionPoint(
            Decimal(str(x)),
            Decimal(str(y)),
            Decimal(str(z)) if z is not None else None,
            self.active_precision_level
        )

        if self.config.validation_enabled:
            if not self.coordinate_system.validate_point(point):
                raise ValueError(f"Invalid point coordinates: {point}")

        self.points.append(point)
        logger.debug(f"Created precision point: {point}")
        return point

    def create_vector(self, dx: Union[float, Decimal], dy: Union[float, Decimal],
                     dz: Optional[Union[float, Decimal]] = None) -> PrecisionVector:
        """Create a new precision vector."""
        vector = PrecisionVector(
            Decimal(str(dx)),
            Decimal(str(dy)),
            Decimal(str(dz)) if dz is not None else None,
            self.active_precision_level
        )

        self.vectors.append(vector)
        logger.debug(f"Created precision vector: {vector}")
        return vector

    def calculate_distance(self, point1: PrecisionPoint, point2: PrecisionPoint) -> Decimal:
        """Calculate distance between two points."""
        return point1.distance_to(point2)

    def calculate_angle(self, vector1: PrecisionVector, vector2: PrecisionVector) -> Decimal:
        """Calculate angle between two vectors in radians."""
        dot_product = (vector1.dx * vector2.dx + vector1.dy * vector2.dy)
        if vector1.dz is not None and vector2.dz is not None:
            dot_product += vector1.dz * vector2.dz

        mag1 = vector1.magnitude()
        mag2 = vector2.magnitude()

        if mag1 == 0 or mag2 == 0:
            return Decimal("0")

        cos_angle = dot_product / (mag1 * mag2)
        # Clamp to valid range for acos
        cos_angle = max(Decimal("-1"), min(Decimal("1"), cos_angle))
        return Decimal(str(math.acos(float(cos_angle))))

    def round_to_precision(self, value: Union[float, Decimal],
                          level: Optional[PrecisionLevel] = None) -> Decimal:
        """Round value to specified precision level."""
        if level is None:
            level = self.active_precision_level

        precision = self.coordinate_system.get_precision_value(level)
        return Decimal(str(value)).quantize(precision)

    def validate_precision(self, value: Union[float, Decimal],
                          level: Optional[PrecisionLevel] = None) -> bool:
        """Validate if value meets precision requirements."""
        if level is None:
            level = self.active_precision_level

        precision = self.coordinate_system.get_precision_value(level)
        rounded_value = Decimal(str(value)).quantize(precision)
        return abs(Decimal(str(value)) - rounded_value) < precision

    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        return {
            "total_points": len(self.points),
            "total_vectors": len(self.vectors),
            "active_precision_level": self.active_precision_level.value,
            "config": {
                "ui_precision": float(self.config.ui_precision),
                "edit_precision": float(self.config.edit_precision),
                "compute_precision": float(self.config.compute_precision),
                "validation_enabled": self.config.validation_enabled,
                "auto_rounding": self.config.auto_rounding
            }
        }

    def export_data(self) -> Dict[str, Any]:
        """Export system data for persistence."""
        return {
            "points": [point.to_dict() for point in self.points],
            "vectors": [vector.to_dict() for vector in self.vectors],
            "active_precision_level": self.active_precision_level.value,
            "config": {
                "ui_precision": float(self.config.ui_precision),
                "edit_precision": float(self.config.edit_precision),
                "compute_precision": float(self.config.compute_precision),
                "validation_enabled": self.config.validation_enabled,
                "auto_rounding": self.config.auto_rounding
            }
        }

    def import_data(self, data: Dict[str, Any]) -> None:
        """Import system data from persistence."""
        self.points = [PrecisionPoint.from_dict(p) for p in data.get("points", [])]
        self.vectors = [PrecisionVector(**v) for v in data.get("vectors", [])]
        self.active_precision_level = PrecisionLevel(data.get("active_precision_level", "compute")
        if "config" in data:
            config_data = data["config"]
            self.config.ui_precision = Decimal(str(config_data.get("ui_precision", "0.1")))
            self.config.edit_precision = Decimal(str(config_data.get("edit_precision", "0.01")))
            self.config.compute_precision = Decimal(str(config_data.get("compute_precision", "0.001")))
            self.config.validation_enabled = config_data.get("validation_enabled", True)
            self.config.auto_rounding = config_data.get("auto_rounding", True)

        logger.info("Precision drawing system data imported successfully")


# Factory functions for easy instantiation
def create_precision_drawing_system(config: Optional[PrecisionConfig] = None) -> PrecisionDrawingSystem:
    """Create a new precision drawing system instance."""
    return PrecisionDrawingSystem(config)


def create_precision_config(ui_precision: float = 0.1, edit_precision: float = 0.01,
                          compute_precision: float = 0.001, validation_enabled: bool = True,
                          auto_rounding: bool = True) -> PrecisionConfig:
    """Create a precision configuration."""
    return PrecisionConfig(
        ui_precision=Decimal(str(ui_precision)),
        edit_precision=Decimal(str(edit_precision)),
        compute_precision=Decimal(str(compute_precision)),
        validation_enabled=validation_enabled,
        auto_rounding=auto_rounding
    )
