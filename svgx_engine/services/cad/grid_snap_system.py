"""
Grid and Snap System for Arxos CAD Components

This module provides professional CAD snapping functionality including:
- Configurable grid spacing and origin
- Grid snapping with tolerance settings
- Object snapping (endpoints, midpoints, intersections)
- Angle snapping for precise alignment
- Visual grid and snap feedback
"""

import math
import decimal
from typing import List, Dict, Optional, Union, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from .precision_drawing import PrecisionPoint, PrecisionVector, PrecisionLevel

logger = logging.getLogger(__name__)


class SnapType(Enum):
    """Types of snapping available."""

    GRID = "grid"
    ENDPOINT = "endpoint"
    MIDPOINT = "midpoint"
    INTERSECTION = "intersection"
    CENTER = "center"
    TANGENT = "tangent"
    PERPENDICULAR = "perpendicular"
    PARALLEL = "parallel"
    ANGLE = "angle"
    NEAREST = "nearest"


class GridStyle(Enum):
    """Grid display styles."""

    DOTS = "dots"
    LINES = "lines"
    CROSSHAIR = "crosshair"
    NONE = "none"


@dataclass
class GridSettings:
    """Grid configuration settings."""

    enabled: bool = True
    visible: bool = True
    spacing: decimal.Decimal = decimal.Decimal("10.0")
    origin_x: decimal.Decimal = decimal.Decimal("0.0")
    origin_y: decimal.Decimal = decimal.Decimal("0.0")
    style: GridStyle = GridStyle.LINES
    color: str = "#CCCCCC"
    opacity: float = 0.5
    major_lines: int = 5  # Every Nth line is major
    snap_tolerance: decimal.Decimal = decimal.Decimal("5.0")


@dataclass
class SnapSettings:
    """Snap configuration settings."""

    enabled: bool = True
    snap_types: Set[SnapType] = field(
        default_factory=lambda: {
            SnapType.GRID,
            SnapType.ENDPOINT,
            SnapType.MIDPOINT,
            SnapType.INTERSECTION,
        }
    )
    tolerance: decimal.Decimal = decimal.Decimal("5.0")
    angle_snap: decimal.Decimal = decimal.Decimal("15.0")  # Degrees
    visual_feedback: bool = True
    magnetic_snap: bool = True  # Snap to nearest point automatically


@dataclass
class SnapPoint:
    """A snap point with type and position."""

    position: PrecisionPoint
    snap_type: SnapType
    entity: Optional[Any] = None
    distance: decimal.Decimal = decimal.Decimal("0.0")
    priority: int = 0  # Higher priority points are preferred

    def __lt__(self, other: "SnapPoint") -> bool:
        """Compare snap points by priority and distance."""
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.distance < other.distance


class GridSystem:
    """Grid system for CAD drawings."""

    def __init__(self, settings: Optional[GridSettings] = None):
        """
        Initialize grid system.

        Args:
            settings: Grid configuration settings
        """
        self.settings = settings or GridSettings()
        self.major_spacing = self.settings.spacing * self.settings.major_lines

    def snap_to_grid(self, point: PrecisionPoint) -> PrecisionPoint:
        """
        Snap a point to the nearest grid intersection.

        Args:
            point: Point to snap

        Returns:
            Snapped point
        """
        if not self.settings.enabled:
            return point

        # Calculate grid coordinates
        grid_x = (point.x - self.settings.origin_x) / self.settings.spacing
        grid_y = (point.y - self.settings.origin_y) / self.settings.spacing

        # Round to nearest grid intersection
        snapped_grid_x = round(grid_x)
        snapped_grid_y = round(grid_y)

        # Convert back to world coordinates
        snapped_x = self.settings.origin_x + snapped_grid_x * self.settings.spacing
        snapped_y = self.settings.origin_y + snapped_grid_y * self.settings.spacing

        return PrecisionPoint(snapped_x, snapped_y, point.precision)

    def get_grid_lines(
        self, bounds: Tuple[PrecisionPoint, PrecisionPoint]
    ) -> List[Tuple[PrecisionPoint, PrecisionPoint]]:
        """
        Get grid lines within specified bounds.

        Args:
            bounds: (min_point, max_point) defining the area

        Returns:
            List of (start_point, end_point) tuples for grid lines
        """
        if not self.settings.visible:
            return []

        min_point, max_point = bounds
        lines = []

        # Calculate grid range
        start_x = (min_point.x - self.settings.origin_x) // self.settings.spacing
        end_x = (max_point.x - self.settings.origin_x) // self.settings.spacing + 1
        start_y = (min_point.y - self.settings.origin_y) // self.settings.spacing
        end_y = (max_point.y - self.settings.origin_y) // self.settings.spacing + 1

        # Generate vertical lines
        for i in range(int(start_x), int(end_x) + 1):
            x = self.settings.origin_x + i * self.settings.spacing
            if min_point.x <= x <= max_point.x:
                start_point = PrecisionPoint(x, min_point.y)
                end_point = PrecisionPoint(x, max_point.y)
                lines.append((start_point, end_point))

        # Generate horizontal lines
        for i in range(int(start_y), int(end_y) + 1):
            y = self.settings.origin_y + i * self.settings.spacing
            if min_point.y <= y <= max_point.y:
                start_point = PrecisionPoint(min_point.x, y)
                end_point = PrecisionPoint(max_point.x, y)
                lines.append((start_point, end_point))

        return lines

    def is_major_line(self, coordinate: decimal.Decimal, is_horizontal: bool) -> bool:
        """
        Check if a grid line is a major line.

        Args:
            coordinate: Grid coordinate
            is_horizontal: True for horizontal lines, False for vertical

        Returns:
            True if this is a major line
        """
        if is_horizontal:
            grid_coord = (coordinate - self.settings.origin_y) / self.settings.spacing
        else:
            grid_coord = (coordinate - self.settings.origin_x) / self.settings.spacing

        return abs(grid_coord) % self.settings.major_lines == 0

    def update_settings(self, settings: GridSettings):
        """Update grid settings."""
        self.settings = settings
        self.major_spacing = self.settings.spacing * self.settings.major_lines


class ObjectSnapper:
    """Object snapping functionality."""

    def __init__(self, settings: Optional[SnapSettings] = None):
        """
        Initialize object snapper.

        Args:
            settings: Snap configuration settings
        """
        self.settings = settings or SnapSettings()
        self.entities: List[Any] = []

    def add_entity(self, entity: Any):
        """Add an entity for snapping."""
        self.entities.append(entity)

    def remove_entity(self, entity: Any):
        """Remove an entity from snapping."""
        if entity in self.entities:
            self.entities.remove(entity)

    def find_snap_points(self, cursor_point: PrecisionPoint) -> List[SnapPoint]:
        """
        Find all snap points near the cursor.

        Args:
            cursor_point: Current cursor position

        Returns:
            List of snap points sorted by priority and distance
        """
        if not self.settings.enabled:
            return []

        snap_points = []

        for entity in self.entities:
            entity_snaps = self._get_entity_snap_points(entity, cursor_point)
            snap_points.extend(entity_snaps)

        # Sort by priority and distance
        snap_points.sort()

        return snap_points

    def _get_entity_snap_points(
        self, entity: Any, cursor_point: PrecisionPoint
    ) -> List[SnapPoint]:
        """Get snap points for a specific entity."""
        snap_points = []

        # Endpoint snapping
        if SnapType.ENDPOINT in self.settings.snap_types:
            endpoints = self._get_endpoints(entity)
            for endpoint in endpoints:
                distance = cursor_point.distance_to(endpoint)
                if distance <= self.settings.tolerance:
                    snap_points.append(
                        SnapPoint(
                            position=endpoint,
                            snap_type=SnapType.ENDPOINT,
                            entity=entity,
                            distance=distance,
                            priority=5,
                        )
                    )

        # Midpoint snapping
        if SnapType.MIDPOINT in self.settings.snap_types:
            midpoints = self._get_midpoints(entity)
            for midpoint in midpoints:
                distance = cursor_point.distance_to(midpoint)
                if distance <= self.settings.tolerance:
                    snap_points.append(
                        SnapPoint(
                            position=midpoint,
                            snap_type=SnapType.MIDPOINT,
                            entity=entity,
                            distance=distance,
                            priority=4,
                        )
                    )

        # Center snapping
        if SnapType.CENTER in self.settings.snap_types:
            centers = self._get_centers(entity)
            for center in centers:
                distance = cursor_point.distance_to(center)
                if distance <= self.settings.tolerance:
                    snap_points.append(
                        SnapPoint(
                            position=center,
                            snap_type=SnapType.CENTER,
                            entity=entity,
                            distance=distance,
                            priority=3,
                        )
                    )

        # Tangent snapping
        if SnapType.TANGENT in self.settings.snap_types:
            tangents = self._get_tangent_points(entity, cursor_point)
            for tangent in tangents:
                distance = cursor_point.distance_to(tangent)
                if distance <= self.settings.tolerance:
                    snap_points.append(
                        SnapPoint(
                            position=tangent,
                            snap_type=SnapType.TANGENT,
                            entity=entity,
                            distance=distance,
                            priority=2,
                        )
                    )

        return snap_points

    def _get_endpoints(self, entity: Any) -> List[PrecisionPoint]:
        """Get endpoints of an entity."""
        endpoints = []

        if hasattr(entity, "start") and hasattr(entity, "end"):
            # Line entity
            endpoints.append(PrecisionPoint(entity.start.x, entity.start.y))
            endpoints.append(PrecisionPoint(entity.end.x, entity.end.y))
        elif hasattr(entity, "points"):
            # Polyline entity
            for point in entity.points:
                endpoints.append(PrecisionPoint(point.x, point.y))
        elif hasattr(entity, "center") and hasattr(entity, "radius"):
            # Circle entity - no endpoints, but could snap to quadrants
            center = PrecisionPoint(entity.center.x, entity.center.y)
            radius = entity.radius
            # Add quadrant points
            endpoints.extend(
                [
                    PrecisionPoint(center.x + radius, center.y),
                    PrecisionPoint(center.x - radius, center.y),
                    PrecisionPoint(center.x, center.y + radius),
                    PrecisionPoint(center.x, center.y - radius),
                ]
            )

        return endpoints

    def _get_midpoints(self, entity: Any) -> List[PrecisionPoint]:
        """Get midpoints of an entity."""
        midpoints = []

        if hasattr(entity, "start") and hasattr(entity, "end"):
            # Line entity
            mid_x = (entity.start.x + entity.end.x) / 2
            mid_y = (entity.start.y + entity.end.y) / 2
            midpoints.append(PrecisionPoint(mid_x, mid_y))
        elif hasattr(entity, "points") and len(entity.points) > 1:
            # Polyline entity - midpoints of segments
            for i in range(len(entity.points) - 1):
                p1 = entity.points[i]
                p2 = entity.points[i + 1]
                mid_x = (p1.x + p2.x) / 2
                mid_y = (p1.y + p2.y) / 2
                midpoints.append(PrecisionPoint(mid_x, mid_y))

        return midpoints

    def _get_centers(self, entity: Any) -> List[PrecisionPoint]:
        """Get centers of an entity."""
        centers = []

        if hasattr(entity, "center"):
            # Circle or arc entity
            centers.append(PrecisionPoint(entity.center.x, entity.center.y))
        elif hasattr(entity, "points") and len(entity.points) > 2:
            # Polygon entity - calculate centroid
            total_x = sum(p.x for p in entity.points)
            total_y = sum(p.y for p in entity.points)
            center_x = total_x / len(entity.points)
            center_y = total_y / len(entity.points)
            centers.append(PrecisionPoint(center_x, center_y))

        return centers

    def _get_tangent_points(
        self, entity: Any, cursor_point: PrecisionPoint
    ) -> List[PrecisionPoint]:
        """Get tangent points for an entity from cursor position."""
        tangent_points = []

        if hasattr(entity, "center") and hasattr(entity, "radius"):
            # Circle entity
            center = PrecisionPoint(entity.center.x, entity.center.y)
            radius = entity.radius

            # Calculate tangent points
            dx = cursor_point.x - center.x
            dy = cursor_point.y - center.y
            distance_sq = dx * dx + dy * dy

            if distance_sq > radius * radius:
                # Point is outside circle, calculate tangent points
                distance = distance_sq.sqrt()
                if distance > 0:
                    # Calculate tangent points
                    angle = math.atan2(dy, dx)
                    tangent_angle = math.asin(radius / distance)

                    # Two tangent points
                    angle1 = angle + tangent_angle
                    angle2 = angle - tangent_angle

                    tangent_points.append(
                        PrecisionPoint(
                            center.x + radius * math.cos(angle1),
                            center.y + radius * math.sin(angle1),
                        )
                    )
                    tangent_points.append(
                        PrecisionPoint(
                            center.x + radius * math.cos(angle2),
                            center.y + radius * math.sin(angle2),
                        )
                    )

        return tangent_points

    def update_settings(self, settings: SnapSettings):
        """Update snap settings."""
        self.settings = settings


class AngleSnapper:
    """Angle snapping functionality."""

    def __init__(self, angle_snap: decimal.Decimal = decimal.Decimal("15.0")):
        """
        Initialize angle snapper.

        Args:
            angle_snap: Angle snap increment in degrees
        """
        self.angle_snap = angle_snap
        self.angle_snap_radians = angle_snap * decimal.Decimal(str(math.pi)) / 180

    def snap_angle(self, angle: decimal.Decimal) -> decimal.Decimal:
        """
        Snap an angle to the nearest snap increment.

        Args:
            angle: Angle in radians

        Returns:
            Snapped angle in radians
        """
        # Convert to degrees for easier snapping
        angle_degrees = angle * 180 / decimal.Decimal(str(math.pi))

        # Snap to nearest increment
        snapped_degrees = round(angle_degrees / float(self.angle_snap)) * float(
            self.angle_snap
        )

        # Convert back to radians
        return (
            decimal.Decimal(str(snapped_degrees)) * decimal.Decimal(str(math.pi)) / 180
        )

    def get_snap_angles(self, base_angle: decimal.Decimal) -> List[decimal.Decimal]:
        """
        Get available snap angles from a base angle.

        Args:
            base_angle: Base angle in radians

        Returns:
            List of snap angles in radians
        """
        angles = []
        base_degrees = base_angle * 180 / decimal.Decimal(str(math.pi))

        # Generate snap angles around base angle
        for i in range(-4, 5):  # 9 angles total
            snap_angle = base_degrees + i * float(self.angle_snap)
            angles.append(
                decimal.Decimal(str(snap_angle)) * decimal.Decimal(str(math.pi)) / 180
            )

        return angles


class GridSnapSystem:
    """
    Complete grid and snap system for CAD drawings.

    Provides comprehensive grid and snapping functionality including:
    - Grid display and snapping
    - Object snapping (endpoints, midpoints, centers, tangents)
    - Angle snapping for precise alignment
    - Visual feedback and magnetic snapping
    """

    def __init__(
        self,
        grid_settings: Optional[GridSettings] = None,
        snap_settings: Optional[SnapSettings] = None,
    ):
        """
        Initialize grid and snap system.

        Args:
            grid_settings: Grid configuration settings
            snap_settings: Snap configuration settings
        """
        self.grid_system = GridSystem(grid_settings)
        self.object_snapper = ObjectSnapper(snap_settings)
        self.angle_snapper = AngleSnapper(
            snap_settings.angle_snap if snap_settings else decimal.Decimal("15.0")
        )

        self.last_snap_point: Optional[SnapPoint] = None
        self.snap_history: List[SnapPoint] = []

    def snap_point(
        self,
        point: PrecisionPoint,
        snap_to_grid: bool = True,
        snap_to_objects: bool = True,
        snap_to_angles: bool = True,
    ) -> PrecisionPoint:
        """
        Snap a point to grid, objects, and angles.

        Args:
            point: Point to snap
            snap_to_grid: Whether to snap to grid
            snap_to_objects: Whether to snap to objects
            snap_to_angles: Whether to snap to angles

        Returns:
            Snapped point
        """
        snapped_point = point
        best_snap_point: Optional[SnapPoint] = None

        # Grid snapping
        if snap_to_grid and self.grid_system.settings.enabled:
            grid_snapped = self.grid_system.snap_to_grid(point)
            if grid_snapped != point:
                snapped_point = grid_snapped
                best_snap_point = SnapPoint(
                    position=grid_snapped,
                    snap_type=SnapType.GRID,
                    distance=point.distance_to(grid_snapped),
                    priority=1,
                )

        # Object snapping
        if snap_to_objects and self.object_snapper.settings.enabled:
            snap_points = self.object_snapper.find_snap_points(point)
            if snap_points:
                best_object_snap = snap_points[0]
                if best_snap_point is None or best_object_snap < best_snap_point:
                    snapped_point = best_object_snap.position
                    best_snap_point = best_object_snap

        # Angle snapping (for line drawing)
        if snap_to_angles and self.object_snapper.settings.enabled:
            # This would be used when drawing lines to snap to angle increments
            pass

        # Update snap history
        if best_snap_point:
            self.last_snap_point = best_snap_point
            self.snap_history.append(best_snap_point)
            # Keep only last 10 snap points
            if len(self.snap_history) > 10:
                self.snap_history.pop(0)

        return snapped_point

    def get_snap_feedback(self, cursor_point: PrecisionPoint) -> Dict[str, Any]:
        """
        Get visual feedback for snapping.

        Args:
            cursor_point: Current cursor position

        Returns:
            Dictionary with snap feedback information
        """
        feedback = {
            "snap_points": [],
            "grid_lines": [],
            "snap_type": None,
            "snap_position": None,
            "magnetic": False,
        }

        # Get object snap points
        if self.object_snapper.settings.enabled:
            snap_points = self.object_snapper.find_snap_points(cursor_point)
            if snap_points:
                best_snap = snap_points[0]
                feedback["snap_points"] = [
                    sp.position for sp in snap_points[:3]
                ]  # Top 3
                feedback["snap_type"] = best_snap.snap_type.value
                feedback["snap_position"] = best_snap.position
                feedback["magnetic"] = self.object_snapper.settings.magnetic_snap

        # Get grid lines for display
        if self.grid_system.settings.visible:
            # Calculate display bounds (simplified)
            margin = 100  # pixels
            min_point = PrecisionPoint(cursor_point.x - margin, cursor_point.y - margin)
            max_point = PrecisionPoint(cursor_point.x + margin, cursor_point.y + margin)
            feedback["grid_lines"] = self.grid_system.get_grid_lines(
                (min_point, max_point)
            )

        return feedback

    def add_entity(self, entity: Any):
        """Add an entity for snapping."""
        self.object_snapper.add_entity(entity)

    def remove_entity(self, entity: Any):
        """Remove an entity from snapping."""
        self.object_snapper.remove_entity(entity)

    def update_grid_settings(self, settings: GridSettings):
        """Update grid settings."""
        self.grid_system.update_settings(settings)

    def update_snap_settings(self, settings: SnapSettings):
        """Update snap settings."""
        self.object_snapper.update_settings(settings)
        self.angle_snapper = AngleSnapper(settings.angle_snap)

    def get_snap_statistics(self) -> Dict[str, Any]:
        """Get snap system statistics."""
        return {
            "total_entities": len(self.object_snapper.entities),
            "snap_history_count": len(self.snap_history),
            "last_snap_type": (
                self.last_snap_point.snap_type.value if self.last_snap_point else None
            ),
            "grid_enabled": self.grid_system.settings.enabled,
            "snap_enabled": self.object_snapper.settings.enabled,
            "active_snap_types": [
                st.value for st in self.object_snapper.settings.snap_types
            ],
        }

    def clear_snap_history(self):
        """Clear snap history."""
        self.snap_history.clear()
        self.last_snap_point = None


# Factory functions for easy usage
def create_grid_snap_system(
    grid_settings: Optional[GridSettings] = None,
    snap_settings: Optional[SnapSettings] = None,
) -> GridSnapSystem:
    """Create a grid and snap system."""
    return GridSnapSystem(grid_settings, snap_settings)


def create_grid_settings(
    spacing: Union[float, decimal.Decimal] = 10.0,
    origin_x: Union[float, decimal.Decimal] = 0.0,
    origin_y: Union[float, decimal.Decimal] = 0.0,
    enabled: bool = True,
    visible: bool = True,
) -> GridSettings:
    """Create grid settings."""
    return GridSettings(
        enabled=enabled,
        visible=visible,
        spacing=decimal.Decimal(str(spacing)),
        origin_x=decimal.Decimal(str(origin_x)),
        origin_y=decimal.Decimal(str(origin_y)),
    )


def create_snap_settings(
    enabled: bool = True,
    tolerance: Union[float, decimal.Decimal] = 5.0,
    angle_snap: Union[float, decimal.Decimal] = 15.0,
    snap_types: Optional[Set[SnapType]] = None,
) -> SnapSettings:
    """Create snap settings."""
    if snap_types is None:
        snap_types = {
            SnapType.GRID,
            SnapType.ENDPOINT,
            SnapType.MIDPOINT,
            SnapType.INTERSECTION,
        }

    return SnapSettings(
        enabled=enabled,
        snap_types=snap_types,
        tolerance=decimal.Decimal(str(tolerance)),
        angle_snap=decimal.Decimal(str(angle_snap)),
    )
