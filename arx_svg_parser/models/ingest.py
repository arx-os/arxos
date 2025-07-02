from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Optional
from datetime import datetime

class IngestRequest(BaseModel):
    file_type: Literal['image', 'pdf']
    file_data: str = Field(..., min_length=10)
    building_id: str = Field(..., min_length=1)
    floor_label: str = Field(..., min_length=1)

class IngestResponse(BaseModel):
    svg: str
    summary: Dict[str, Any]

class PlacedObject(BaseModel):
    id: str
    svg_id: Optional[str] = None
    symbol_name: str
    x: float
    y: float
    rotation: float = 0.0
    scale: float = 1.0
    name: str
    info: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Floor(BaseModel):
    id: str
    name: str
    building_id: str
    svg_path: str

class FloorResponse(BaseModel):
    id: str
    name: str
    building_id: str
    svg_path: str

class LogEvent(BaseModel):
    action: str
    timestamp: str
    user: dict
    object: dict
    floor_id: Optional[str] = None
    details: Optional[str] = None 