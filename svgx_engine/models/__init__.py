"""
SVGX Engine Models Package

This package contains all the data models for the SVGX Engine.
"""

from .svgx import (
    SVGXDocument,
    SVGXElement,
    SVGXObject,
    ArxObject,
    ArxBehavior,
    ArxPhysics
)

from .database import (
    Base,
    DatabaseConfig,
    DatabaseManager,
    get_db_manager,
    SVGXModel,
    SVGXElement as SVGXElementDB,
    SVGXObject as SVGXObjectDB,
    SVGXBehavior as SVGXBehaviorDB,
    SVGXPhysics as SVGXPhysicsDB,
    SymbolLibrary,
    ValidationJob,
    ExportJob,
    User as UserDB
)

from .system_elements import (
    SystemElement,
    ElectricalElement,
    PlumbingElement,
    FireAlarmElement,
    SVGXElement as SVGXSystemElement,
    ExtractedElement,
    ExtractionResponse,
    User
)

from .bim import (
    BIMModel,
    BIMElement,
    BIMElementBase,
    BIMSystem,
    BIMRelationship,
    Room,
    Wall,
    Door,
    Window,
    Device,
    Geometry,
    GeometryType,
    SystemType as BIMSystemType,
    RoomType,
    DeviceCategory
)

__all__ = [
    'SVGXDocument',
    'SVGXElement',
    'SVGXObject',
    'ArxObject',
    'ArxBehavior',
    'ArxPhysics',
    'Base',
    'DatabaseConfig',
    'DatabaseManager',
    'get_db_manager',
    'SVGXModel',
    'SVGXElementDB',
    'SVGXObjectDB',
    'SVGXBehaviorDB',
    'SVGXPhysicsDB',
    'SymbolLibrary',
    'ValidationJob',
    'ExportJob',
    'UserDB',
    'SystemElement',
    'ElectricalElement',
    'PlumbingElement',
    'FireAlarmElement',
    'SVGXSystemElement',
    'ExtractedElement',
    'ExtractionResponse',
    'User',
    'BIMModel',
    'BIMElement',
    'BIMElementBase',
    'BIMSystem',
    'BIMRelationship',
    'Room',
    'Wall',
    'Door',
    'Window',
    'Device',
    'Geometry',
    'GeometryType',
    'BIMSystemType',
    'RoomType',
    'DeviceCategory'
] 