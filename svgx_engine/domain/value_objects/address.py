"""
Address Value Object

Represents a physical address in the domain.
This is a value object that is immutable and defined by its attributes.
"""

from dataclasses import dataclass
from typing import Optional
import re


@dataclass(frozen=True)
class Address:
    """
    Address value object representing a physical location.

    Attributes:
        street: Street address
        city: City name
        state: State or province
        postal_code: Postal/ZIP code
        country: Country name
        unit: Optional unit/apartment number
    """

    street: str
    city: str
    state: str
    postal_code: str
    country: str
    unit: Optional[str] = None

    def __post_init__(self):
        """Validate address components after initialization."""
        self._validate_street()
        self._validate_city()
        self._validate_state()
        self._validate_postal_code()
        self._validate_country()
        self._validate_unit()

    def _validate_street(self):
        """Validate street address."""
        if not self.street or not self.street.strip():
            raise ValueError("Street address cannot be empty")
        if len(self.street.strip()) < 5:
            raise ValueError("Street address must be at least 5 characters")

    def _validate_city(self):
        """Validate city name."""
        if not self.city or not self.city.strip():
            raise ValueError("City cannot be empty")
        if len(self.city.strip()) < 2:
            raise ValueError("City must be at least 2 characters")

    def _validate_state(self):
        """Validate state/province."""
        if not self.state or not self.state.strip():
            raise ValueError("State cannot be empty")
        if len(self.state.strip()) < 2:
            raise ValueError("State must be at least 2 characters")

    def _validate_postal_code(self):
        """Validate postal code format."""
        if not self.postal_code or not self.postal_code.strip():
            raise ValueError("Postal code cannot be empty")
        # Basic postal code validation (can be enhanced for specific countries)
        postal_code = self.postal_code.strip()
        if len(postal_code) < 3:
            raise ValueError("Postal code must be at least 3 characters")

    def _validate_country(self):
        """Validate country name."""
        if not self.country or not self.country.strip():
            raise ValueError("Country cannot be empty")
        if len(self.country.strip()) < 2:
            raise ValueError("Country must be at least 2 characters")

    def _validate_unit(self):
        """Validate unit/apartment number if provided."""
        if self.unit is not None and not self.unit.strip():
            raise ValueError("Unit cannot be empty if provided")

    @property
def full_address(self) -> str:
        """Get the complete formatted address."""
        parts = [self.street]
        if self.unit:
            parts.append(f"Unit {self.unit}")
        parts.extend([
            f"{self.city}, {self.state} {self.postal_code}",
            self.country
        ])
        return ", ".join(parts)

    @property
def city_state(self) -> str:
        """Get city and state combination."""
        return f"{self.city}, {self.state}"

    def is_in_country(self, country: str) -> bool:
        """Check if address is in specified country."""
        return self.country.lower() == country.lower()

    def __str__(self) -> str:
        """String representation of the address."""
        return self.full_address

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Address(street='{self.street}', city='{self.city}', state='{self.state}', postal_code='{self.postal_code}', country='{self.country}', unit='{self.unit}')
    def to_dict(self) -> dict:
        """Convert address to dictionary representation."""
        return {
            'street': self.street,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'unit': self.unit
        }

    @classmethod
def from_dict(cls, data: dict) -> 'Address':
        """Create address from dictionary representation."""
        return cls(
            street=data['street'],
            city=data['city'],
            state=data['state'],
            postal_code=data['postal_code'],
            country=data['country'],
            unit=data.get('unit')
