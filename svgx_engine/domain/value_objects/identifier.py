"""
Identifier Value Object

Represents unique identifiers in the domain.
This is a value object that is immutable and defined by its attributes.
"""

from dataclasses import dataclass
from typing import Optional
import uuid
import re


@dataclass(frozen=True)
class Identifier:
    """
    Identifier value object representing unique identifiers.

    Attributes:
        value: The identifier value as a string
        prefix: Optional prefix for the identifier
    """

    value: str
    prefix: Optional[str] = None

    def __post_init__(self):
        """Validate identifier after initialization."""
        self._validate_value()
        self._validate_prefix()

    def _validate_value(self):
        """Validate identifier value."""
        if not self.value or not self.value.strip():
            raise ValueError("Identifier value cannot be empty")

        # Allow alphanumeric characters, hyphens, and underscores
        if not re.match(r"^[a-zA-Z0-9_-]+$", self.value):
            raise ValueError(
                "Identifier can only contain alphanumeric characters, hyphens, and underscores"
            )

    def _validate_prefix(self):
        """Validate prefix if provided."""
        if self.prefix is not None:
            if not self.prefix.strip():
                raise ValueError("Prefix cannot be empty if provided")
            if not re.match(r"^[a-zA-Z0-9_-]+$", self.prefix):
                raise ValueError(
                    "Prefix can only contain alphanumeric characters, hyphens, and underscores"
                )

    @classmethod
    def generate_uuid(cls, prefix: Optional[str] = None) -> "Identifier":
        """
        Generate a new identifier using UUID.

        Args:
            prefix: Optional prefix for the identifier

        Returns:
            New Identifier with UUID value
        """
        uuid_value = str(uuid.uuid4()).replace("-", "")
        return cls(uuid_value, prefix)

    @classmethod
    def generate_sequential(
        cls, sequence: int, prefix: Optional[str] = None, padding: int = 6
    ) -> "Identifier":
        """
        Generate a sequential identifier.

        Args:
            sequence: Sequence number
            prefix: Optional prefix for the identifier
            padding: Number of digits to pad with zeros

        Returns:
            New Identifier with sequential value
        """
        if sequence < 0:
            raise ValueError("Sequence number must be non-negative")

        value = str(sequence).zfill(padding)
        return cls(value, prefix)

    @property
    def full_identifier(self) -> str:
        """Get the complete identifier with prefix."""
        if self.prefix:
            return f"{self.prefix}_{self.value}"
        return self.value

    @property
    def is_uuid(self) -> bool:
        """Check if identifier is a UUID."""
        try:
            uuid.UUID(self.value)
            return True
        except ValueError:
            return False

    @property
    def is_numeric(self) -> bool:
        """Check if identifier is numeric."""
        return self.value.isdigit()

    def matches_pattern(self, pattern: str) -> bool:
        """
        Check if identifier matches a regex pattern.

        Args:
            pattern: Regex pattern to match against

        Returns:
            True if identifier matches pattern
        """
        try:
            return bool(re.match(pattern, self.value))
        except re.error:
            return False

    def __str__(self) -> str:
        """String representation of identifier."""
        return self.full_identifier

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Identifier(value='{self.value}', prefix='{self.prefix}')"
