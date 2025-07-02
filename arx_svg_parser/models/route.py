from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from uuid import uuid4
import json

class RoutePoint(BaseModel):
    """Represents a point in a route with coordinates and metadata"""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    z: Optional[float] = Field(None, description="Z coordinate (optional)")
    name: Optional[str] = Field(None, description="Point name/label")
    type: Literal["start", "end", "waypoint", "checkpoint"] = Field("waypoint", description="Point type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional point metadata")
    
    @validator('x', 'y')
    def validate_coordinates(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError('Coordinates must be numeric')
        return float(v)
    
    @validator('z')
    def validate_z_coordinate(cls, v):
        if v is not None and not isinstance(v, (int, float)):
            raise ValueError('Z coordinate must be numeric')
        return float(v) if v is not None else None

class RouteSegment(BaseModel):
    """Represents a segment between two route points"""
    start_point: RoutePoint
    end_point: RoutePoint
    distance: Optional[float] = Field(None, description="Calculated distance")
    duration: Optional[float] = Field(None, description="Estimated duration in seconds")
    type: Literal["walking", "elevator", "stairs", "ramp", "escalator"] = Field("walking", description="Segment type")
    accessibility: Optional[Dict[str, bool]] = Field(None, description="Accessibility features")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional segment metadata")
    
    @validator('distance')
    def validate_distance(cls, v):
        if v is not None and v < 0:
            raise ValueError('Distance cannot be negative')
        return v
    
    @validator('duration')
    def validate_duration(cls, v):
        if v is not None and v < 0:
            raise ValueError('Duration cannot be negative')
        return v

class RouteGeometry(BaseModel):
    """Represents the geometric path of a route"""
    points: List[RoutePoint] = Field(..., min_items=2, description="Route points")
    segments: List[RouteSegment] = Field(default_factory=list, description="Route segments")
    total_distance: Optional[float] = Field(None, description="Total route distance")
    total_duration: Optional[float] = Field(None, description="Total route duration")
    bounding_box: Optional[Dict[str, float]] = Field(None, description="Route bounding box")
    
    @validator('points')
    def validate_points(cls, v):
        if len(v) < 2:
            raise ValueError('Route must have at least 2 points')
        return v
    
    def calculate_metrics(self):
        """Calculate route metrics (distance, duration, bounding box)"""
        if len(self.points) < 2:
            return
        
        # Calculate total distance
        total_distance = 0.0
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
            distance = ((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2) ** 0.5
            if p1.z is not None and p2.z is not None:
                distance = (distance ** 2 + (p2.z - p1.z) ** 2) ** 0.5
            total_distance += distance
        
        self.total_distance = total_distance
        
        # Calculate bounding box
        x_coords = [p.x for p in self.points]
        y_coords = [p.y for p in self.points]
        z_coords = [p.z for p in self.points if p.z is not None]
        
        self.bounding_box = {
            'min_x': min(x_coords),
            'max_x': max(x_coords),
            'min_y': min(y_coords),
            'max_y': max(y_coords)
        }
        
        if z_coords:
            self.bounding_box.update({
                'min_z': min(z_coords),
                'max_z': max(z_coords)
            })

class Route(BaseModel):
    """Main route model with comprehensive route information"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique route identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Route name")
    description: Optional[str] = Field(None, max_length=500, description="Route description")
    floor_id: str = Field(..., description="Associated floor ID")
    building_id: str = Field(..., description="Associated building ID")
    
    # Route classification
    type: Literal["evacuation", "accessibility", "maintenance", "delivery", "custom"] = Field("custom", description="Route type")
    category: Optional[str] = Field(None, description="Route category")
    priority: Literal["low", "medium", "high", "critical"] = Field("medium", description="Route priority")
    
    # Route geometry and metrics
    geometry: RouteGeometry = Field(..., description="Route geometry")
    start_point: RoutePoint = Field(..., description="Route start point")
    end_point: RoutePoint = Field(..., description="Route end point")
    
    # Route properties
    is_active: bool = Field(True, description="Route active status")
    is_public: bool = Field(True, description="Route visibility")
    is_optimized: bool = Field(False, description="Route optimization status")
    
    # Performance metrics
    performance_score: Optional[float] = Field(None, ge=0, le=100, description="Route performance score")
    efficiency_rating: Optional[float] = Field(None, ge=0, le=10, description="Route efficiency rating")
    accessibility_score: Optional[float] = Field(None, ge=0, le=100, description="Accessibility score")
    
    # Metadata and tracking
    created_by: Optional[str] = Field(None, description="User who created the route")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_by: Optional[str] = Field(None, description="User who last updated the route")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Route constraints and requirements
    constraints: Optional[Dict[str, Any]] = Field(None, description="Route constraints")
    requirements: Optional[Dict[str, Any]] = Field(None, description="Route requirements")
    
    # Tags and categorization
    tags: List[str] = Field(default_factory=list, description="Route tags")
    
    # Validation and status
    validation_status: Literal["pending", "validated", "invalid", "warning"] = Field("pending", description="Validation status")
    validation_errors: List[str] = Field(default_factory=list, description="Validation error messages")
    validation_warnings: List[str] = Field(default_factory=list, description="Validation warning messages")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('geometry')
    def validate_geometry(cls, v):
        """Validate route geometry"""
        if v.points[0].type != "start":
            raise ValueError('First point must be of type "start"')
        if v.points[-1].type != "end":
            raise ValueError('Last point must be of type "end"')
        return v
    
    @validator('start_point', 'end_point')
    def validate_endpoints(cls, v, values):
        """Validate start and end points match geometry"""
        if 'geometry' in values and values['geometry']:
            geometry = values['geometry']
            if v == geometry.points[0] and v.type != "start":
                raise ValueError('Start point type must be "start"')
            if v == geometry.points[-1] and v.type != "end":
                raise ValueError('End point type must be "end"')
        return v
    
    def update_metrics(self):
        """Update route metrics"""
        self.geometry.calculate_metrics()
        self.total_distance = self.geometry.total_distance
        self.total_duration = self.geometry.total_duration
    
    def validate_route(self) -> List[str]:
        """Validate route and return list of errors"""
        errors = []
        
        # Basic validation
        if not self.name.strip():
            errors.append("Route name cannot be empty")
        
        if len(self.geometry.points) < 2:
            errors.append("Route must have at least 2 points")
        
        # Geometry validation
        for i, point in enumerate(self.geometry.points):
            if i == 0 and point.type != "start":
                errors.append("First point must be of type 'start'")
            elif i == len(self.geometry.points) - 1 and point.type != "end":
                errors.append("Last point must be of type 'end'")
        
        # Distance validation
        if self.geometry.total_distance and self.geometry.total_distance <= 0:
            errors.append("Route distance must be greater than 0")
        
        # Performance validation
        if self.performance_score is not None and (self.performance_score < 0 or self.performance_score > 100):
            errors.append("Performance score must be between 0 and 100")
        
        return errors

class RouteCreateRequest(BaseModel):
    """Request model for creating a new route"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    floor_id: str = Field(..., description="Associated floor ID")
    building_id: str = Field(..., description="Associated building ID")
    type: Literal["evacuation", "accessibility", "maintenance", "delivery", "custom"] = Field("custom")
    category: Optional[str] = None
    priority: Literal["low", "medium", "high", "critical"] = Field("medium")
    geometry: RouteGeometry
    is_public: bool = Field(True)
    constraints: Optional[Dict[str, Any]] = None
    requirements: Optional[Dict[str, Any]] = None
    tags: List[str] = Field(default_factory=list)

class RouteUpdateRequest(BaseModel):
    """Request model for updating an existing route"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    type: Optional[Literal["evacuation", "accessibility", "maintenance", "delivery", "custom"]] = None
    category: Optional[str] = None
    priority: Optional[Literal["low", "medium", "high", "critical"]] = None
    geometry: Optional[RouteGeometry] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    constraints: Optional[Dict[str, Any]] = None
    requirements: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

class RouteResponse(BaseModel):
    """Response model for route operations"""
    route: Route
    message: str = "Operation completed successfully"
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)

class RouteListResponse(BaseModel):
    """Response model for route listing operations"""
    routes: List[Route]
    total_count: int
    page: int = 1
    page_size: int = 50
    filters: Optional[Dict[str, Any]] = None

class RouteAnalytics(BaseModel):
    """Analytics data for routes"""
    route_id: str
    total_usage: int = 0
    average_duration: Optional[float] = None
    success_rate: Optional[float] = None
    user_ratings: Optional[float] = None
    last_used: Optional[datetime] = None
    performance_trends: Optional[Dict[str, Any]] = None

class RouteOptimizationRequest(BaseModel):
    """Request model for route optimization"""
    route_id: str
    optimization_type: Literal["distance", "time", "accessibility", "efficiency"] = Field("efficiency")
    constraints: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None

class RouteConflict(BaseModel):
    """Model for route conflicts"""
    conflict_id: str = Field(default_factory=lambda: str(uuid4()))
    route_id: str
    conflict_type: Literal["overlap", "intersection", "proximity", "accessibility"] = Field(...)
    severity: Literal["low", "medium", "high", "critical"] = Field(...)
    description: str
    affected_routes: List[str] = Field(default_factory=list)
    location: Optional[Dict[str, float]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = Field(False)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

class RouteValidationResult(BaseModel):
    """Result of route validation"""
    route_id: str
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    performance_score: Optional[float] = None
    accessibility_score: Optional[float] = None
    efficiency_rating: Optional[float] = None
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow) 