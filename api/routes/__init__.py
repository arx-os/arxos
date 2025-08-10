"""
API Routes Module

This module organizes and exports all API routers for the Arxos platform.
"""

from .device_routes import router as device_router
from .room_routes import router as room_router
from .user_routes import router as user_router
from .project_routes import router as project_router
from .building_routes import router as building_router
from .floor_routes import router as floor_router
from .health_routes import router as health_router
# Optional PDF analysis routes are excluded from default import to avoid pulling
# heavy dependencies during core API test runs. Enable when that subsystem is ready.
# from .pdf_analysis_routes import pdf_router

# Export all routers
__all__ = [
    "device_router",
    "room_router",
    "user_router",
    "project_router",
    "building_router",
    "floor_router",
    "health_router",
]
