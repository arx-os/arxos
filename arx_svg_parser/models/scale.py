from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum

class CoordinateSystem(str, Enum):
    SVG = "svg"
    REAL_WORLD_METERS = "real_world_meters"
    REAL_WORLD_FEET = "real_world_feet"
    BIM = "bim"

class Units(str, Enum):
    PIXELS = "pixels"
    METERS = "meters"
    FEET = "feet"
    INCHES = "inches"
    MILLIMETERS = "millimeters"

class AnchorPoint(BaseModel):
    svg: List[float] = Field(..., min_items=2, max_items=2)
    real: List[float] = Field(..., min_items=2, max_items=2)

    @validator('svg', 'real')
    def coords_must_be_two_numbers(cls, v):
        if len(v) != 2 or not all(isinstance(x, (int, float)) for x in v):
            raise ValueError('svg and real must be lists of two numbers')
        return v

class ScaleRequest(BaseModel):
    svg_xml: str = Field(..., min_length=10)
    anchor_points: List[AnchorPoint] = Field(..., min_items=2)

class ScaleResponse(BaseModel):
    modified_svg: str

class RealWorldCoordinateRequest(BaseModel):
    svg_coordinates: List[List[float]] = Field(..., description="List of [x, y] coordinates in SVG space")
    scale_x: float = Field(..., gt=0, description="Scale factor for X axis")
    scale_y: float = Field(..., gt=0, description="Scale factor for Y axis")
    origin_x: float = Field(default=0.0, description="Origin X coordinate in real-world space")
    origin_y: float = Field(default=0.0, description="Origin Y coordinate in real-world space")
    units: Units = Field(default=Units.METERS, description="Units for real-world coordinates")

    @validator('svg_coordinates')
    def validate_coordinates(cls, v):
        for coord in v:
            if len(coord) != 2:
                raise ValueError('Each coordinate must be a list of two numbers [x, y]')
            if not all(isinstance(x, (int, float)) for x in coord):
                raise ValueError('Coordinates must be numbers')
        return v

class RealWorldCoordinateResponse(BaseModel):
    real_world_coordinates: List[List[float]]
    units: Units
    scale_factors: Dict[str, float]
    origin: Dict[str, float]

class ScaleValidationRequest(BaseModel):
    anchor_points: List[AnchorPoint] = Field(..., min_items=2)

class ScaleValidationResponse(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    scale_factors: Optional[Dict[str, float]] = None
    coordinate_system_info: Dict[str, Any] = Field(default_factory=dict)

class CoordinateTransformRequest(BaseModel):
    coordinates: List[List[float]] = Field(..., description="List of [x, y] coordinates to transform")
    source_system: CoordinateSystem = Field(..., description="Source coordinate system")
    target_system: CoordinateSystem = Field(..., description="Target coordinate system")
    transformation_matrix: Optional[List[List[float]]] = Field(
        default=None, 
        description="4x4 transformation matrix (optional, will be calculated if not provided)"
    )

    @validator('coordinates')
    def validate_coordinates(cls, v):
        for coord in v:
            if len(coord) != 2:
                raise ValueError('Each coordinate must be a list of two numbers [x, y]')
            if not all(isinstance(x, (int, float)) for x in coord):
                raise ValueError('Coordinates must be numbers')
        return v

    @validator('transformation_matrix')
    def validate_transformation_matrix(cls, v):
        if v is not None:
            if len(v) != 4:
                raise ValueError('Transformation matrix must be 4x4')
            for row in v:
                if len(row) != 4:
                    raise ValueError('Transformation matrix must be 4x4')
                if not all(isinstance(x, (int, float)) for x in row):
                    raise ValueError('Transformation matrix elements must be numbers')
        return v

class CoordinateTransformResponse(BaseModel):
    transformed_coordinates: List[List[float]]
    source_system: CoordinateSystem
    target_system: CoordinateSystem
    transformation_matrix: Optional[List[List[float]]] = None

class CoordinateSystemInfo(BaseModel):
    name: str
    description: str
    units: Units
    origin: str
    axes: str
    supported_transformations: List[str] = Field(default_factory=list)

class ScaleFactors(BaseModel):
    x: float = Field(..., gt=0)
    y: float = Field(..., gt=0)
    uniform: bool = Field(default=False)
    confidence: float = Field(..., ge=0, le=1)

class CoordinateValidationResult(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

class BIMCoordinateRequest(BaseModel):
    svg_coordinates: List[List[float]]
    project_id: str
    floor_id: Optional[str] = None
    scale_factors: Optional[ScaleFactors] = None
    coordinate_system: str = Field(default="project_local")

class BIMCoordinateResponse(BaseModel):
    bim_coordinates: List[List[float]]
    project_id: str
    floor_id: Optional[str] = None
    coordinate_system: str
    units: Units
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ScaleCalculationRequest(BaseModel):
    anchor_points: List[AnchorPoint] = Field(..., min_items=2)
    preferred_units: Units = Field(default=Units.METERS)
    force_uniform_scale: bool = Field(default=False)

class ScaleCalculationResponse(BaseModel):
    scale_factors: ScaleFactors
    anchor_points: List[AnchorPoint]
    validation: CoordinateValidationResult
    recommended_units: Units
    confidence_score: float = Field(..., ge=0, le=1) 