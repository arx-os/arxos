from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Body, Path, Query, Depends
from pydantic import BaseModel
from arx_svg_parser.services.vision_pipeline import vectorize_image_or_pdf
from arx_svg_parser.services.svg_symbol_library import SVG_SYMBOLS
from arx_svg_parser.models.ingest import IngestResponse, PlacedObject, Floor, FloorResponse, LogEvent
from arx_svg_parser.models.route import (
    Route, RouteCreateRequest, RouteUpdateRequest, RouteResponse, RouteListResponse,
    RouteAnalytics, RouteOptimizationRequest, RouteConflict, RouteValidationResult,
    RoutePoint, RouteGeometry, RouteSegment
)
from arx_svg_parser.models.floor_management import (
    GridCalibration, GridCalibrationRequest, GridCalibrationResponse,
    FloorAnalytics, FloorAnalyticsRequest, FloorAnalyticsResponse,
    FloorComparison, FloorComparisonRequest, FloorComparisonResponse,
    FloorMergeRequest, FloorMergeResponse, FloorDashboardResponse,
    EnhancedFloor
)
import xml.etree.ElementTree as ET
import json
from uuid import uuid4
from datetime import datetime
import os
from typing import List, Optional, Dict, Any
from arx_svg_parser.utils.auth import get_current_user
import time
import math
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
import csv
import io

router = APIRouter()

OBJECTS_FILE = 'placed_objects.json'
FLOORS_FILE = 'floors.json'
FLOOR_SVG_DIR = 'uploaded_floors'
LOG_EVENTS_FILE = 'log_events.json'
CONNECTIONS_FILE = 'connections.json'
ROUTES_FILE = 'routes.json'
ROUTE_ANALYTICS_FILE = 'route_analytics.json'
ROUTE_CONFLICTS_FILE = 'route_conflicts.json'

# --- Floor Management Data Persistence ---
FLOOR_CALIBRATION_FILE = 'floor_calibrations.json'
FLOOR_ANALYTICS_FILE = 'floor_analytics.json'
FLOOR_COMPARISON_FILE = 'floor_comparisons.json'
ENHANCED_FLOORS_FILE = 'enhanced_floors.json'

def load_objects():
    try:
        with open(OBJECTS_FILE, 'r') as f:
            return [PlacedObject(**obj) for obj in json.load(f)]
    except Exception:
        return []

def save_objects(objects):
    with open(OBJECTS_FILE, 'w') as f:
        json.dump([obj.dict() for obj in objects], f, default=str)

def load_floors():
    try:
        with open(FLOORS_FILE, 'r') as f:
            return [Floor(**obj) for obj in json.load(f)]
    except Exception:
        return []

def save_floors(floors):
    with open(FLOORS_FILE, 'w') as f:
        json.dump([obj.dict() for obj in floors], f, default=str)

def load_logs():
    try:
        with open(LOG_EVENTS_FILE, 'r') as f:
            return [LogEvent(**obj) for obj in json.load(f)]
    except Exception:
        return []

def save_logs(logs):
    # Log rotation: archive if file exceeds 10MB
    if os.path.exists(LOG_EVENTS_FILE) and os.path.getsize(LOG_EVENTS_FILE) > 10 * 1024 * 1024:
        ts = int(time.time())
        os.rename(LOG_EVENTS_FILE, f"log_events_{ts}.json")
    with open(LOG_EVENTS_FILE, 'w') as f:
        json.dump([obj.dict() for obj in logs], f, default=str)

def load_connections():
    try:
        with open(CONNECTIONS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def save_connections(connections):
    with open(CONNECTIONS_FILE, 'w') as f:
        json.dump(connections, f, default=str)

# Route Management Functions
def load_routes():
    """Load routes from JSON file"""
    try:
        with open(ROUTES_FILE, 'r') as f:
            routes_data = json.load(f)
            return [Route(**route) for route in routes_data]
    except Exception:
        return []

def save_routes(routes):
    """Save routes to JSON file"""
    with open(ROUTES_FILE, 'w') as f:
        json.dump([route.dict() for route in routes], f, default=str)

def load_route_analytics():
    """Load route analytics from JSON file"""
    try:
        with open(ROUTE_ANALYTICS_FILE, 'r') as f:
            analytics_data = json.load(f)
            return [RouteAnalytics(**analytics) for analytics in analytics_data]
    except Exception:
        return []

def save_route_analytics(analytics):
    """Save route analytics to JSON file"""
    with open(ROUTE_ANALYTICS_FILE, 'w') as f:
        json.dump([a.dict() for a in analytics], f, default=str)

def load_route_conflicts():
    """Load route conflicts from JSON file"""
    try:
        with open(ROUTE_CONFLICTS_FILE, 'r') as f:
            conflicts_data = json.load(f)
            return [RouteConflict(**conflict) for conflict in conflicts_data]
    except Exception:
        return []

def save_route_conflicts(conflicts):
    """Save route conflicts to JSON file"""
    with open(ROUTE_CONFLICTS_FILE, 'w') as f:
        json.dump([c.dict() for c in conflicts], f, default=str)

def validate_floor_id(floor_id: str) -> bool:
    """Validate that a floor ID exists"""
    floors = load_floors()
    return any(floor.id == floor_id for floor in floors)

def log_route_event(action: str, route_id: str, user: dict, details: str = None):
    """Log route-related events"""
    logs = load_logs()
    log_event = LogEvent(
        action=action,
        timestamp=datetime.utcnow().isoformat(),
        user=user,
        object={"route_id": route_id},
        details=details
    )
    logs.append(log_event)
    save_logs(logs)

# Route Validation Functions
def validate_route_geometry(geometry: RouteGeometry) -> List[str]:
    """Validate route geometry and return list of errors"""
    errors = []
    
    if len(geometry.points) < 2:
        errors.append("Route must have at least 2 points")
        return errors
    
    # Check start and end points
    if geometry.points[0].type != "start":
        errors.append("First point must be of type 'start'")
    if geometry.points[-1].type != "end":
        errors.append("Last point must be of type 'end'")
    
    # Check for duplicate consecutive points
    for i in range(len(geometry.points) - 1):
        p1 = geometry.points[i]
        p2 = geometry.points[i + 1]
        if p1.x == p2.x and p1.y == p2.y and p1.z == p2.z:
            errors.append(f"Duplicate consecutive points at index {i}")
    
    # Check for reasonable distances between points
    for i in range(len(geometry.points) - 1):
        p1 = geometry.points[i]
        p2 = geometry.points[i + 1]
        distance = math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
        if distance < 0.1:  # Minimum 10cm between points
            errors.append(f"Points too close together at index {i}")
        if distance > 1000:  # Maximum 1000 units between points
            errors.append(f"Points too far apart at index {i}")
    
    return errors

def check_route_consistency(route: Route, all_routes: List[Route]) -> List[str]:
    """Check route consistency with other routes"""
    warnings = []
    
    # Check for overlapping routes
    for other_route in all_routes:
        if other_route.id == route.id:
            continue
        
        if other_route.floor_id != route.floor_id:
            continue
        
        # Check for overlapping bounding boxes
        if route.geometry.bounding_box and other_route.geometry.bounding_box:
            bb1 = route.geometry.bounding_box
            bb2 = other_route.geometry.bounding_box
            
            if (bb1['max_x'] >= bb2['min_x'] and bb1['min_x'] <= bb2['max_x'] and
                bb1['max_y'] >= bb2['min_y'] and bb1['min_y'] <= bb2['max_y']):
                warnings.append(f"Route overlaps with route '{other_route.name}'")
    
    return warnings

def detect_route_conflicts(route: Route, all_routes: List[Route]) -> List[RouteConflict]:
    """Detect conflicts between routes"""
    conflicts = []
    
    for other_route in all_routes:
        if other_route.id == route.id:
            continue
        
        if other_route.floor_id != route.floor_id:
            continue
        
        # Check for intersections
        for i, point1 in enumerate(route.geometry.points[:-1]):
            for j, point2 in enumerate(other_route.geometry.points[:-1]):
                # Simple line segment intersection check
                if segments_intersect(
                    route.geometry.points[i], route.geometry.points[i+1],
                    other_route.geometry.points[j], other_route.geometry.points[j+1]
                ):
                    conflict = RouteConflict(
                        route_id=route.id,
                        conflict_type="intersection",
                        severity="high",
                        description=f"Route intersects with route '{other_route.name}'",
                        affected_routes=[other_route.id],
                        location={"x": (point1.x + point2.x) / 2, "y": (point1.y + point2.y) / 2}
                    )
                    conflicts.append(conflict)
        
        # Check for proximity conflicts
        min_distance = 5.0  # Minimum distance between routes
        for point1 in route.geometry.points:
            for point2 in other_route.geometry.points:
                distance = math.sqrt((point2.x - point1.x)**2 + (point2.y - point1.y)**2)
                if distance < min_distance:
                    conflict = RouteConflict(
                        route_id=route.id,
                        conflict_type="proximity",
                        severity="medium",
                        description=f"Route too close to route '{other_route.name}'",
                        affected_routes=[other_route.id],
                        location={"x": point1.x, "y": point1.y}
                    )
                    conflicts.append(conflict)
    
    return conflicts

def segments_intersect(p1: RoutePoint, p2: RoutePoint, p3: RoutePoint, p4: RoutePoint) -> bool:
    """Check if two line segments intersect"""
    def ccw(A, B, C):
        return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)
    
    A = (p1.x, p1.y)
    B = (p2.x, p2.y)
    C = (p3.x, p3.y)
    D = (p4.x, p4.y)
    
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)

def validate_route_performance(route: Route) -> Dict[str, Any]:
    """Validate route performance metrics"""
    performance_data = {
        "performance_score": None,
        "efficiency_rating": None,
        "accessibility_score": None,
        "warnings": []
    }
    
    # Calculate performance score based on route characteristics
    if route.geometry.total_distance:
        # Score based on distance efficiency
        if route.geometry.total_distance < 50:
            performance_data["performance_score"] = 90
        elif route.geometry.total_distance < 100:
            performance_data["performance_score"] = 80
        elif route.geometry.total_distance < 200:
            performance_data["performance_score"] = 70
        else:
            performance_data["performance_score"] = 60
            performance_data["warnings"].append("Route is quite long")
    
    # Calculate efficiency rating
    if route.geometry.total_distance and len(route.geometry.points) > 2:
        # Efficiency based on straightness (fewer points = more efficient)
        straight_line_distance = math.sqrt(
            (route.end_point.x - route.start_point.x)**2 + 
            (route.end_point.y - route.start_point.y)**2
        )
        if straight_line_distance > 0:
            efficiency = (straight_line_distance / route.geometry.total_distance) * 10
            performance_data["efficiency_rating"] = min(10, max(0, efficiency))
    
    # Calculate accessibility score
    accessibility_features = 0
    total_segments = len(route.geometry.segments)
    
    for segment in route.geometry.segments:
        if segment.accessibility:
            if segment.accessibility.get("wheelchair_accessible", False):
                accessibility_features += 1
            if segment.accessibility.get("ramp_available", False):
                accessibility_features += 1
            if segment.accessibility.get("elevator_available", False):
                accessibility_features += 1
    
    if total_segments > 0:
        performance_data["accessibility_score"] = (accessibility_features / total_segments) * 100
    
    return performance_data

# Route CRUD Operations
@router.post("/routes", response_model=RouteResponse)
def create_route(req: RouteCreateRequest, user=Depends(get_current_user)):
    """Create a new route with comprehensive validation"""
    
    # Validate floor ID
    if not validate_floor_id(req.floor_id):
        raise HTTPException(status_code=400, detail="Invalid floor ID")
    
    # Load existing routes
    routes = load_routes()
    
    # Check for duplicate route names on the same floor
    if any(r.name.lower() == req.name.lower() and r.floor_id == req.floor_id for r in routes):
        raise HTTPException(status_code=400, detail="Route name already exists on this floor")
    
    # Create route geometry
    geometry = req.geometry
    geometry.calculate_metrics()
    
    # Validate geometry
    geometry_errors = validate_route_geometry(geometry)
    if geometry_errors:
        raise HTTPException(status_code=400, detail=f"Invalid route geometry: {'; '.join(geometry_errors)}")
    
    # Create route
    route = Route(
        name=req.name,
        description=req.description,
        floor_id=req.floor_id,
        building_id=req.building_id,
        type=req.type,
        category=req.category,
        priority=req.priority,
        geometry=geometry,
        start_point=geometry.points[0],
        end_point=geometry.points[-1],
        is_public=req.is_public,
        constraints=req.constraints,
        requirements=req.requirements,
        tags=req.tags,
        created_by=user.get("id") if user else None
    )
    
    # Update route metrics
    route.update_metrics()
    
    # Validate route
    validation_errors = route.validate_route()
    if validation_errors:
        route.validation_status = "invalid"
        route.validation_errors = validation_errors
    else:
        route.validation_status = "validated"
    
    # Check consistency with other routes
    consistency_warnings = check_route_consistency(route, routes)
    route.validation_warnings = consistency_warnings
    
    # Detect conflicts
    conflicts = detect_route_conflicts(route, routes)
    if conflicts:
        existing_conflicts = load_route_conflicts()
        existing_conflicts.extend(conflicts)
        save_route_conflicts(existing_conflicts)
    
    # Calculate performance metrics
    performance_data = validate_route_performance(route)
    route.performance_score = performance_data["performance_score"]
    route.efficiency_rating = performance_data["efficiency_rating"]
    route.accessibility_score = performance_data["accessibility_score"]
    route.validation_warnings.extend(performance_data["warnings"])
    
    # Save route
    routes.append(route)
    save_routes(routes)
    
    # Log event
    log_route_event("route_created", route.id, user, f"Created route '{route.name}'")
    
    return RouteResponse(
        route=route,
        validation_errors=route.validation_errors,
        validation_warnings=route.validation_warnings
    )

@router.get("/routes", response_model=RouteListResponse)
def get_routes(
    floor_id: Optional[str] = Query(None, description="Filter by floor ID"),
    building_id: Optional[str] = Query(None, description="Filter by building ID"),
    route_type: Optional[str] = Query(None, description="Filter by route type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size")
):
    """Get routes with filtering and pagination"""
    
    routes = load_routes()
    
    # Apply filters
    if floor_id:
        routes = [r for r in routes if r.floor_id == floor_id]
    if building_id:
        routes = [r for r in routes if r.building_id == building_id]
    if route_type:
        routes = [r for r in routes if r.type == route_type]
    if is_active is not None:
        routes = [r for r in routes if r.is_active == is_active]
    
    # Pagination
    total_count = len(routes)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_routes = routes[start_idx:end_idx]
    
    return RouteListResponse(
        routes=paginated_routes,
        total_count=total_count,
        page=page,
        page_size=page_size,
        filters={
            "floor_id": floor_id,
            "building_id": building_id,
            "route_type": route_type,
            "is_active": is_active
        }
    )

@router.get("/routes/{route_id}", response_model=RouteResponse)
def get_route(route_id: str = Path(..., description="Route ID")):
    """Get a specific route by ID"""
    
    routes = load_routes()
    route = next((r for r in routes if r.id == route_id), None)
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return RouteResponse(route=route)

@router.get("/floors/{floor_id}/routes", response_model=RouteListResponse)
def get_routes_by_floor(
    floor_id: str = Path(..., description="Floor ID"),
    route_type: Optional[str] = Query(None, description="Filter by route type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """Get all routes for a specific floor"""
    
    # Validate floor ID
    if not validate_floor_id(floor_id):
        raise HTTPException(status_code=400, detail="Invalid floor ID")
    
    routes = load_routes()
    floor_routes = [r for r in routes if r.floor_id == floor_id]
    
    # Apply additional filters
    if route_type:
        floor_routes = [r for r in floor_routes if r.type == route_type]
    if is_active is not None:
        floor_routes = [r for r in floor_routes if r.is_active == is_active]
    
    return RouteListResponse(
        routes=floor_routes,
        total_count=len(floor_routes),
        page=1,
        page_size=len(floor_routes)
    )

@router.patch("/routes/{route_id}", response_model=RouteResponse)
def update_route(
    route_id: str = Path(..., description="Route ID"),
    req: RouteUpdateRequest = Body(...),
    user=Depends(get_current_user)
):
    """Update an existing route with change tracking"""
    
    routes = load_routes()
    route = next((r for r in routes if r.id == route_id), None)
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Track changes
    changes = []
    
    # Update fields if provided
    if req.name is not None and req.name != route.name:
        changes.append(f"name: {route.name} -> {req.name}")
        route.name = req.name
    
    if req.description is not None and req.description != route.description:
        changes.append(f"description updated")
        route.description = req.description
    
    if req.type is not None and req.type != route.type:
        changes.append(f"type: {route.type} -> {req.type}")
        route.type = req.type
    
    if req.category is not None and req.category != route.category:
        changes.append(f"category: {route.category} -> {req.category}")
        route.category = req.category
    
    if req.priority is not None and req.priority != route.priority:
        changes.append(f"priority: {route.priority} -> {req.priority}")
        route.priority = req.priority
    
    if req.is_active is not None and req.is_active != route.is_active:
        changes.append(f"active status: {route.is_active} -> {req.is_active}")
        route.is_active = req.is_active
    
    if req.is_public is not None and req.is_public != route.is_public:
        changes.append(f"public status: {route.is_public} -> {req.is_public}")
        route.is_public = req.is_public
    
    if req.constraints is not None:
        changes.append("constraints updated")
        route.constraints = req.constraints
    
    if req.requirements is not None:
        changes.append("requirements updated")
        route.requirements = req.requirements
    
    if req.tags is not None:
        changes.append("tags updated")
        route.tags = req.tags
    
    # Update geometry if provided
    if req.geometry is not None:
        changes.append("geometry updated")
        route.geometry = req.geometry
        route.geometry.calculate_metrics()
        route.start_point = route.geometry.points[0]
        route.end_point = route.geometry.points[-1]
        
        # Re-validate geometry
        geometry_errors = validate_route_geometry(route.geometry)
        if geometry_errors:
            route.validation_status = "invalid"
            route.validation_errors = geometry_errors
        else:
            route.validation_status = "validated"
            route.validation_errors = []
        
        # Re-check consistency and conflicts
        consistency_warnings = check_route_consistency(route, routes)
        route.validation_warnings = consistency_warnings
        
        conflicts = detect_route_conflicts(route, routes)
        if conflicts:
            existing_conflicts = load_route_conflicts()
            existing_conflicts.extend(conflicts)
            save_route_conflicts(existing_conflicts)
        
        # Re-calculate performance metrics
        performance_data = validate_route_performance(route)
        route.performance_score = performance_data["performance_score"]
        route.efficiency_rating = performance_data["efficiency_rating"]
        route.accessibility_score = performance_data["accessibility_score"]
        route.validation_warnings.extend(performance_data["warnings"])
    
    # Update metadata
    route.updated_by = user.get("id") if user else None
    route.updated_at = datetime.utcnow()
    
    # Save changes
    save_routes(routes)
    
    # Log event
    if changes:
        log_route_event("route_updated", route.id, user, f"Updated: {', '.join(changes)}")
    
    return RouteResponse(
        route=route,
        validation_errors=route.validation_errors,
        validation_warnings=route.validation_warnings
    )

@router.delete("/routes/{route_id}")
def delete_route(
    route_id: str = Path(..., description="Route ID"),
    user=Depends(get_current_user)
):
    """Delete a route with cascade cleanup"""
    
    routes = load_routes()
    route = next((r for r in routes if r.id == route_id), None)
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Cascade cleanup: remove related analytics
    analytics = load_route_analytics()
    analytics = [a for a in analytics if a.route_id != route_id]
    save_route_analytics(analytics)
    
    # Cascade cleanup: remove related conflicts
    conflicts = load_route_conflicts()
    conflicts = [c for c in conflicts if c.route_id != route_id]
    save_route_conflicts(conflicts)
    
    # Remove route
    routes = [r for r in routes if r.id != route_id]
    save_routes(routes)
    
    # Log event
    log_route_event("route_deleted", route_id, user, f"Deleted route '{route.name}'")
    
    return {"message": "Route deleted successfully", "route_id": route_id}

# Route Validation Endpoints
@router.post("/routes/{route_id}/validate", response_model=RouteValidationResult)
def validate_route_endpoint(
    route_id: str = Path(..., description="Route ID"),
    user=Depends(get_current_user)
):
    """Validate a specific route"""
    
    routes = load_routes()
    route = next((r for r in routes if r.id == route_id), None)
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Perform comprehensive validation
    errors = route.validate_route()
    geometry_errors = validate_route_geometry(route.geometry)
    consistency_warnings = check_route_consistency(route, routes)
    performance_data = validate_route_performance(route)
    
    # Combine all errors and warnings
    all_errors = errors + geometry_errors
    all_warnings = consistency_warnings + performance_data["warnings"]
    
    # Update route validation status
    route.validation_status = "invalid" if all_errors else "validated"
    route.validation_errors = all_errors
    route.validation_warnings = all_warnings
    
    # Update performance metrics
    route.performance_score = performance_data["performance_score"]
    route.efficiency_rating = performance_data["efficiency_rating"]
    route.accessibility_score = performance_data["accessibility_score"]
    
    # Save updated route
    save_routes(routes)
    
    # Log validation event
    log_route_event("route_validated", route_id, user, f"Validation completed: {len(all_errors)} errors, {len(all_warnings)} warnings")
    
    return RouteValidationResult(
        route_id=route_id,
        is_valid=len(all_errors) == 0,
        errors=all_errors,
        warnings=all_warnings,
        performance_score=route.performance_score,
        accessibility_score=route.accessibility_score,
        efficiency_rating=route.efficiency_rating
    )

# Route Analytics Endpoints
@router.get("/routes/{route_id}/analytics", response_model=RouteAnalytics)
def get_route_analytics(route_id: str = Path(..., description="Route ID")):
    """Get analytics for a specific route"""
    
    # Check if route exists
    routes = load_routes()
    route = next((r for r in routes if r.id == route_id), None)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Load analytics
    analytics_list = load_route_analytics()
    analytics = next((a for a in analytics_list if a.route_id == route_id), None)
    
    if not analytics:
        # Create default analytics if none exist
        analytics = RouteAnalytics(route_id=route_id)
    
    return analytics

@router.post("/routes/{route_id}/analytics/record-usage")
def record_route_usage(
    route_id: str = Path(..., description="Route ID"),
    duration: Optional[float] = Query(None, description="Usage duration in seconds"),
    success: bool = Query(True, description="Whether the route was successfully completed"),
    rating: Optional[float] = Query(None, ge=1, le=5, description="User rating (1-5)"),
    user=Depends(get_current_user)
):
    """Record usage analytics for a route"""
    
    # Check if route exists
    routes = load_routes()
    route = next((r for r in routes if r.id == route_id), None)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Load and update analytics
    analytics_list = load_route_analytics()
    analytics = next((a for a in analytics_list if a.route_id == route_id), None)
    
    if not analytics:
        analytics = RouteAnalytics(route_id=route_id)
        analytics_list.append(analytics)
    
    # Update analytics
    analytics.total_usage += 1
    analytics.last_used = datetime.utcnow()
    
    if duration is not None:
        if analytics.average_duration is None:
            analytics.average_duration = duration
        else:
            analytics.average_duration = (analytics.average_duration + duration) / 2
    
    if rating is not None:
        if analytics.user_ratings is None:
            analytics.user_ratings = rating
        else:
            analytics.user_ratings = (analytics.user_ratings + rating) / 2
    
    # Calculate success rate
    if not hasattr(analytics, 'successful_usage'):
        analytics.successful_usage = 0
    if success:
        analytics.successful_usage += 1
    analytics.success_rate = (analytics.successful_usage / analytics.total_usage) * 100
    
    # Save analytics
    save_route_analytics(analytics_list)
    
    # Log usage event
    log_route_event("route_used", route_id, user, f"Route used successfully: {success}")
    
    return {"message": "Usage recorded successfully", "analytics": analytics.dict()}

# Route Optimization Endpoints
@router.post("/routes/{route_id}/optimize")
def optimize_route(
    route_id: str = Path(..., description="Route ID"),
    req: RouteOptimizationRequest = Body(...),
    user=Depends(get_current_user)
):
    """Optimize a route based on specified criteria"""
    
    routes = load_routes()
    route = next((r for r in routes if r.id == route_id), None)
    
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    # Simple optimization algorithm (in production, this would be more sophisticated)
    optimized_geometry = optimize_route_geometry(route.geometry, req.optimization_type, req.constraints)
    
    # Create optimized route
    optimized_route = route.copy()
    optimized_route.id = str(uuid4())
    optimized_route.name = f"{route.name} (Optimized)"
    optimized_route.geometry = optimized_geometry
    optimized_route.is_optimized = True
    optimized_route.created_by = user.get("id") if user else None
    optimized_route.created_at = datetime.utcnow()
    
    # Update metrics
    optimized_route.update_metrics()
    
    # Validate optimized route
    validation_errors = optimized_route.validate_route()
    if validation_errors:
        optimized_route.validation_status = "invalid"
        optimized_route.validation_errors = validation_errors
    else:
        optimized_route.validation_status = "validated"
    
    # Save optimized route
    routes.append(optimized_route)
    save_routes(routes)
    
    # Log optimization event
    log_route_event("route_optimized", route_id, user, f"Created optimized route: {optimized_route.id}")
    
    return RouteResponse(
        route=optimized_route,
        message=f"Route optimized for {req.optimization_type}",
        validation_errors=optimized_route.validation_errors
    )

def optimize_route_geometry(geometry: RouteGeometry, optimization_type: str, constraints: Optional[Dict[str, Any]] = None) -> RouteGeometry:
    """Simple route optimization algorithm"""
    
    # For now, implement a basic optimization that reduces the number of waypoints
    # In production, this would use more sophisticated algorithms like A*, Dijkstra, etc.
    
    optimized_points = []
    
    if optimization_type == "distance":
        # Optimize for shortest distance - use fewer waypoints
        optimized_points = [geometry.points[0]]  # Start point
        
        # Add key waypoints only
        for i in range(1, len(geometry.points) - 1):
            point = geometry.points[i]
            if point.type == "checkpoint" or i % 3 == 0:  # Keep every 3rd point and checkpoints
                optimized_points.append(point)
        
        optimized_points.append(geometry.points[-1])  # End point
    
    elif optimization_type == "time":
        # Optimize for fastest time - prefer elevators/escalators
        optimized_points = geometry.points.copy()
        # In a real implementation, you'd analyze segment types and optimize accordingly
    
    elif optimization_type == "accessibility":
        # Optimize for accessibility - avoid stairs, prefer ramps/elevators
        optimized_points = geometry.points.copy()
        # In a real implementation, you'd filter segments based on accessibility features
    
    else:  # efficiency
        # General efficiency optimization
        optimized_points = geometry.points.copy()
    
    # Create optimized geometry
    optimized_geometry = RouteGeometry(points=optimized_points)
    optimized_geometry.calculate_metrics()
    
    return optimized_geometry

# Route Conflict Management
@router.get("/routes/conflicts", response_model=List[RouteConflict])
def get_route_conflicts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status")
):
    """Get all route conflicts with optional filtering"""
    
    conflicts = load_route_conflicts()
    
    # Apply filters
    if severity:
        conflicts = [c for c in conflicts if c.severity == severity]
    if resolved is not None:
        conflicts = [c for c in conflicts if c.resolved == resolved]
    
    return conflicts

@router.patch("/routes/conflicts/{conflict_id}/resolve")
def resolve_route_conflict(
    conflict_id: str = Path(..., description="Conflict ID"),
    user=Depends(get_current_user)
):
    """Mark a route conflict as resolved"""
    
    conflicts = load_route_conflicts()
    conflict = next((c for c in conflicts if c.conflict_id == conflict_id), None)
    
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")
    
    conflict.resolved = True
    conflict.resolved_at = datetime.utcnow()
    conflict.resolved_by = user.get("id") if user else None
    
    save_route_conflicts(conflicts)
    
    # Log resolution event
    log_route_event("conflict_resolved", conflict.route_id, user, f"Resolved conflict: {conflict.conflict_type}")
    
    return {"message": "Conflict resolved successfully", "conflict_id": conflict_id}

# Existing endpoints continue below...
@router.post("/ingest", response_model=IngestResponse)
def ingest_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    building_id: str = Form(...),
    floor_label: str = Form(...)
):
    file_data = file.file.read()
    result = vectorize_image_or_pdf(
        file_data,
        file_type,
        building_id=building_id,
        floor_label=floor_label
    )
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

class AddSymbolRequest(BaseModel):
    svg_content: str
    symbol_name: str
    x: float
    y: float
    rotation: float = 0.0
    scale: float = 1.0
    name: str = None
    info: str = None

class AddSymbolResponse(BaseModel):
    svg: str

@router.post("/add_symbol", response_model=AddSymbolResponse)
def add_symbol(req: AddSymbolRequest):
    symbol = SVG_SYMBOLS.get(req.symbol_name)
    if not symbol:
        raise HTTPException(status_code=404, detail="Symbol not found")
    # Uniqueness check: name must be unique per symbol_name (object type)
    objects = load_objects()
    # Auto-generate name if not provided
    name = req.name
    if not name:
        prefix = req.symbol_name.capitalize()
        existing = [o for o in objects if o.symbol_name == req.symbol_name and o.name and o.name.startswith(prefix + '-')]
        nums = []
        for o in existing:
            try:
                n = int(o.name.split('-')[-1])
                nums.append(n)
            except Exception:
                continue
        next_num = max(nums) + 1 if nums else 1
        name = f"{prefix}-{next_num}"
    if name and any(o.symbol_name == req.symbol_name and o.name and o.name.lower() == name.lower() for o in objects):
        raise HTTPException(status_code=400, detail=f"Name '{name}' already exists for type '{req.symbol_name}'")
    try:
        svg_root = ET.fromstring(req.svg_content)
        symbol_elem = ET.fromstring(symbol["svg"])
        obj_id = str(uuid4())
        attribs = {
            "transform": f"translate({req.x},{req.y}) scale({req.scale}) rotate({req.rotation})",
            "data-id": obj_id,
            "data-name": name
        }
        if req.info:
            attribs["data-info"] = req.info
        g = ET.Element("g", attrib=attribs)
        g.append(symbol_elem)
        svg_root.append(g)
        updated_svg = ET.tostring(svg_root, encoding="unicode")
        # Persist object
        placed_obj = PlacedObject(
            id=obj_id,
            svg_id=None,  # Set if you have SVG/floor/building context
            symbol_name=req.symbol_name,
            x=req.x,
            y=req.y,
            rotation=req.rotation,
            scale=req.scale,
            name=name,
            info=req.info
        )
        objects.append(placed_obj)
        save_objects(objects)
        return {"svg": updated_svg}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SVG processing error: {str(e)}") 

class UpdateObjectRequest(BaseModel):
    id: str
    x: float = None
    y: float = None
    rotation: float = None
    scale: float = None
    name: str = None
    info: str = None

class UpdateObjectResponse(BaseModel):
    object: PlacedObject

@router.patch("/update_object")
def update_object(req: UpdateObjectRequest):
    objects = load_objects()
    obj = next((o for o in objects if o.id == req.id), None)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    updated = False
    if req.x is not None:
        obj.x = req.x
        updated = True
    if req.y is not None:
        obj.y = req.y
        updated = True
    if req.rotation is not None:
        obj.rotation = req.rotation
        updated = True
    if req.scale is not None:
        obj.scale = req.scale
        updated = True
    if req.name is not None:
        obj.name = req.name
        updated = True
    if req.info is not None:
        obj.info = req.info
        updated = True
    if updated:
        obj.updated_at = datetime.utcnow()
        save_objects(objects)
    # --- SVG update logic ---
    # For demo: load SVG from a placeholder file, update the <g> with data-id, and return updated SVG
    svg_path = 'current_floor.svg'  # TODO: Use actual SVG path for the floor
    try:
        with open(svg_path, 'r') as f:
            svg_content = f.read()
        svg_root = ET.fromstring(svg_content)
        # Find and update the object
        for g in svg_root.findall(".//g[@data-id='{}']".format(req.id)):
            if req.x is not None or req.y is not None:
                current_x = obj.x
                current_y = obj.y
                new_x = req.x if req.x is not None else current_x
                new_y = req.y if req.y is not None else current_y
                g.set("transform", f"translate({new_x},{new_y}) scale({obj.scale}) rotate({obj.rotation})")
            if req.name is not None:
                g.set("data-name", req.name)
            if req.info is not None:
                g.set("data-info", req.info)
        updated_svg = ET.tostring(svg_root, encoding="unicode")
        return {"object": obj, "svg": updated_svg}
    except Exception as e:
        return {"object": obj, "svg": None, "error": f"SVG update failed: {str(e)}"}

class RemoveObjectRequest(BaseModel):
    id: str

class RemoveObjectResponse(BaseModel):
    success: bool

@router.post("/remove_object")
def remove_object(req: RemoveObjectRequest):
    objects = load_objects()
    obj = next((o for o in objects if o.id == req.id), None)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    objects = [o for o in objects if o.id != req.id]
    save_objects(objects)
    # --- SVG removal logic ---
    svg_path = 'current_floor.svg'  # TODO: Use actual SVG path for the floor
    try:
        with open(svg_path, 'r') as f:
            svg_content = f.read()
        svg_root = ET.fromstring(svg_content)
        # Remove the object from SVG
        for g in svg_root.findall(".//g[@data-id='{}']".format(req.id)):
            g.getparent().remove(g)
        updated_svg = ET.tostring(svg_root, encoding="unicode")
        return {"success": True, "svg": updated_svg}
    except Exception as e:
        return {"success": True, "svg": None, "error": f"SVG removal failed: {str(e)}"}

@router.post("/api/buildings/{building_id}/floors", response_model=FloorResponse)
def upload_floor(
    building_id: str = Path(...),
    name: str = Form(...),
    file: UploadFile = File(...)
):
    # Save the uploaded file
    floor_id = str(uuid4())
    svg_path = os.path.join(FLOOR_SVG_DIR, f"{floor_id}.svg")
    os.makedirs(FLOOR_SVG_DIR, exist_ok=True)
    with open(svg_path, "wb") as f:
        f.write(file.file.read())
    
    # Create floor record
    floor = Floor(
        id=floor_id,
        name=name,
        building_id=building_id,
        svg_path=svg_path
    )
    
    # Save floor
    floors = load_floors()
    floors.append(floor)
    save_floors(floors)
    
    return floor

@router.get("/api/buildings/{building_id}/floors")
def list_floors(building_id: str = Path(...)):
    floors = load_floors()
    return [floor for floor in floors if floor.building_id == building_id]

@router.post("/api/log")
def post_log(event: LogEvent, user=Depends(get_current_user)):
    # Overwrite the user field with the authenticated user
    event.user = user
    logs = load_logs()
    logs.append(event)
    save_logs(logs)
    return {"message": "Log event recorded"}

@router.get("/api/log")
def get_logs(floor_id: str = Query(None), limit: int = Query(1000), user=Depends(get_current_user)):
    logs = load_logs()
    if floor_id:
        logs = [log for log in logs if log.floor_id == floor_id]
    return logs[-limit:]

class ConnectionRequest(BaseModel):
    source_id: str
    target_id: str
    floor_id: str

class ConnectionResponse(BaseModel):
    id: str
    source_id: str
    target_id: str
    floor_id: str

@router.post("/api/connect", response_model=ConnectionResponse)
def create_connection(req: ConnectionRequest):
    connections = load_connections()
    connection_id = str(uuid4())
    connection = {
        "id": connection_id,
        "source_id": req.source_id,
        "target_id": req.target_id,
        "floor_id": req.floor_id
    }
    connections.append(connection)
    save_connections(connections)
    return connection

# --- Floor Management Data Persistence ---
def load_floor_calibrations():
    try:
        with open(FLOOR_CALIBRATION_FILE, 'r') as f:
            return [GridCalibration(**obj) for obj in json.load(f)]
    except Exception:
        return []

def save_floor_calibrations(calibrations):
    with open(FLOOR_CALIBRATION_FILE, 'w') as f:
        json.dump([c.dict() for c in calibrations], f, default=str)

def load_floor_analytics():
    try:
        with open(FLOOR_ANALYTICS_FILE, 'r') as f:
            return [FloorAnalytics(**obj) for obj in json.load(f)]
    except Exception:
        return []

def save_floor_analytics(analytics):
    with open(FLOOR_ANALYTICS_FILE, 'w') as f:
        json.dump([a.dict() for a in analytics], f, default=str)

def load_floor_comparisons():
    try:
        with open(FLOOR_COMPARISON_FILE, 'r') as f:
            return [FloorComparison(**obj) for obj in json.load(f)]
    except Exception:
        return []

def save_floor_comparisons(comparisons):
    with open(FLOOR_COMPARISON_FILE, 'w') as f:
        json.dump([c.dict() for c in comparisons], f, default=str)

def load_enhanced_floors():
    try:
        with open(ENHANCED_FLOORS_FILE, 'r') as f:
            return [EnhancedFloor(**obj) for obj in json.load(f)]
    except Exception:
        return []

def save_enhanced_floors(floors):
    with open(ENHANCED_FLOORS_FILE, 'w') as f:
        json.dump([f.dict() for f in floors], f, default=str)

# --- Grid Calibration Endpoints ---
@router.post('/floors/{floor_id}/grid_calibration', response_model=GridCalibrationResponse)
def calibrate_grid(floor_id: str, req: GridCalibrationRequest, user=Depends(get_current_user)):
    calibrations = load_floor_calibrations()
    calibration = GridCalibration(
        floor_id=floor_id,
        building_id=req.floor_id.split('-')[0] if '-' in req.floor_id else '',
        grid_size=req.grid_size,
        grid_origin=req.grid_origin,
        grid_rotation=req.grid_rotation,
        grid_type=req.grid_type,
        calibration_points=req.calibration_points,
        reference_points=req.reference_points,
        aligned_with_floors=req.align_with_floors,
        created_by=user.get('id') if user else None
    )
    calibration.calibration_accuracy = calibration.calculate_accuracy()
    calibration.is_valid = calibration.calibration_accuracy > 0.7
    if not calibration.is_valid:
        calibration.validation_errors.append('Calibration accuracy too low')
    calibrations.append(calibration)
    save_floor_calibrations(calibrations)
    return GridCalibrationResponse(
        calibration=calibration,
        accuracy=calibration.calibration_accuracy,
        confidence=calibration.calibration_confidence,
        validation_errors=calibration.validation_errors,
        alignment_results={}
    )

# --- Multi-Floor Grid Alignment ---
@router.post('/floors/{floor_id}/align_grids', response_model=GridCalibrationResponse)
def align_grids(floor_id: str, align_with: list, user=Depends(get_current_user)):
    calibrations = load_floor_calibrations()
    calibration = next((c for c in calibrations if c.floor_id == floor_id), None)
    if not calibration:
        raise HTTPException(status_code=404, detail='Calibration not found')
    # Simulate alignment (in production, calculate real offsets)
    for other_floor in align_with:
        calibration.aligned_with_floors.append(other_floor)
        calibration.alignment_offsets[other_floor] = (0.0, 0.0, 0.0)
    save_floor_calibrations(calibrations)
    return GridCalibrationResponse(
        calibration=calibration,
        accuracy=calibration.calibration_accuracy,
        confidence=calibration.calibration_confidence,
        validation_errors=calibration.validation_errors,
        alignment_results={f: {'offset': calibration.alignment_offsets[f]} for f in align_with}
    )

# --- Grid Validation Tools ---
@router.get('/floors/{floor_id}/grid_validation', response_model=GridCalibrationResponse)
def validate_grid(floor_id: str):
    calibrations = load_floor_calibrations()
    calibration = next((c for c in calibrations if c.floor_id == floor_id), None)
    if not calibration:
        raise HTTPException(status_code=404, detail='Calibration not found')
    calibration.calibration_accuracy = calibration.calculate_accuracy()
    calibration.is_valid = calibration.calibration_accuracy > 0.7
    if not calibration.is_valid:
        calibration.validation_errors.append('Calibration accuracy too low')
    save_floor_calibrations(calibrations)
    return GridCalibrationResponse(
        calibration=calibration,
        accuracy=calibration.calibration_accuracy,
        confidence=calibration.calibration_confidence,
        validation_errors=calibration.validation_errors,
        alignment_results={}
    )

# --- Floor Analytics Endpoints ---
@router.post('/floors/{floor_id}/analytics', response_model=FloorAnalyticsResponse)
def get_floor_analytics(floor_id: str, req: FloorAnalyticsRequest):
    analytics_list = load_floor_analytics()
    analytics = next((a for a in analytics_list if a.floor_id == floor_id), None)
    if not analytics:
        analytics = FloorAnalytics(floor_id=floor_id, building_id=floor_id.split('-')[0] if '-' in floor_id else '')
    # Simulate trends and recommendations
    trends = {'usage': analytics.daily_usage, 'growth': analytics.monthly_growth}
    recommendations = ['Increase data completeness', 'Improve render performance']
    performance_indicators = {
        'overall_score': analytics.calculate_overall_score(),
        'average_rating': analytics.average_rating
    }
    return FloorAnalyticsResponse(
        analytics=analytics,
        trends=trends,
        recommendations=recommendations,
        performance_indicators=performance_indicators
    )

# --- Floor Comparison Endpoints ---
@router.post('/floors/compare', response_model=FloorComparisonResponse)
def compare_floors(req: FloorComparisonRequest, user=Depends(get_current_user)):
    comparisons = load_floor_comparisons()
    comparison = FloorComparison(
        floor_id_1=req.floor_id_1,
        floor_id_2=req.floor_id_2,
        building_id=req.floor_id_1.split('-')[0] if '-' in req.floor_id_1 else '',
        comparison_type=req.comparison_type,
        created_by=user.get('id') if user else None
    )
    # Simulate similarity and differences
    comparison.layout_similarity = 0.85
    comparison.object_similarity = 0.8
    comparison.route_similarity = 0.75
    comparison.grid_alignment_score = 0.9 if req.include_grid_alignment else 0.0
    comparison.calculate_similarity_score()
    comparison.differences = [{'type': 'object', 'id': 'obj-123', 'change': 'added'}]
    comparison.added_objects = ['obj-123']
    comparisons.append(comparison)
    save_floor_comparisons(comparisons)
    return FloorComparisonResponse(
        comparison=comparison,
        differences_summary={'added': 1, 'removed': 0, 'modified': 0},
        similarity_breakdown={
            'layout': comparison.layout_similarity,
            'objects': comparison.object_similarity,
            'routes': comparison.route_similarity,
            'grid': comparison.grid_alignment_score
        },
        recommendations=['Review added objects', 'Align grid for better accuracy']
    )

# --- Floor Merge Functionality ---
@router.post('/floors/merge', response_model=FloorMergeResponse)
def merge_floors(req: FloorMergeRequest, user=Depends(get_current_user)):
    floors = load_enhanced_floors()
    source = next((f for f in floors if f.id == req.source_floor_id), None)
    target = next((f for f in floors if f.id == req.target_floor_id), None)
    if not source or not target:
        raise HTTPException(status_code=404, detail='Source or target floor not found')
    # Simulate merge (in production, merge objects/routes/metadata)
    merged_floor_id = target.id
    merge_summary = {'source': source.id, 'target': target.id, 'strategy': req.merge_strategy}
    conflicts_resolved = list(req.conflict_resolution.keys())
    merge_history = {'timestamp': datetime.utcnow().isoformat(), 'user': user.get('id') if user else None}
    return FloorMergeResponse(
        merged_floor_id=merged_floor_id,
        merge_summary=merge_summary,
        conflicts_resolved=conflicts_resolved,
        merge_history=merge_history
    )

# --- Floor Dashboard Endpoint ---
@router.get('/floors/{floor_id}/dashboard', response_model=FloorDashboardResponse)
def get_floor_dashboard(floor_id: str):
    floors = load_enhanced_floors()
    floor = next((f for f in floors if f.id == floor_id), None)
    if not floor:
        raise HTTPException(status_code=404, detail='Floor not found')
    analytics = floor.analytics or FloorAnalytics(floor_id=floor_id, building_id=floor.building_id)
    grid_calibration = floor.grid_calibration
    recent_comparisons = floor.comparisons[-5:] if floor.comparisons else []
    performance_metrics = {'quality_score': floor.quality_score}
    quality_indicators = {'validation_status': floor.validation_status}
    recommendations = ['Review grid calibration', 'Increase data completeness']
    trends = analytics.weekly_trends
    return FloorDashboardResponse(
        floor_id=floor_id,
        analytics=analytics,
        grid_calibration=grid_calibration,
        recent_comparisons=recent_comparisons,
        performance_metrics=performance_metrics,
        quality_indicators=quality_indicators,
        recommendations=recommendations,
        trends=trends
    )

# --- Floor Export Endpoints ---
@router.get('/floors/{floor_id}/export/svg')
def export_floor_svg(floor_id: str):
    floors = load_enhanced_floors()
    floor = next((f for f in floors if f.id == floor_id), None)
    if not floor or not floor.svg_path or not os.path.exists(floor.svg_path):
        raise HTTPException(status_code=404, detail='SVG file not found')
    return FileResponse(floor.svg_path, media_type='image/svg+xml', filename=f'{floor.name}.svg')

@router.get('/floors/{floor_id}/export/pdf')
def export_floor_pdf(floor_id: str):
    # Simulate PDF generation (in production, use a library like CairoSVG or ReportLab)
    floors = load_enhanced_floors()
    floor = next((f for f in floors if f.id == floor_id), None)
    if not floor:
        raise HTTPException(status_code=404, detail='Floor not found')
    pdf_path = floor.svg_path.replace('.svg', '.pdf')
    if not os.path.exists(pdf_path):
        # Simulate PDF creation by copying SVG (replace with real PDF generation)
        with open(pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n% Simulated PDF for floor export\n')
    return FileResponse(pdf_path, media_type='application/pdf', filename=f'{floor.name}.pdf')

@router.get('/floors/{floor_id}/export/bim')
def export_floor_bim(floor_id: str):
    # Simulate BIM export (in production, generate IFC/COBie or custom BIM JSON)
    floors = load_enhanced_floors()
    floor = next((f for f in floors if f.id == floor_id), None)
    if not floor:
        raise HTTPException(status_code=404, detail='Floor not found')
    bim_data = {
        'id': floor.id,
        'name': floor.name,
        'building_id': floor.building_id,
        'area': floor.floor_area,
        'height': floor.floor_height,
        'grid': floor.grid_calibration.dict() if floor.grid_calibration else None,
        'analytics': floor.analytics.dict() if floor.analytics else None,
        'objects': floor.properties.get('objects', []),
        'routes': floor.properties.get('routes', []),
        'metadata': floor.properties
    }
    return JSONResponse(content=bim_data, media_type='application/json')

@router.get('/floors/{floor_id}/export/json')
def export_floor_json(floor_id: str):
    floors = load_enhanced_floors()
    floor = next((f for f in floors if f.id == floor_id), None)
    if not floor:
        raise HTTPException(status_code=404, detail='Floor not found')
    return JSONResponse(content=floor.dict(), media_type='application/json')

@router.get('/floors/{floor_id}/export/csv')
def export_floor_csv(floor_id: str):
    floors = load_enhanced_floors()
    floor = next((f for f in floors if f.id == floor_id), None)
    if not floor:
        raise HTTPException(status_code=404, detail='Floor not found')
    # Flatten floor data for CSV
    output = io.StringIO()
    writer = csv.writer(output)
    # Write header
    writer.writerow(['id', 'name', 'building_id', 'area', 'height', 'type', 'created_at'])
    writer.writerow([
        floor.id, floor.name, floor.building_id, floor.floor_area, floor.floor_height, floor.floor_type, floor.created_at
    ])
    # Optionally, export objects and routes as separate rows
    objects = floor.properties.get('objects', [])
    if objects:
        writer.writerow([])
        writer.writerow(['Objects'])
        writer.writerow(['object_id', 'type', 'x', 'y', 'metadata'])
        for obj in objects:
            writer.writerow([
                obj.get('id'), obj.get('type'), obj.get('x'), obj.get('y'), json.dumps(obj.get('metadata', {}))
            ])
    routes = floor.properties.get('routes', [])
    if routes:
        writer.writerow([])
        writer.writerow(['Routes'])
        writer.writerow(['route_id', 'name', 'type', 'start', 'end', 'metadata'])
        for route in routes:
            writer.writerow([
                route.get('id'), route.get('name'), route.get('type'),
                json.dumps(route.get('start')), json.dumps(route.get('end')),
                json.dumps(route.get('metadata', {}))
            ])
    output.seek(0)
    return StreamingResponse(output, media_type='text/csv', headers={
        'Content-Disposition': f'attachment; filename={floor.name}.csv'
    })