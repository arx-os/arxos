"""
SVGX System Elements Models

This module defines the data models for SVGX system elements including:
- Base system element with SVGX metadata support
- Specialized elements for different building systems
- Enhanced metadata for SVGX-specific properties
- Validation and serialization support
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional, Union, List, Tuple, Dict, Any

class SystemElement(BaseModel):
    """Base system element with SVGX enhancements."""
    id: str
    label: Optional[str] = None
    system: Literal["E", "P", "FA", "LV", "N", "M", "Structural"]
    type: str
    coordinates: Tuple[float, float]
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ElectricalElement(SystemElement):
    """Electrical system element with SVGX enhancements."""
    system: Literal["E"]
    type: Literal["outlet", "panel", "switch", "light"]
    voltage: Optional[str] = None
    breaker_rating: Optional[str] = None
    svgx_properties: Optional[Dict[str, Any]] = Field(default_factory=dict)

class PlumbingElement(SystemElement):
    """Plumbing system element with SVGX enhancements."""
    system: Literal["P"]
    type: Literal["pipe", "valve", "faucet", "drain"]
    pipe_size: Optional[str] = None
    material: Optional[str] = None
    svgx_properties: Optional[Dict[str, Any]] = Field(default_factory=dict)

class FireAlarmElement(SystemElement):
    """Fire alarm system element with SVGX enhancements."""
    system: Literal["FA"]
    type: Literal["horn", "strobe", "pull_station", "panel"]
    candela: Optional[int] = None
    svgx_properties: Optional[Dict[str, Any]] = Field(default_factory=dict)

class SVGXElement(SystemElement):
    """SVGX-specific element with enhanced metadata."""
    system: Literal["Structural"]  # Map SVGX to Structural for compatibility
    type: str  # Allow any type for SVGX elements
    svgx_namespace: Optional[str] = None
    svgx_component_type: Optional[str] = None
    svgx_properties: Optional[Dict[str, Any]] = Field(default_factory=dict)
    original_system: Optional[str] = "SVGX"

# Union type for all extracted elements
ExtractedElement = Union[
    ElectricalElement,
    PlumbingElement,
    FireAlarmElement,
    SVGXElement,
    SystemElement
]

class ExtractionResponse(BaseModel):
    """Response model for BIM extraction with SVGX enhancements."""
    building_id: str
    floor_id: str
    elements: List[ExtractedElement]
    svgx_elements_count: Optional[int] = 0
    extraction_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class User(BaseModel):
    """Simple user model for authentication."""
    id: str
    username: str
    email: Optional[str] = None 