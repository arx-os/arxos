"""
Coordinates Value Object

Represents geographic coordinates (latitude, longitude) in the domain.
This is a value object that is immutable and defined by its attributes.
"""

from dataclasses import dataclass
from typing import Tuple
import math


@dataclass(frozen=True)
class Coordinates:
    """
    Coordinates value object representing geographic location.

    Attributes:
        latitude: Latitude in decimal degrees (-90 to 90)
        longitude: Longitude in decimal degrees (-180 to 180)
    """

    latitude: float
    longitude: float

    def __post_init__(self):
        """Validate coordinates after initialization."""
        self._validate_latitude()
        self._validate_longitude()

    def _validate_latitude(self):
        """Validate latitude value."""
        if not isinstance(self.latitude, (int, float)):
            raise ValueError("Latitude must be a number")
        if self.latitude < -90 or self.latitude > 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")

    def _validate_longitude(self):
        """Validate longitude value."""
        if not isinstance(self.longitude, (int, float)):
            raise ValueError("Longitude must be a number")
        if self.longitude < -180 or self.longitude > 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")

    @property
    def as_tuple(self) -> Tuple[float, float]:
        """Get coordinates as a tuple."""
        return (self.latitude, self.longitude)

    @property
    def is_valid(self) -> bool:
        """Check if coordinates are valid."""
        return (-90 <= self.latitude <= 90) and (-180 <= self.longitude <= 180)

    def distance_to(self, other: "Coordinates") -> float:
        """
        Calculate distance to another set of coordinates using Haversine formula.

        Args:
            other: Another Coordinates object

        Returns:
            Distance in kilometers
        """
        if not isinstance(other, Coordinates):
            raise ValueError("Other must be a Coordinates object")

        # Haversine formula for calculating distance between two points on Earth
        R = 6371  # Earth's radius in kilometers

        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def bearing_to(self, other: "Coordinates") -> float:
        """
        Calculate bearing to another set of coordinates.

        Args:
            other: Another Coordinates object

        Returns:
            Bearing in degrees (0-360)
        """
        if not isinstance(other, Coordinates):
            raise ValueError("Other must be a Coordinates object")

        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)

        dlon = lon2 - lon1

        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(
            lat2
        ) * math.cos(dlon)

        bearing = math.degrees(math.atan2(y, x))
        return (bearing + 360) % 360  # Normalize to 0-360

    def within_radius(self, other: "Coordinates", radius_km: float) -> bool:
        """
        Check if another coordinate is within specified radius.

        Args:
            other: Another Coordinates object
            radius_km: Radius in kilometers

        Returns:
            True if within radius, False otherwise
        """
        return self.distance_to(other) <= radius_km

    def __str__(self) -> str:
        """String representation of coordinates."""
        return f"({self.latitude:.6f}, {self.longitude:.6f})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Coordinates(latitude={self.latitude}, longitude={self.longitude})"
