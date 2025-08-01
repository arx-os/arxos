"""
Arxos Core Shared Utilities

A centralized shared library for common utility functions used across
the Arxos Platform. This package provides standardized implementations
for date/time handling, object manipulation, request processing, and
other frequently used utilities.

Modules:
    date_utils: Date and time manipulation utilities
    object_utils: Object flattening, validation, and manipulation
    request_utils: HTTP request processing and validation utilities
    handlers: Error handling and request processing utilities
    models: Common data models and structures
    config: Configuration management utilities
"""

__version__ = "1.0.0"
__author__ = "Arxos Platform Team"

from . import date_utils
from . import object_utils
from . import request_utils
from . import handlers
from . import models
from . import config

__all__ = [
    "date_utils",
    "object_utils", 
    "request_utils",
    "handlers",
    "models",
    "config"
] 