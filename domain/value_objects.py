"""
Value Objects - Immutable Domain Characteristics

This module contains value objects that represent domain characteristics
without identity. Value objects are immutable and describe aspects of
the domain that are defined by their attributes rather than identity.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import re


class BuildingStatus(Enum):
    """Building status enumeration."""

    PLANNED = "planned"
    UNDER_CONSTRUCTION = "under_construction"
    COMPLETED = "completed"
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"


class FloorStatus(Enum):
    """Floor status enumeration."""

    PLANNED = "planned"
    UNDER_CONSTRUCTION = "under_construction"
    COMPLETED = "completed"
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"


class RoomStatus(Enum):
    """Room status enumeration."""

    PLANNED = "planned"
    UNDER_CONSTRUCTION = "under_construction"
    COMPLETED = "completed"
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    OCCUPIED = "occupied"
    VACANT = "vacant"


class DeviceStatus(Enum):
    """Device status enumeration."""

    INSTALLED = "installed"
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    ERROR = "error"
    DECOMMISSIONED = "decommissioned"


class UserRole(Enum):
    """User role enumeration."""

    ADMIN = "admin"
    ARCHITECT = "architect"
    ENGINEER = "engineer"
    CONTRACTOR = "contractor"
    FACILITY_MANAGER = "facility_manager"
    VIEWER = "viewer"


class ProjectStatus(Enum):
    """Project status enumeration."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class BuildingId:
    """Building identifier value object."""

    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Validate building ID format."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Building ID must be a non-empty string")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"BuildingId('{self.value}')"


@dataclass(frozen=True)
class FloorId:
    """Floor identifier value object."""

    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Validate floor ID format."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Floor ID must be a non-empty string")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"FloorId('{self.value}')"


@dataclass(frozen=True)
class RoomId:
    """Room identifier value object."""

    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Validate room ID format."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Room ID must be a non-empty string")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"RoomId('{self.value}')"


@dataclass(frozen=True)
class DeviceId:
    """Device identifier value object."""

    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Validate device ID format."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Device ID must be a non-empty string")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"DeviceId('{self.value}')"


@dataclass(frozen=True)
class UserId:
    """User identifier value object."""

    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Validate user ID format."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("User ID must be a non-empty string")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"UserId('{self.value}')"


@dataclass(frozen=True)
class ProjectId:
    """Project identifier value object."""

    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Validate project ID format."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Project ID must be a non-empty string")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"ProjectId('{self.value}')"


@dataclass(frozen=True)
class Address:
    """Address value object."""

    street: str
    city: str
    state: str
    postal_code: str
    country: str = "USA"
    unit: Optional[str] = None

    def __post_init__(self):
        """Validate address data."""
        if not self.street or not self.street.strip():
            raise ValueError("Street address is required")
        if not self.city or not self.city.strip():
            raise ValueError("City is required")
        if not self.state or not self.state.strip():
            raise ValueError("State is required")
        if not self.postal_code or not self.postal_code.strip():
            raise ValueError("Postal code is required")

    @property
    def full_address(self) -> str:
        """Get the complete address string."""
        address_parts = [self.street]
        if self.unit:
            address_parts.append(f"Unit {self.unit}")
        address_parts.extend([self.city, self.state, self.postal_code])
        if self.country != "USA":
            address_parts.append(self.country)
        return ", ".join(address_parts)

    def is_valid(self) -> bool:
        """Check if address is valid."""
        return all(
            [
                self.street and self.street.strip(),
                self.city and self.city.strip(),
                self.state and self.state.strip(),
                self.postal_code and self.postal_code.strip(),
            ]
        )

    def __str__(self) -> str:
        return self.full_address

    def __repr__(self) -> str:
        return f"Address('{self.full_address}')"

    @classmethod
    def from_string(cls, address_string: str) -> "Address":
        """Create an Address from a string representation."""
        if not address_string or not address_string.strip():
            raise ValueError("Address string cannot be empty")

        # Simple parsing - split by comma and strip whitespace
        parts = [part.strip() for part in address_string.split(",")]

        if len(parts) < 3:
            raise ValueError("Address must contain at least street, city, and state")

        # Extract components
        street = parts[0]
        city = parts[1]
        state = parts[2]

        # Handle postal code (might be in state field like "CA 12345")
        postal_code = ""
        if len(parts) > 3:
            postal_code = parts[3]
        elif " " in state:
            # State might contain postal code like "CA 12345"
            state_parts = state.split()
            if len(state_parts) > 1:
                state = state_parts[0]
                postal_code = state_parts[1]

        # Default country
        country = "USA"
        if len(parts) > 4:
            country = parts[4]

        return cls(
            street=street,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
        )


@dataclass(frozen=True)
class Coordinates:
    """Geographic coordinates value object."""

    latitude: float
    longitude: float
    elevation: Optional[float] = None

    def __post_init__(self):
        """Validate coordinate values."""
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")
        if self.elevation is not None and not -1000 <= self.elevation <= 9000:
            raise ValueError("Elevation must be between -1000 and 9000 meters")

    def distance_to(self, other: "Coordinates") -> float:
        """Calculate distance to another coordinate point (Haversine formula)."""
        import math

        R = 6371000  # Earth's radius in meters

        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def __str__(self) -> str:
        coord_str = f"{self.latitude:.6f}, {self.longitude:.6f}"
        if self.elevation is not None:
            coord_str += f", {self.elevation:.2f}m"
        return coord_str

    def __repr__(self) -> str:
        return f"Coordinates({self.__str__()})"


@dataclass(frozen=True)
class Dimensions:
    """Physical dimensions value object."""

    width: float
    length: float
    height: Optional[float] = None
    unit: str = "meters"

    def __post_init__(self):
        """Validate dimension values."""
        if self.width <= 0:
            raise ValueError("Width must be positive")
        if self.length <= 0:
            raise ValueError("Length must be positive")
        if self.height is not None and self.height <= 0:
            raise ValueError("Height must be positive")
        if self.unit not in ["meters", "feet", "inches", "centimeters"]:
            raise ValueError("Invalid unit specified")

    @property
    def area(self) -> float:
        """Calculate area in square meters."""
        area = self.width * self.length
        if self.unit == "feet":
            return area * 0.092903
        elif self.unit == "inches":
            return area * 0.00064516
        elif self.unit == "centimeters":
            return area * 0.0001
        return area  # meters

    @property
    def volume(self) -> Optional[float]:
        """Calculate volume in cubic meters."""
        if self.height is None:
            return None
        volume = self.width * self.length * self.height
        if self.unit == "feet":
            return volume * 0.0283168
        elif self.unit == "inches":
            return volume * 0.000016387
        elif self.unit == "centimeters":
            return volume * 0.000001
        return volume  # meters

    def __str__(self) -> str:
        dim_str = f"{self.width} x {self.length}"
        if self.height is not None:
            dim_str += f" x {self.height}"
        return f"{dim_str} {self.unit}"

    def __repr__(self) -> str:
        return f"Dimensions({self.__str__()})"


@dataclass(frozen=True)
class Email:
    """Email address value object."""

    value: str

    def __post_init__(self):
        """Validate email format."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Email must be a non-empty string")

        # Basic email validation regex
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, self.value):
            raise ValueError("Invalid email format")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Email('{self.value}')"

    @property
    def domain(self) -> str:
        """Get the email domain."""
        return self.value.split("@")[1]

    @property
    def local_part(self) -> str:
        """Get the local part of the email."""
        return self.value.split("@")[0]


@dataclass(frozen=True)
class PhoneNumber:
    """Phone number value object."""

    value: str
    country_code: str = "+1"

    def __post_init__(self):
        """Validate phone number format."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Phone number must be a non-empty string")

        # Remove all non-digit characters for validation
        digits_only = re.sub(r"\D", "", self.value)
        if len(digits_only) < 10:
            raise ValueError("Phone number must have at least 10 digits")

    def __str__(self) -> str:
        return f"{self.country_code} {self.value}"

    def __repr__(self) -> str:
        return f"PhoneNumber('{self.__str__()}')"

    @property
    def formatted(self) -> str:
        """Get formatted phone number."""
        digits_only = re.sub(r"\D", "", self.value)
        if len(digits_only) == 10:
            return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
        elif len(digits_only) == 11:
            return f"+{digits_only[0]} ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
        return self.value
