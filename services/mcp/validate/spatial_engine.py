"""
Spatial Relationship Engine for MCP Validation

This module provides advanced spatial relationship calculations and validation
for building objects including distance calculations, adjacency detection,
and spatial constraint validation.
"""

import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from models.mcp_models import BuildingObject

logger = logging.getLogger(__name__)


@dataclass
class SpatialRelationship:
    """Represents a spatial relationship between objects"""

    object_a_id: str
    object_b_id: str
    relationship_type: str
    distance: float
    metadata: Dict[str, Any]


class SpatialEngine:
    """
    Advanced spatial relationship engine for building validation

    Provides:
    - Distance calculations between objects
    - Room adjacency detection
    - Floor-to-floor relationships
    - Elevation and height constraints
    - Spatial clustering and grouping
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Spatial relationship types
        self.relationship_types = {
            "adjacent": self._check_adjacency,
            "within_distance": self._check_within_distance,
            "above": self._check_above,
            "below": self._check_below,
            "same_floor": self._check_same_floor,
            "connected": self._check_connected,
            "overlapping": self._check_overlapping,
        }

    def calculate_distance(self, obj_a: BuildingObject, obj_b: BuildingObject) -> float:
        """Calculate 3D distance between two objects"""
        try:
            if not obj_a.location or not obj_b.location:
                return float("inf")

            # Get 3D coordinates
            x1, y1, z1 = self._get_3d_coordinates(obj_a)
            x2, y2, z2 = self._get_3d_coordinates(obj_b)

            # Calculate 3D distance
            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)
            return distance

        except Exception as e:
            self.logger.error(f"Error calculating distance: {e}")
            return float("inf")

    def _get_3d_coordinates(self, obj: BuildingObject) -> Tuple[float, float, float]:
        """Extract 3D coordinates from object location"""
        location = obj.location or {}

        x = location.get("x", 0.0)
        y = location.get("y", 0.0)
        z = location.get("z", 0.0)

        return x, y, z

    def check_spatial_relationship(
        self,
        obj_a: BuildingObject,
        obj_b: BuildingObject,
        relationship_type: str,
        **kwargs,
    ) -> bool:
        """Check if two objects have a specific spatial relationship"""
        if relationship_type not in self.relationship_types:
            self.logger.warning(f"Unknown relationship type: {relationship_type}")
            return False

        try:
            return self.relationship_types[relationship_type](obj_a, obj_b, **kwargs)
        except Exception as e:
            self.logger.error(f"Error checking spatial relationship: {e}")
            return False

    def _check_adjacency(
        self, obj_a: BuildingObject, obj_b: BuildingObject, max_distance: float = 1.0
    ) -> bool:
        """Check if objects are adjacent (within specified distance)"""
        distance = self.calculate_distance(obj_a, obj_b)
        return distance <= max_distance

    def _check_within_distance(
        self, obj_a: BuildingObject, obj_b: BuildingObject, max_distance: float
    ) -> bool:
        """Check if objects are within specified distance"""
        distance = self.calculate_distance(obj_a, obj_b)
        return distance <= max_distance

    def _check_above(
        self, obj_a: BuildingObject, obj_b: BuildingObject, min_height_diff: float = 0.1
    ) -> bool:
        """Check if obj_a is above obj_b"""
        try:
            z1 = obj_a.location.get("z", 0) if obj_a.location else 0
            z2 = obj_b.location.get("z", 0) if obj_b.location else 0

            return z1 > z2 + min_height_diff
        except Exception:
            return False

    def _check_below(
        self, obj_a: BuildingObject, obj_b: BuildingObject, min_height_diff: float = 0.1
    ) -> bool:
        """Check if obj_a is below obj_b"""
        try:
            z1 = obj_a.location.get("z", 0) if obj_a.location else 0
            z2 = obj_b.location.get("z", 0) if obj_b.location else 0

            return z1 < z2 - min_height_diff
        except Exception:
            return False

    def _check_same_floor(
        self, obj_a: BuildingObject, obj_b: BuildingObject, tolerance: float = 0.5
    ) -> bool:
        """Check if objects are on the same floor"""
        try:
            z1 = obj_a.location.get("z", 0) if obj_a.location else 0
            z2 = obj_b.location.get("z", 0) if obj_b.location else 0

            return abs(z1 - z2) <= tolerance
        except Exception:
            return False

    def _check_connected(self, obj_a: BuildingObject, obj_b: BuildingObject) -> bool:
        """Check if objects are connected (share connections)"""
        return (
            obj_b.object_id in obj_a.connections or obj_a.object_id in obj_b.connections
        )

    def _check_overlapping(self, obj_a: BuildingObject, obj_b: BuildingObject) -> bool:
        """Check if objects overlap in 3D space"""
        try:
            if not obj_a.location or not obj_b.location:
                return False

            # Get bounding boxes
            box_a = self._get_bounding_box(obj_a)
            box_b = self._get_bounding_box(obj_b)

            # Check for overlap in all dimensions
            return (
                box_a["x_min"] < box_b["x_max"]
                and box_a["x_max"] > box_b["x_min"]
                and box_a["y_min"] < box_b["y_max"]
                and box_a["y_max"] > box_b["y_min"]
                and box_a["z_min"] < box_b["z_max"]
                and box_a["z_max"] > box_b["z_min"]
            )

        except Exception:
            return False

    def _get_bounding_box(self, obj: BuildingObject) -> Dict[str, float]:
        """Get 3D bounding box for object"""
        location = obj.location or {}

        x = location.get("x", 0)
        y = location.get("y", 0)
        z = location.get("z", 0)
        width = location.get("width", 0)
        height = location.get("height", 0)
        depth = location.get("depth", 0)

        return {
            "x_min": x,
            "x_max": x + width,
            "y_min": y,
            "y_max": y + height,
            "z_min": z,
            "z_max": z + depth,
        }

    def find_objects_within_distance(
        self,
        target_obj: BuildingObject,
        all_objects: List[BuildingObject],
        max_distance: float,
    ) -> List[BuildingObject]:
        """Find all objects within specified distance of target"""
        nearby_objects = []

        for obj in all_objects:
            if obj.object_id == target_obj.object_id:
                continue

            distance = self.calculate_distance(target_obj, obj)
            if distance <= max_distance:
                nearby_objects.append(obj)

        return nearby_objects

    def find_adjacent_rooms(
        self, room: BuildingObject, all_rooms: List[BuildingObject]
    ) -> List[BuildingObject]:
        """Find rooms adjacent to the specified room"""
        adjacent_rooms = []

        for other_room in all_rooms:
            if other_room.object_id == room.object_id:
                continue

            if self._check_adjacency(room, other_room, max_distance=2.0):
                adjacent_rooms.append(other_room)

        return adjacent_rooms

    def calculate_room_area(self, room: BuildingObject) -> float:
        """Calculate area of a room"""
        try:
            location = room.location or {}
            width = location.get("width", 0)
            height = location.get("height", 0)

            if width > 0 and height > 0:
                return width * height

            # Fallback to properties
            return room.properties.get("area", 0)

        except Exception as e:
            self.logger.error(f"Error calculating room area: {e}")
            return 0

    def calculate_room_volume(self, room: BuildingObject) -> float:
        """Calculate volume of a room"""
        try:
            location = room.location or {}
            width = location.get("width", 0)
            height = location.get("height", 0)
            depth = location.get("depth", 0)

            if width > 0 and height > 0 and depth > 0:
                return width * height * depth

            # Fallback to properties
            return room.properties.get("volume", 0)

        except Exception as e:
            self.logger.error(f"Error calculating room volume: {e}")
            return 0

    def get_floor_level(self, obj: BuildingObject) -> int:
        """Get floor level for object"""
        try:
            z = obj.location.get("z", 0) if obj.location else 0
            floor_height = 10  # Standard floor height in feet
            return int(z / floor_height)
        except Exception:
            return 0

    def validate_spatial_constraints(
        self, objects: List[BuildingObject], constraints: List[Dict[str, Any]]
    ) -> List[str]:
        """Validate spatial constraints between objects"""
        violations = []

        for constraint in constraints:
            try:
                constraint_type = constraint.get("type")
                object_a_type = constraint.get("object_a_type")
                object_b_type = constraint.get("object_b_type")
                relationship = constraint.get("relationship")
                max_distance = constraint.get("max_distance", 1.0)

                # Find objects of specified types
                objects_a = [obj for obj in objects if obj.object_type == object_a_type]
                objects_b = [obj for obj in objects if obj.object_type == object_b_type]

                # Check constraints
                for obj_a in objects_a:
                    for obj_b in objects_b:
                        if obj_a.object_id == obj_b.object_id:
                            continue

                        if not self.check_spatial_relationship(
                            obj_a, obj_b, relationship, max_distance=max_distance
                        ):
                            violation_msg = f"Spatial constraint violation: {obj_a.object_type} {obj_a.object_id} must be {relationship} {obj_b.object_type} {obj_b.object_id}"
                            violations.append(violation_msg)

            except Exception as e:
                self.logger.error(f"Error validating spatial constraint: {e}")
                violations.append(f"Error validating spatial constraint: {e}")

        return violations

    def calculate_egress_distance(
        self, room: BuildingObject, exit_objects: List[BuildingObject]
    ) -> float:
        """Calculate shortest egress distance from room to nearest exit"""
        if not exit_objects:
            return float("inf")

        min_distance = float("inf")
        for exit_obj in exit_objects:
            distance = self.calculate_distance(room, exit_obj)
            min_distance = min(min_distance, distance)

        return min_distance

    def validate_egress_requirements(
        self,
        rooms: List[BuildingObject],
        exits: List[BuildingObject],
        max_egress_distance: float,
    ) -> List[str]:
        """Validate egress distance requirements"""
        violations = []

        for room in rooms:
            egress_distance = self.calculate_egress_distance(room, exits)
            if egress_distance > max_egress_distance:
                violation_msg = f"Egress distance violation: Room {room.object_id} is {egress_distance:.1f} units from nearest exit (max {max_egress_distance})"
                violations.append(violation_msg)

        return violations
