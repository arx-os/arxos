from typing import List, Optional, Tuple, Any
from pydantic import BaseModel, validator

class Geometry(BaseModel):
    type: str  # "Polygon", "LineString", "Point"
    coordinates: Any

    @validator('coordinates')
    def polygon_must_be_closed(cls, v, values):
        if values.get('type') == 'Polygon' and v and v[0] != v[-1]:
            raise ValueError("Polygon coordinates must be closed")
        return v

class BIMElementBase(BaseModel):
    id: str
    name: Optional[str]
    geometry: Geometry
    parent_id: Optional[str] = None
    children: List[str] = []

class Room(BIMElementBase):
    pass

class Wall(BIMElementBase):
    pass

class Door(BIMElementBase):
    pass

class Device(BIMElementBase):
    system: str
    subtype: Optional[str]

class BIMData(BaseModel):
    rooms: List[Room] = []
    walls: List[Wall] = []
    doors: List[Door] = []
    devices: List[Device] = []

class Label(BaseModel):
    id: str
    text: str
    position: Tuple[float, float]
    layer: Optional[str] = None

class BIMModel(BaseModel):
    walls: List[Wall] = []
    rooms: List[Room] = []
    doors: List[Door] = []
    labels: List[Label] = []
    devices: List[Device] = []
    metadata: Optional[dict] = None

def build_bim_model(parsed_svg_elements: List[dict]) -> BIMModel:
    """
    Placeholder utility to build a BIMModel from parsed SVG elements.
    Implement your logic here.
    """
    return BIMModel() 