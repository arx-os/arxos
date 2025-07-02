"""
Advanced Floor Management Models
Comprehensive models for floor-specific features including grid calibration,
analytics, comparison tools, and enhanced floor management
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Literal, Tuple
from datetime import datetime
from uuid import uuid4
import json
import math

class GridPoint(BaseModel):
    """Represents a point in the grid calibration system"""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    z: Optional[float] = Field(None, description="Z coordinate (for 3D grids)")
    grid_x: int = Field(..., description="Grid X index")
    grid_y: int = Field(..., description="Grid Y index")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Calibration confidence")
    reference_point: bool = Field(False, description="Whether this is a reference point")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class GridCalibration(BaseModel):
    """Grid calibration data for a floor"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Calibration ID")
    floor_id: str = Field(..., description="Associated floor ID")
    building_id: str = Field(..., description="Associated building ID")
    
    # Grid configuration
    grid_size: float = Field(..., gt=0, description="Grid cell size in units")
    grid_origin: Tuple[float, float] = Field(..., description="Grid origin point (x, y)")
    grid_rotation: float = Field(0.0, description="Grid rotation in degrees")
    grid_type: Literal["rectangular", "hexagonal", "custom"] = Field("rectangular", description="Grid type")
    
    # Calibration points
    calibration_points: List[GridPoint] = Field(default_factory=list, description="Calibration points")
    reference_points: List[GridPoint] = Field(default_factory=list, description="Reference points")
    
    # Calibration metrics
    calibration_accuracy: float = Field(0.0, ge=0.0, le=1.0, description="Overall calibration accuracy")
    calibration_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Calibration confidence")
    calibration_errors: List[str] = Field(default_factory=list, description="Calibration error messages")
    
    # Multi-floor alignment
    aligned_with_floors: List[str] = Field(default_factory=list, description="Floors this grid is aligned with")
    alignment_offsets: Dict[str, Tuple[float, float, float]] = Field(default_factory=dict, description="Alignment offsets to other floors")
    
    # Metadata
    created_by: Optional[str] = Field(None, description="User who created the calibration")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_by: Optional[str] = Field(None, description="User who last updated the calibration")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Validation status
    is_valid: bool = Field(False, description="Whether calibration is valid")
    validation_errors: List[str] = Field(default_factory=list, description="Validation error messages")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('calibration_points')
    def validate_calibration_points(cls, v):
        """Validate calibration points"""
        if len(v) < 3:
            raise ValueError('At least 3 calibration points are required')
        return v
    
    @validator('reference_points')
    def validate_reference_points(cls, v):
        """Validate reference points"""
        if len(v) < 2:
            raise ValueError('At least 2 reference points are required')
        return v
    
    def calculate_accuracy(self) -> float:
        """Calculate calibration accuracy based on point distribution"""
        if len(self.calibration_points) < 3:
            return 0.0
        
        # Calculate average confidence
        avg_confidence = sum(p.confidence for p in self.calibration_points) / len(self.calibration_points)
        
        # Calculate point distribution quality
        points = [(p.x, p.y) for p in self.calibration_points]
        distribution_score = self._calculate_distribution_score(points)
        
        # Calculate reference point alignment
        reference_score = self._calculate_reference_alignment()
        
        # Weighted combination
        accuracy = (avg_confidence * 0.4 + distribution_score * 0.4 + reference_score * 0.2)
        return min(1.0, max(0.0, accuracy))
    
    def _calculate_distribution_score(self, points: List[Tuple[float, float]]) -> float:
        """Calculate how well distributed the calibration points are"""
        if len(points) < 3:
            return 0.0
        
        # Calculate convex hull area
        hull_area = self._calculate_convex_hull_area(points)
        
        # Calculate bounding box area
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        bbox_area = (max(x_coords) - min(x_coords)) * (max(y_coords) - min(y_coords))
        
        if bbox_area == 0:
            return 0.0
        
        # Ratio of hull area to bounding box area (higher is better)
        return hull_area / bbox_area
    
    def _calculate_convex_hull_area(self, points: List[Tuple[float, float]]) -> float:
        """Calculate convex hull area using Graham scan algorithm"""
        if len(points) < 3:
            return 0.0
        
        # Sort points by polar angle
        center = (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))
        
        def polar_angle(p):
            return math.atan2(p[1] - center[1], p[0] - center[0])
        
        sorted_points = sorted(points, key=polar_angle)
        
        # Graham scan
        hull = []
        for p in sorted_points:
            while len(hull) >= 2 and self._cross_product(hull[-2], hull[-1], p) <= 0:
                hull.pop()
            hull.append(p)
        
        # Calculate area
        area = 0.0
        for i in range(len(hull)):
            j = (i + 1) % len(hull)
            area += hull[i][0] * hull[j][1]
            area -= hull[j][0] * hull[i][1]
        
        return abs(area) / 2.0
    
    def _cross_product(self, a: Tuple[float, float], b: Tuple[float, float], c: Tuple[float, float]) -> float:
        """Calculate cross product for three points"""
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    
    def _calculate_reference_alignment(self) -> float:
        """Calculate how well reference points align with calibration points"""
        if len(self.reference_points) < 2 or len(self.calibration_points) < 2:
            return 0.0
        
        # Calculate average distance between reference points and nearest calibration points
        total_distance = 0.0
        for ref_point in self.reference_points:
            min_distance = float('inf')
            for cal_point in self.calibration_points:
                distance = math.sqrt((ref_point.x - cal_point.x)**2 + (ref_point.y - cal_point.y)**2)
                min_distance = min(min_distance, distance)
            total_distance += min_distance
        
        avg_distance = total_distance / len(self.reference_points)
        
        # Convert to score (closer is better)
        max_expected_distance = self.grid_size * 2  # 2 grid cells
        if avg_distance > max_expected_distance:
            return 0.0
        
        return 1.0 - (avg_distance / max_expected_distance)

class FloorAnalytics(BaseModel):
    """Analytics data for a floor"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Analytics ID")
    floor_id: str = Field(..., description="Associated floor ID")
    building_id: str = Field(..., description="Associated building ID")
    
    # Usage metrics
    total_views: int = Field(0, description="Total floor views")
    unique_visitors: int = Field(0, description="Unique visitors")
    average_session_duration: float = Field(0.0, description="Average session duration in seconds")
    last_accessed: Optional[datetime] = Field(None, description="Last access timestamp")
    
    # Content metrics
    total_objects: int = Field(0, description="Total objects on floor")
    total_routes: int = Field(0, description="Total routes on floor")
    total_annotations: int = Field(0, description="Total annotations on floor")
    
    # Performance metrics
    load_time_average: float = Field(0.0, description="Average load time in seconds")
    render_performance: float = Field(0.0, ge=0.0, le=100.0, description="Render performance score")
    interaction_responsiveness: float = Field(0.0, ge=0.0, le=100.0, description="Interaction responsiveness score")
    
    # Quality metrics
    data_completeness: float = Field(0.0, ge=0.0, le=100.0, description="Data completeness percentage")
    data_accuracy: float = Field(0.0, ge=0.0, le=100.0, description="Data accuracy percentage")
    validation_score: float = Field(0.0, ge=0.0, le=100.0, description="Overall validation score")
    
    # User engagement
    user_ratings: List[float] = Field(default_factory=list, description="User ratings (1-5)")
    average_rating: float = Field(0.0, ge=0.0, le=5.0, description="Average user rating")
    feedback_count: int = Field(0, description="Number of user feedback items")
    
    # Trends
    daily_usage: Dict[str, int] = Field(default_factory=dict, description="Daily usage counts")
    weekly_trends: Dict[str, float] = Field(default_factory=dict, description="Weekly trend data")
    monthly_growth: float = Field(0.0, description="Monthly growth percentage")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def update_average_rating(self):
        """Update average rating from user ratings"""
        if self.user_ratings:
            self.average_rating = sum(self.user_ratings) / len(self.user_ratings)
        else:
            self.average_rating = 0.0
    
    def add_rating(self, rating: float):
        """Add a new user rating"""
        if 1.0 <= rating <= 5.0:
            self.user_ratings.append(rating)
            self.update_average_rating()
            self.feedback_count += 1
    
    def calculate_overall_score(self) -> float:
        """Calculate overall floor performance score"""
        weights = {
            "performance": 0.25,
            "quality": 0.25,
            "engagement": 0.25,
            "usage": 0.25
        }
        
        performance_score = (self.render_performance + self.interaction_responsiveness) / 2
        quality_score = (self.data_completeness + self.data_accuracy + self.validation_score) / 3
        engagement_score = (self.average_rating / 5.0) * 100
        usage_score = min(100.0, (self.total_views / 1000.0) * 100)  # Normalize to 100
        
        overall_score = (
            performance_score * weights["performance"] +
            quality_score * weights["quality"] +
            engagement_score * weights["engagement"] +
            usage_score * weights["usage"]
        )
        
        return min(100.0, max(0.0, overall_score))

class FloorComparison(BaseModel):
    """Floor comparison data"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Comparison ID")
    floor_id_1: str = Field(..., description="First floor ID")
    floor_id_2: str = Field(..., description="Second floor ID")
    building_id: str = Field(..., description="Associated building ID")
    
    # Comparison metrics
    similarity_score: float = Field(0.0, ge=0.0, le=1.0, description="Overall similarity score")
    layout_similarity: float = Field(0.0, ge=0.0, le=1.0, description="Layout similarity score")
    object_similarity: float = Field(0.0, ge=0.0, le=1.0, description="Object similarity score")
    route_similarity: float = Field(0.0, ge=0.0, le=1.0, description="Route similarity score")
    
    # Differences
    differences: List[Dict[str, Any]] = Field(default_factory=list, description="List of differences")
    added_objects: List[str] = Field(default_factory=list, description="Objects added in floor 2")
    removed_objects: List[str] = Field(default_factory=list, description="Objects removed in floor 2")
    modified_objects: List[str] = Field(default_factory=list, description="Objects modified between floors")
    
    # Grid alignment
    grid_alignment_score: float = Field(0.0, ge=0.0, le=1.0, description="Grid alignment score")
    grid_offset: Tuple[float, float, float] = Field((0.0, 0.0, 0.0), description="Grid offset between floors")
    
    # Metadata
    comparison_type: Literal["layout", "objects", "routes", "comprehensive"] = Field("comprehensive", description="Type of comparison")
    created_by: Optional[str] = Field(None, description="User who created the comparison")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def calculate_similarity_score(self):
        """Calculate overall similarity score"""
        weights = {
            "layout": 0.4,
            "objects": 0.3,
            "routes": 0.2,
            "grid": 0.1
        }
        
        self.similarity_score = (
            self.layout_similarity * weights["layout"] +
            self.object_similarity * weights["objects"] +
            self.route_similarity * weights["routes"] +
            self.grid_alignment_score * weights["grid"]
        )

class EnhancedFloor(BaseModel):
    """Enhanced floor model with advanced features"""
    id: str = Field(default_factory=lambda: str(uuid4()), description="Floor ID")
    name: str = Field(..., description="Floor name")
    building_id: str = Field(..., description="Associated building ID")
    
    # Basic properties
    floor_number: Optional[int] = Field(None, description="Floor number")
    floor_type: Literal["ground", "basement", "mezzanine", "standard", "roof"] = Field("standard", description="Floor type")
    floor_area: Optional[float] = Field(None, description="Floor area in square units")
    floor_height: Optional[float] = Field(None, description="Floor height in units")
    
    # File paths
    svg_path: str = Field(..., description="Path to SVG file")
    thumbnail_path: Optional[str] = Field(None, description="Path to thumbnail image")
    metadata_path: Optional[str] = Field(None, description="Path to metadata file")
    
    # Grid calibration
    grid_calibration: Optional[GridCalibration] = Field(None, description="Grid calibration data")
    grid_enabled: bool = Field(True, description="Whether grid is enabled")
    
    # Analytics
    analytics: Optional[FloorAnalytics] = Field(None, description="Floor analytics data")
    
    # Comparison data
    comparisons: List[FloorComparison] = Field(default_factory=list, description="Floor comparisons")
    
    # Validation and quality
    validation_status: Literal["pending", "validated", "invalid", "warning"] = Field("pending", description="Validation status")
    validation_errors: List[str] = Field(default_factory=list, description="Validation error messages")
    quality_score: float = Field(0.0, ge=0.0, le=100.0, description="Overall quality score")
    
    # Metadata
    description: Optional[str] = Field(None, description="Floor description")
    tags: List[str] = Field(default_factory=list, description="Floor tags")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Custom properties")
    
    # Timestamps
    created_by: Optional[str] = Field(None, description="User who created the floor")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_by: Optional[str] = Field(None, description="User who last updated the floor")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Status
    is_active: bool = Field(True, description="Whether floor is active")
    is_public: bool = Field(True, description="Whether floor is publicly visible")
    is_template: bool = Field(False, description="Whether floor is a template")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def update_quality_score(self):
        """Update quality score based on various factors"""
        scores = []
        
        # Grid calibration quality
        if self.grid_calibration and self.grid_calibration.is_valid:
            scores.append(self.grid_calibration.calibration_accuracy * 100)
        else:
            scores.append(0.0)
        
        # Analytics quality
        if self.analytics:
            scores.append(self.analytics.calculate_overall_score())
        else:
            scores.append(50.0)  # Default score
        
        # Validation status
        if self.validation_status == "validated":
            scores.append(100.0)
        elif self.validation_status == "warning":
            scores.append(75.0)
        elif self.validation_status == "invalid":
            scores.append(25.0)
        else:
            scores.append(50.0)
        
        # Calculate average
        self.quality_score = sum(scores) / len(scores)

# Request and Response Models

class GridCalibrationRequest(BaseModel):
    """Request model for grid calibration"""
    floor_id: str = Field(..., description="Floor ID to calibrate")
    grid_size: float = Field(..., gt=0, description="Grid cell size")
    grid_origin: Tuple[float, float] = Field(..., description="Grid origin point")
    grid_rotation: float = Field(0.0, description="Grid rotation in degrees")
    grid_type: Literal["rectangular", "hexagonal", "custom"] = Field("rectangular", description="Grid type")
    calibration_points: List[GridPoint] = Field(..., min_items=3, description="Calibration points")
    reference_points: List[GridPoint] = Field(..., min_items=2, description="Reference points")
    align_with_floors: List[str] = Field(default_factory=list, description="Floors to align with")

class GridCalibrationResponse(BaseModel):
    """Response model for grid calibration"""
    calibration: GridCalibration
    accuracy: float
    confidence: float
    validation_errors: List[str] = Field(default_factory=list)
    alignment_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

class FloorAnalyticsRequest(BaseModel):
    """Request model for floor analytics"""
    floor_id: str = Field(..., description="Floor ID")
    date_range: Optional[Tuple[datetime, datetime]] = Field(None, description="Date range for analytics")
    metrics: List[str] = Field(default_factory=list, description="Specific metrics to calculate")

class FloorAnalyticsResponse(BaseModel):
    """Response model for floor analytics"""
    analytics: FloorAnalytics
    trends: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    performance_indicators: Dict[str, float] = Field(default_factory=dict)

class FloorComparisonRequest(BaseModel):
    """Request model for floor comparison"""
    floor_id_1: str = Field(..., description="First floor ID")
    floor_id_2: str = Field(..., description="Second floor ID")
    comparison_type: Literal["layout", "objects", "routes", "comprehensive"] = Field("comprehensive", description="Type of comparison")
    include_grid_alignment: bool = Field(True, description="Whether to include grid alignment")

class FloorComparisonResponse(BaseModel):
    """Response model for floor comparison"""
    comparison: FloorComparison
    differences_summary: Dict[str, int] = Field(default_factory=dict)
    similarity_breakdown: Dict[str, float] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)

class FloorMergeRequest(BaseModel):
    """Request model for floor merging"""
    source_floor_id: str = Field(..., description="Source floor ID")
    target_floor_id: str = Field(..., description="Target floor ID")
    merge_strategy: Literal["overwrite", "merge", "selective"] = Field("merge", description="Merge strategy")
    conflict_resolution: Dict[str, str] = Field(default_factory=dict, description="Conflict resolution rules")
    preserve_history: bool = Field(True, description="Whether to preserve merge history")

class FloorMergeResponse(BaseModel):
    """Response model for floor merging"""
    merged_floor_id: str
    merge_summary: Dict[str, Any] = Field(default_factory=dict)
    conflicts_resolved: List[str] = Field(default_factory=list)
    merge_history: Dict[str, Any] = Field(default_factory=dict)

class FloorDashboardResponse(BaseModel):
    """Response model for floor dashboard"""
    floor_id: str
    analytics: FloorAnalytics
    grid_calibration: Optional[GridCalibration]
    recent_comparisons: List[FloorComparison]
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    quality_indicators: Dict[str, float] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    trends: Dict[str, Any] = Field(default_factory=dict) 