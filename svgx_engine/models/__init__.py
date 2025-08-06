"""
SVGX Engine - Models Package

Provides data models for SVGX Engine including:
- SVGX document models
- BIM models
- Database models
- System element models
"""

from svgx_engine.models.svgx import (
    SVGXDocument,
    SVGXElement,
    SVGXObject,
    ArxObject,
    ArxBehavior,
    ArxPhysics,
    SVGXSymbol,
)
from svgx_engine.models.database import (
    DatabaseManager,
    DatabaseConfig,
    get_db_manager,
    SVGXModel,
    SVGXElement as SVGXDBElement,
    SVGXObject as SVGXDBObject,
    SVGXBehavior as SVGXDBBehavior,
    SVGXPhysics as SVGXDBPhysics,
    SymbolLibrary,
    ValidationJob,
    ExportJob,
    User,
)
from svgx_engine.models.system_elements import (
    SystemElement,
    ElectricalElement,
    PlumbingElement,
    FireAlarmElement,
    SVGXElement,
    ExtractionResponse,
    User as SystemUser,
)
from svgx_engine.models.bim import (
    BIMModel,
    BIMElement,
    BIMSystem,
    BIMSpace,
    BIMRelationship,
    Room,
    Wall,
    Door,
    Window,
    HVACZone,
    Device,
    SystemType,
    ElementCategory,
    Geometry,
    GeometryType,
)

__all__ = [
    # SVGX Models
    "SVGXDocument",
    "SVGXElement",
    "SVGXObject",
    "ArxObject",
    "ArxBehavior",
    "ArxPhysics",
    "SVGXSymbol",
    # Database Models
    "DatabaseManager",
    "DatabaseConfig",
    "get_db_manager",
    "SVGXModel",
    "SVGXDBElement",
    "SVGXDBObject",
    "SVGXDBBehavior",
    "SVGXDBPhysics",
    "SymbolLibrary",
    "ValidationJob",
    "ExportJob",
    "User",
    # System Element Models
    "SystemElement",
    "ElectricalElement",
    "PlumbingElement",
    "FireAlarmElement",
    "SVGXElement",
    "ExtractionResponse",
    "SystemUser",
    # BIM Models
    "BIMModel",
    "BIMElement",
    "BIMSystem",
    "BIMSpace",
    "BIMRelationship",
    "Room",
    "Wall",
    "Door",
    "Window",
    "HVACZone",
    "Device",
    "SystemType",
    "ElementCategory",
    "Geometry",
    "GeometryType",
]
