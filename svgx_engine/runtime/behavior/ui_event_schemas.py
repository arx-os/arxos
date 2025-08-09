from typing import List, Optional, Union, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class SelectionOrigin(BaseModel):
    """
    Class for SelectionOrigin functionality

Attributes:
        None

Methods:
        None

Example:
        instance = SelectionOrigin()
        result = instance.method()
        print(result)
    """
    x: float
    y: float
    zoom_level: Optional[float] = 1.0

class Modifiers(BaseModel):
    ctrl: bool = False
    shift: bool = False

class SelectionPayload(BaseModel):
    selection_mode: str = Field(..., description="single|multi|lasso|bbox")
    selected_ids: List[str]
    selection_origin: Optional[SelectionOrigin]
    modifiers: Optional[Modifiers]

class EditingPayload(BaseModel):
    target_id: str
    edit_type: str = Field(..., description="move|rotate|scale|update_property")
    before: Optional[Dict[str, Any]]
    after: Optional[Dict[str, Any]]
    property_changed: Optional[Dict[str, Any]]

class NavigationPayload(BaseModel):
    action: str = Field(..., description="zoom|pan|goto_object|floor_change")
    zoom_level: Optional[float]
    camera_position: Optional[Dict[str, float]]
    target_object_id: Optional[str]
    floor_id: Optional[str]

class MediaInfo(BaseModel):
    """
    Class for AnnotationPayload functionality

Attributes:
        None

Methods:
        None

Example:
        instance = AnnotationPayload()
        result = instance.method()
        print(result)
    """
    image_url: Optional[str]

class AnnotationPayload(BaseModel):
    target_id: str
    annotation_type: str = Field(..., description="note|issue|measurement|photo")
    content: Optional[str]
    location: Optional[Dict[str, float]]
    media: Optional[MediaInfo]
    tag: Optional[List[str]]

class UIEventBase(BaseModel):
    event_type: str
    timestamp: datetime
    session_id: str
    user_id: str
    canvas_id: str
    payload: dict

class SelectionEvent(UIEventBase):
    event_type: Literal["selection"]
    payload: SelectionPayload

class EditingEvent(UIEventBase):
    event_type: Literal["editing"]
    payload: EditingPayload

class NavigationEvent(UIEventBase):
    event_type: Literal["navigation"]
    payload: NavigationPayload

class AnnotationEvent(UIEventBase):
    event_type: Literal["annotation"]
    payload: AnnotationPayload

# Union for validation/dispatch
UIEvent = Union[SelectionEvent, EditingEvent, NavigationEvent, AnnotationEvent]
