"""
Application Layer - Use Cases and Data Transfer Objects

This module contains the application layer components including use cases,
data transfer objects (DTOs), and application services that orchestrate
domain logic and handle external interfaces.
"""

# Application Services
from application.services.engineering_logic_engine import EngineeringLogicEngine

# Version and metadata
__version__ = "2.0.0"
__description__ = "Application layer for SVGX Engine with embedded engineering logic"

# Export all application components
__all__ = [
    # Application Services
    "EngineeringLogicEngine"
]
