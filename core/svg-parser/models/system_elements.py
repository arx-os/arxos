from pydantic import BaseModel, Field
from typing import Literal, Optional, Union, List, Tuple, Dict, Any

class SystemElement(BaseModel):
    id: str
    label: Optional[str] = None
    system: Literal["E", "P", "FA", "LV", "N", "M", "Structural"]
    type: str
    coordinates: Tuple[float, float]
    metadata: Optional[Dict[str, Any]] = None

class ElectricalElement(SystemElement):
    system: Literal["E"]
    type: Literal["outlet", "panel", "switch", "light"]
    voltage: Optional[str] = None
    breaker_rating: Optional[str] = None

class PlumbingElement(SystemElement):
    system: Literal["P"]
    type: Literal["pipe", "valve", "faucet", "drain"]
    pipe_size: Optional[str] = None
    material: Optional[str] = None

class FireAlarmElement(SystemElement):
    system: Literal["FA"]
    type: Literal["horn", "strobe", "pull_station", "panel"]
    candela: Optional[int] = None

# Add more specializations as needed...

ExtractedElement = Union[
    ElectricalElement,
    PlumbingElement,
    FireAlarmElement,
    SystemElement
]

class ExtractionResponse(BaseModel):
    building_id: str
    floor_id: str
    elements: List[ExtractedElement]

class User(BaseModel):
    """Simple user model for authentication"""
    id: str
    username: str
    email: Optional[str] = None

class User(BaseModel):
    """Simple user model for authentication"""
    id: str
    username: str
    email: Optional[str] = None 