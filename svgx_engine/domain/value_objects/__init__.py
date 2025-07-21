"""
Value Objects Module

This module contains all value objects used in the domain layer.
Value objects are immutable objects that represent concepts in the domain
and are defined by their attributes rather than their identity.
"""

from .address import Address
from .coordinates import Coordinates
from .dimensions import Dimensions
from .identifier import Identifier
from .money import Money
from .status import Status

__all__ = [
    'Address',
    'Coordinates', 
    'Dimensions',
    'Identifier',
    'Money',
    'Status'
] 