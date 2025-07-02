from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal

class Annotation(BaseModel):
    type: Literal['note', 'device']
    coordinates: List[float] = Field(..., min_items=2, max_items=2)
    text: Optional[str] = None
    subtype: Optional[str] = None
    id: Optional[str] = None

    @validator('coordinates')
    def coords_must_be_two_numbers(cls, v):
        if len(v) != 2 or not all(isinstance(x, (int, float)) for x in v):
            raise ValueError('coordinates must be a list of two numbers')
        return v

class AnnotateRequest(BaseModel):
    svg_xml: str = Field(..., min_length=10)
    annotations: List[Annotation]

class AnnotateResponse(BaseModel):
    modified_svg: str 