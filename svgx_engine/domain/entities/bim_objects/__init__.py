"""
SVGX Engine - BIM Objects Package

This package contains all BIM object entities with embedded engineering logic,
organized by building system type. Each BIM object has its own engineering analysis capabilities.
"""

# Electrical System BIM Objects
from .electrical import (
    ElectricalObjectType,
    ElectricalBIMObject,
    ElectricalOutlet,
    ElectricalPanel,
    ElectricalSwitch,
    ElectricalTransformer,
    ElectricalBreaker,
    ElectricalLight,
)

# Mechanical System BIM Objects (HVAC)
from .mechanical import (
    HVACObjectType,
    HVACBIMObject,
    HVACDuct,
    HVACDamper,
    HVACDiffuser,
    HVACFan,
    HVACThermostat,
)

# Plumbing System BIM Objects
from .plumbing import (
    PlumbingObjectType,
    PlumbingBIMObject,
    PlumbingPipe,
    PlumbingValve,
    PlumbingFixture,
    PlumbingPump,
    PlumbingDrain,
)

# Structural System BIM Objects
from .structural import (
    StructuralObjectType,
    StructuralBIMObject,
    StructuralBeam,
    StructuralColumn,
    StructuralWall,
    StructuralSlab,
    StructuralFoundation,
)

# TODO: Future system implementations
# from .fire_protection import (...)
# from .security import (...)
# from .lighting import (...)
# from .communications import (...)
# from .audiovisual import (...)

__all__ = [
    # Electrical objects
    "ElectricalObjectType",
    "ElectricalBIMObject",
    "ElectricalOutlet",
    "ElectricalPanel",
    "ElectricalSwitch",
    "ElectricalTransformer",
    "ElectricalBreaker",
    "ElectricalLight",
    # Mechanical objects (HVAC)
    "HVACObjectType",
    "HVACBIMObject",
    "HVACDuct",
    "HVACDamper",
    "HVACDiffuser",
    "HVACFan",
    "HVACThermostat",
    # Plumbing objects
    "PlumbingObjectType",
    "PlumbingBIMObject",
    "PlumbingPipe",
    "PlumbingValve",
    "PlumbingFixture",
    "PlumbingPump",
    "PlumbingDrain",
    # Structural objects
    "StructuralObjectType",
    "StructuralBIMObject",
    "StructuralBeam",
    "StructuralColumn",
    "StructuralWall",
    "StructuralSlab",
    "StructuralFoundation",
]
