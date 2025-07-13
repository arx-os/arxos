"""
Route Management Service
Handles route creation, validation, optimization, and analytics
"""

import json
import math
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4
import numpy as np
from dataclasses import dataclass
from enum import Enum

from models.route import (
    Route, RoutePoint, RouteGeometry, RouteSegment, RouteAnalytics,
    RouteConflict, RouteValidationResult, RouteOptimizationRequest
)

class RouteType(Enum):
    """Route type enumeration"""
    EVACUATION = "evacuation"
    ACCESS = "accessibility"
    MAINTENANCE = "maintenance"
    DELIVERY = "delivery"
    CUSTOM = "custom"

class RouteStatus(Enum):
    """Route status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ARCHIVED = "archived"

@dataclass
class RouteMetrics:
    """Comprehensive route metrics"""
    total_distance: float
    total_duration: float
    efficiency_score: float
    accessibility_score: float
    complexity_score: float
    safety_score: float
    congestion_score: float

class RouteManager:
    """Advanced route management service"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.routes_file = os.path.join(data_dir, "routes.json")
        self.analytics_file = os.path.join(data_dir, "route_analytics.json")
        self.conflicts_file = os.path.join(data_dir, "route_conflicts.json")
        self.performance_file = os.path.join(data_dir, "route_performance.json")
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
        
        # Performance thresholds
        self.performance_thresholds = {
            "distance": {"min": 0.1, "max": 1000.0},
            "duration": {"min": 1.0, "max": 3600.0},
            "efficiency": {"min": 0.0, "max": 1.0},
            "accessibility": {"min": 0.0, "max": 100.0}
        }
    
    def load_routes(self) -> List[Route]:
        """Load all routes from storage"""
        try:
            if os.path.exists(self.routes_file):
                with open(self.routes_file, 'r') as f:
                    routes_data = json.load(f)
                    return [Route(**route) for route in routes_data]
        except Exception as e:
            print(f"Error loading routes: {e}")
        return []
    
    def save_routes(self, routes: List[Route]) -> bool:
        """Save routes to storage"""
        try:
            with open(self.routes_file, 'w') as f:
                json.dump([route.dict() for route in routes], f, default=str, indent=2)
            return True
        except Exception as e:
            print(f"Error saving routes: {e}")
            return False
    
    def load_analytics(self) -> List[RouteAnalytics]:
        """Load route analytics from storage"""
        try:
            if os.path.exists(self.analytics_file):
                with open(self.analytics_file, 'r') as f:
                    analytics_data = json.load(f)
                    return [RouteAnalytics(**analytics) for analytics in analytics_data]
        except Exception as e:
            logger.error("error_loading_analytics", error=str(e))
        return []
    
    def save_analytics(self, analytics: List[RouteAnalytics]) -> bool:
        """Save route analytics to storage"""
        try:
            with open(self.analytics_file, 'w') as f:
                json.dump([a.dict() for a in analytics], f, default=str, indent=2)
            return True
        except Exception as e:
            logger.error("error_saving_analytics", error=str(e))
            return False
    
    def load_conflicts(self) -> List[RouteConflict]:
        """Load route conflicts from storage"""
        try:
            if os.path.exists(self.conflicts_file):
                with open(self.conflicts_file, 'r') as f:
                    conflicts_data = json.load(f)
                    return [RouteConflict(**conflict) for conflict in conflicts_data]
        except Exception as e:
            logger.error("error_loading_conflicts", error=str(e))
        return []
    
    def save_conflicts(self, conflicts: List[RouteConflict]) -> bool:
        """Save route conflicts to storage"""
        try:
            with open(self.conflicts_file, 'w') as f:
                json.dump([c.dict() for c in conflicts], f, default=str, indent=2)
            return True
        except Exception as e:
            logger.error("error_saving_conflicts", error=str(e))
            return False
    
    # Route Validation Methods
    def validate_route_geometry(self, geometry: RouteGeometry) -> List[str]:
        """Comprehensive route geometry validation"""
        errors = []
        
        # Basic validation
        if len(geometry.points) < 2:
            errors.append("Route must have at least 2 points")
            return errors
        
        # Point type validation
        if geometry.points[0].type != "start":
            errors.append("First point must be of type 'start'")
        if geometry.points[-1].type != "end":
            errors.append("Last point must be of type 'end'")
        
        # Coordinate validation
        for i, point in enumerate(geometry.points):
            if not self._is_valid_coordinate(point.x, point.y):
                errors.append(f"Invalid coordinates at point {i}: ({point.x}, {point.y})")
            
            if point.z is not None and not self._is_valid_coordinate(point.z):
                errors.append(f"Invalid Z coordinate at point {i}: {point.z}")
        
        # Distance validation
        for i in range(len(geometry.points) - 1):
            p1 = geometry.points[i]
            p2 = geometry.points[i + 1]
            
            # Check for duplicate consecutive points
            if self._points_equal(p1, p2):
                errors.append(f"Duplicate consecutive points at index {i}")
            
            # Check distance constraints
            distance = self._calculate_distance(p1, p2)
            if distance < self.performance_thresholds["distance"]["min"]:
                errors.append(f"Points too close at index {i}: {distance:.2f} units")
            elif distance > self.performance_thresholds["distance"]["max"]:
                errors.append(f"Points too far apart at index {i}: {distance:.2f} units")
        
        # Segment validation
        for i, segment in enumerate(geometry.segments):
            if not self._validate_segment(segment):
                errors.append(f"Invalid segment at index {i}")
        
        return errors
    
    def _is_valid_coordinate(self, coord: float) -> bool:
        """Check if coordinate is valid"""
        return isinstance(coord, (int, float)) and not math.isnan(coord) and not math.isinf(coord)
    
    def _points_equal(self, p1: RoutePoint, p2: RoutePoint) -> bool:
        """Check if two points are equal"""
        return (abs(p1.x - p2.x) < 0.001 and 
                abs(p1.y - p2.y) < 0.001 and 
                (p1.z is None and p2.z is None or 
                 p1.z is not None and p2.z is not None and abs(p1.z - p2.z) < 0.001))
    
    def _calculate_distance(self, p1: RoutePoint, p2: RoutePoint) -> float:
        """Calculate distance between two points"""
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        dz = (p2.z or 0) - (p1.z or 0)
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def _validate_segment(self, segment: RouteSegment) -> bool:
        """Validate a route segment"""
        if segment.distance is not None and segment.distance < 0:
            return False
        if segment.duration is not None and segment.duration < 0:
            return False
        return True
    
    def check_route_consistency(self, route: Route, all_routes: List[Route]) -> List[str]:
        """Check route consistency with other routes"""
        warnings = []
        
        for other_route in all_routes:
            if other_route.id == route.id:
                continue
            
            if other_route.floor_id != route.floor_id:
                continue
            
            # Check for overlapping bounding boxes
            if self._bounding_boxes_overlap(route.geometry.bounding_box, other_route.geometry.bounding_box):
                warnings.append(f"Route overlaps with route '{other_route.name}'")
            
            # Check for similar routes
            if self._routes_are_similar(route, other_route):
                warnings.append(f"Route is very similar to route '{other_route.name}'")
        
        return warnings
    
    def _bounding_boxes_overlap(self, bb1: Dict[str, float], bb2: Dict[str, float]) -> bool:
        """Check if two bounding boxes overlap"""
        if not bb1 or not bb2:
            return False
        
        return (bb1['max_x'] >= bb2['min_x'] and bb1['min_x'] <= bb2['max_x'] and
                bb1['max_y'] >= bb2['min_y'] and bb1['min_y'] <= bb2['max_y'])
    
    def _routes_are_similar(self, route1: Route, route2: Route) -> bool:
        """Check if two routes are very similar"""
        # Compare start and end points
        start_similarity = self._calculate_point_similarity(route1.start_point, route2.start_point)
        end_similarity = self._calculate_point_similarity(route1.end_point, route2.end_point)
        
        # Compare total distances
        distance_similarity = 1.0
        if route1.geometry.total_distance and route2.geometry.total_distance:
            distance_diff = abs(route1.geometry.total_distance - route2.geometry.total_distance)
            distance_similarity = 1.0 - (distance_diff / max(route1.geometry.total_distance, route2.geometry.total_distance))
        
        # Routes are similar if start/end points are close and distances are similar
        return (start_similarity > 0.8 and end_similarity > 0.8 and distance_similarity > 0.7)
    
    def _calculate_point_similarity(self, p1: RoutePoint, p2: RoutePoint) -> float:
        """Calculate similarity between two points (0-1)"""
        distance = self._calculate_distance(p1, p2)
        max_distance = 10.0  # Consider points similar if within 10 units
        return max(0, 1 - (distance / max_distance))
    
    # Route Conflict Detection
    def detect_route_conflicts(self, route: Route, all_routes: List[Route]) -> List[RouteConflict]:
        """Detect conflicts between routes"""
        conflicts = []
        
        for other_route in all_routes:
            if other_route.id == route.id:
                continue
            
            if other_route.floor_id != route.floor_id:
                continue
            
            # Check for intersections
            intersection_conflicts = self._detect_intersections(route, other_route)
            conflicts.extend(intersection_conflicts)
            
            # Check for proximity conflicts
            proximity_conflicts = self._detect_proximity_conflicts(route, other_route)
            conflicts.extend(proximity_conflicts)
            
            # Check for accessibility conflicts
            accessibility_conflicts = self._detect_accessibility_conflicts(route, other_route)
            conflicts.extend(accessibility_conflicts)
        
        return conflicts
    
    def _detect_intersections(self, route1: Route, route2: Route) -> List[RouteConflict]:
        """Detect route intersections"""
        conflicts = []
        
        for i, point1 in enumerate(route1.geometry.points[:-1]):
            for j, point2 in enumerate(route2.geometry.points[:-1]):
                if self._segments_intersect(
                    route1.geometry.points[i], route1.geometry.points[i+1],
                    route2.geometry.points[j], route2.geometry.points[j+1]
                ):
                    conflict = RouteConflict(
                        route_id=route1.id,
                        conflict_type="intersection",
                        severity="high",
                        description=f"Route intersects with route '{route2.name}'",
                        affected_routes=[route2.id],
                        location={"x": (point1.x + point2.x) / 2, "y": (point1.y + point2.y) / 2}
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_proximity_conflicts(self, route1: Route, route2: Route) -> List[RouteConflict]:
        """Detect proximity conflicts between routes"""
        conflicts = []
        min_distance = 5.0  # Minimum distance between routes
        
        for point1 in route1.geometry.points:
            for point2 in route2.geometry.points:
                distance = self._calculate_distance(point1, point2)
                if distance < min_distance:
                    conflict = RouteConflict(
                        route_id=route1.id,
                        conflict_type="proximity",
                        severity="medium",
                        description=f"Route too close to route '{route2.name}' (distance: {distance:.2f})",
                        affected_routes=[route2.id],
                        location={"x": point1.x, "y": point1.y}
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _detect_accessibility_conflicts(self, route1: Route, route2: Route) -> List[RouteConflict]:
        """Detect accessibility conflicts between routes"""
        conflicts = []
        
        # Check if routes have conflicting accessibility requirements
        if (route1.type == "accessibility" and route2.type == "accessibility" and
            route1.accessibility_score and route2.accessibility_score):
            
            # If both routes are accessibility routes but have very different scores
            score_diff = abs(route1.accessibility_score - route2.accessibility_score)
            if score_diff > 50:  # More than 50% difference
                conflict = RouteConflict(
                    route_id=route1.id,
                    conflict_type="accessibility",
                    severity="medium",
                    description=f"Accessibility conflict with route '{route2.name}' (score difference: {score_diff:.1f})",
                    affected_routes=[route2.id],
                    location={"x": route1.start_point.x, "y": route1.start_point.y}
                )
                conflicts.append(conflict)
        
        return conflicts
    
    def _segments_intersect(self, p1: RoutePoint, p2: RoutePoint, p3: RoutePoint, p4: RoutePoint) -> bool:
        """Check if two line segments intersect"""
        def ccw(A, B, C):
            return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)
        
        A = (p1.x, p1.y)
        B = (p2.x, p2.y)
        C = (p3.x, p3.y)
        D = (p4.x, p4.y)
        
        return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)
    
    # Route Performance Validation
    def validate_route_performance(self, route: Route) -> Dict[str, Any]:
        """Comprehensive route performance validation"""
        metrics = self._calculate_route_metrics(route)
        
        performance_data = {
            "performance_score": self._calculate_performance_score(metrics),
            "efficiency_rating": self._calculate_efficiency_rating(metrics),
            "accessibility_score": self._calculate_accessibility_score(route),
            "safety_score": self._calculate_safety_score(route),
            "warnings": self._generate_performance_warnings(metrics, route)
        }
        
        return performance_data
    
    def _calculate_route_metrics(self, route: Route) -> RouteMetrics:
        """Calculate comprehensive route metrics"""
        # Calculate total distance
        total_distance = 0.0
        for i in range(len(route.geometry.points) - 1):
            p1 = route.geometry.points[i]
            p2 = route.geometry.points[i + 1]
            total_distance += self._calculate_distance(p1, p2)
        
        # Calculate efficiency score (straightness)
        straight_line_distance = self._calculate_distance(route.start_point, route.end_point)
        efficiency_score = straight_line_distance / total_distance if total_distance > 0 else 0
        
        # Calculate complexity score (number of turns)
        complexity_score = self._calculate_complexity_score(route.geometry.points)
        
        # Calculate accessibility score
        accessibility_score = self._calculate_accessibility_score(route)
        
        # Calculate safety score
        safety_score = self._calculate_safety_score(route)
        
        # Calculate congestion score
        congestion_score = self._calculate_congestion_score(route)
        
        # Estimate duration based on distance and route type
        total_duration = self._estimate_duration(total_distance, route.type, route.geometry.segments)
        
        return RouteMetrics(
            total_distance=total_distance,
            total_duration=total_duration,
            efficiency_score=efficiency_score,
            accessibility_score=accessibility_score,
            complexity_score=complexity_score,
            safety_score=safety_score,
            congestion_score=congestion_score
        )
    
    def _calculate_complexity_score(self, points: List[RoutePoint]) -> float:
        """Calculate route complexity based on number of turns"""
        if len(points) < 3:
            return 0.0
        
        turns = 0
        for i in range(1, len(points) - 1):
            # Calculate angle between three consecutive points
            angle = self._calculate_angle(points[i-1], points[i], points[i+1])
            if abs(angle) > 15:  # Consider it a turn if angle > 15 degrees
                turns += 1
        
        # Normalize complexity score (0-1)
        max_expected_turns = len(points) - 2
        return turns / max_expected_turns if max_expected_turns > 0 else 0
    
    def _calculate_angle(self, p1: RoutePoint, p2: RoutePoint, p3: RoutePoint) -> float:
        """Calculate angle between three points"""
        # Vector 1: p1 to p2
        v1x = p2.x - p1.x
        v1y = p2.y - p1.y
        
        # Vector 2: p2 to p3
        v2x = p3.x - p2.x
        v2y = p3.y - p2.y
        
        # Calculate angle
        dot_product = v1x * v2x + v1y * v2y
        mag1 = math.sqrt(v1x * v1x + v1y * v1y)
        mag2 = math.sqrt(v2x * v2x + v2y * v2y)
        
        if mag1 == 0 or mag2 == 0:
            return 0
        
        cos_angle = dot_product / (mag1 * mag2)
        cos_angle = max(-1, min(1, cos_angle))  # Clamp to [-1, 1]
        
        return math.degrees(math.acos(cos_angle))
    
    def _calculate_accessibility_score(self, route: Route) -> float:
        """Calculate accessibility score based on route features"""
        if not route.geometry.segments:
            return 50.0  # Default score
        
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
                if segment.accessibility.get("handrail_available", False):
                    accessibility_features += 0.5
        
        # Base score for having segments
        base_score = 30.0
        
        # Additional score for accessibility features
        feature_score = (accessibility_features / total_segments) * 70.0
        
        return min(100.0, base_score + feature_score)
    
    def _calculate_safety_score(self, route: Route) -> float:
        """Calculate safety score based on route characteristics"""
        # Base safety score
        safety_score = 70.0
        
        # Reduce score for long routes (more exposure)
        if route.geometry.total_distance and route.geometry.total_distance > 200:
            safety_score -= 10
        
        # Reduce score for complex routes (more turns = more risk)
        complexity_score = self._calculate_complexity_score(route.geometry.points)
        safety_score -= complexity_score * 20
        
        # Increase score for evacuation routes
        if route.type == "evacuation":
            safety_score += 15
        
        return max(0.0, min(100.0, safety_score))
    
    def _calculate_congestion_score(self, route: Route) -> float:
        """Calculate congestion score based on route usage"""
        # This would typically use real-time data
        # For now, use a simple heuristic based on route type
        congestion_scores = {
            "evacuation": 20.0,  # Low congestion for evacuation routes
            "accessibility": 30.0,  # Medium congestion for accessibility routes
            "maintenance": 40.0,  # Higher congestion for maintenance routes
            "delivery": 50.0,  # High congestion for delivery routes
            "custom": 35.0  # Default congestion for custom routes
        }
        
        return congestion_scores.get(route.type, 35.0)
    
    def _estimate_duration(self, distance: float, route_type: str, segments: List[RouteSegment]) -> float:
        """Estimate route duration based on distance and route type"""
        # Base walking speed (meters per second)
        base_speed = 1.4  # ~5 km/h
        
        # Adjust speed based on route type
        speed_multipliers = {
            "evacuation": 1.5,  # Faster for evacuation
            "accessibility": 0.8,  # Slower for accessibility
            "maintenance": 1.0,  # Normal speed
            "delivery": 1.2,  # Slightly faster for delivery
            "custom": 1.0  # Normal speed
        }
        
        speed = base_speed * speed_multipliers.get(route_type, 1.0)
        
        # Adjust for segments with different speeds
        for segment in segments:
            if segment.type == "elevator":
                speed *= 2.0  # Elevators are faster
            elif segment.type == "stairs":
                speed *= 0.7  # Stairs are slower
            elif segment.type == "ramp":
                speed *= 0.9  # Ramps are slightly slower
        
        return distance / speed if speed > 0 else 0
    
    def _calculate_performance_score(self, metrics: RouteMetrics) -> float:
        """Calculate overall performance score"""
        # Weighted combination of various metrics
        weights = {
            "efficiency": 0.3,
            "accessibility": 0.25,
            "safety": 0.25,
            "congestion": 0.2
        }
        
        # Normalize congestion score (lower is better)
        normalized_congestion = 1.0 - (metrics.congestion_score / 100.0)
        
        performance_score = (
            metrics.efficiency_score * weights["efficiency"] +
            (metrics.accessibility_score / 100.0) * weights["accessibility"] +
            (metrics.safety_score / 100.0) * weights["safety"] +
            normalized_congestion * weights["congestion"]
        ) * 100
        
        return max(0.0, min(100.0, performance_score))
    
    def _calculate_efficiency_rating(self, metrics: RouteMetrics) -> float:
        """Calculate efficiency rating (0-10)"""
        # Base efficiency on straightness
        efficiency = metrics.efficiency_score * 10
        
        # Penalize for complexity
        efficiency -= metrics.complexity_score * 3
        
        return max(0.0, min(10.0, efficiency))
    
    def _generate_performance_warnings(self, metrics: RouteMetrics, route: Route) -> List[str]:
        """Generate performance warnings"""
        warnings = []
        
        if metrics.total_distance > 200:
            warnings.append("Route is quite long - consider breaking into segments")
        
        if metrics.efficiency_score < 0.5:
            warnings.append("Route has low efficiency - consider optimization")
        
        if metrics.complexity_score > 0.7:
            warnings.append("Route is complex with many turns")
        
        if metrics.accessibility_score < 50:
            warnings.append("Route has limited accessibility features")
        
        if metrics.safety_score < 60:
            warnings.append("Route has safety concerns")
        
        return warnings
    
    # Route Optimization
    def optimize_route(self, route: Route, optimization_type: str, constraints: Optional[Dict[str, Any]] = None) -> Route:
        """Optimize a route based on specified criteria"""
        
        if optimization_type == "distance":
            return self._optimize_for_distance(route, constraints)
        elif optimization_type == "time":
            return self._optimize_for_time(route, constraints)
        elif optimization_type == "accessibility":
            return self._optimize_for_accessibility(route, constraints)
        elif optimization_type == "efficiency":
            return self._optimize_for_efficiency(route, constraints)
        else:
            return route  # Return original if optimization type not recognized
    
    def _optimize_for_distance(self, route: Route, constraints: Optional[Dict[str, Any]] = None) -> Route:
        """Optimize route for shortest distance"""
        # Use A* algorithm for pathfinding
        optimized_points = self._a_star_optimization(route, "distance")
        
        # Create optimized geometry
        optimized_geometry = RouteGeometry(points=optimized_points)
        optimized_geometry.calculate_metrics()
        
        # Create optimized route
        optimized_route = route.copy()
        optimized_route.id = str(uuid4())
        optimized_route.name = f"{route.name} (Distance Optimized)"
        optimized_route.geometry = optimized_geometry
        optimized_route.is_optimized = True
        optimized_route.created_at = datetime.utcnow()
        
        return optimized_route
    
    def _optimize_for_time(self, route: Route, constraints: Optional[Dict[str, Any]] = None) -> Route:
        """Optimize route for fastest time"""
        # Prefer faster segments (elevators, escalators)
        optimized_points = self._a_star_optimization(route, "time")
        
        optimized_geometry = RouteGeometry(points=optimized_points)
        optimized_geometry.calculate_metrics()
        
        optimized_route = route.copy()
        optimized_route.id = str(uuid4())
        optimized_route.name = f"{route.name} (Time Optimized)"
        optimized_route.geometry = optimized_geometry
        optimized_route.is_optimized = True
        optimized_route.created_at = datetime.utcnow()
        
        return optimized_route
    
    def _optimize_for_accessibility(self, route: Route, constraints: Optional[Dict[str, Any]] = None) -> Route:
        """Optimize route for accessibility"""
        # Prefer accessible segments (ramps, elevators)
        optimized_points = self._a_star_optimization(route, "accessibility")
        
        optimized_geometry = RouteGeometry(points=optimized_points)
        optimized_geometry.calculate_metrics()
        
        optimized_route = route.copy()
        optimized_route.id = str(uuid4())
        optimized_route.name = f"{route.name} (Accessibility Optimized)"
        optimized_route.geometry = optimized_geometry
        optimized_route.is_optimized = True
        optimized_route.created_at = datetime.utcnow()
        
        return optimized_route
    
    def _optimize_for_efficiency(self, route: Route, constraints: Optional[Dict[str, Any]] = None) -> Route:
        """Optimize route for general efficiency"""
        # Balance distance, time, and accessibility
        optimized_points = self._a_star_optimization(route, "efficiency")
        
        optimized_geometry = RouteGeometry(points=optimized_points)
        optimized_geometry.calculate_metrics()
        
        optimized_route = route.copy()
        optimized_route.id = str(uuid4())
        optimized_route.name = f"{route.name} (Efficiency Optimized)"
        optimized_route.geometry = optimized_geometry
        optimized_route.is_optimized = True
        optimized_route.created_at = datetime.utcnow()
        
        return optimized_route
    
    def _a_star_optimization(self, route: Route, optimization_type: str) -> List[RoutePoint]:
        """A* pathfinding algorithm for route optimization"""
        # This is a simplified A* implementation
        # In production, you'd have a proper graph representation of the building
        
        start_point = route.start_point
        end_point = route.end_point
        waypoints = route.geometry.points[1:-1]  # Exclude start and end points
        
        # For now, return a simplified path
        # In a real implementation, you'd:
        # 1. Create a graph of all possible paths
        # 2. Use A* to find the optimal path
        # 3. Consider constraints and preferences
        
        optimized_points = [start_point]
        
        # Add waypoints based on optimization type
        if optimization_type == "distance":
            # Minimize number of waypoints
            for i, point in enumerate(waypoints):
                if i % 3 == 0 or point.type == "checkpoint":
                    optimized_points.append(point)
        elif optimization_type == "time":
            # Prefer faster segments
            optimized_points.extend(waypoints)
        elif optimization_type == "accessibility":
            # Prefer accessible segments
            optimized_points.extend(waypoints)
        else:  # efficiency
            # Balance approach
            for i, point in enumerate(waypoints):
                if i % 2 == 0 or point.type == "checkpoint":
                    optimized_points.append(point)
        
        optimized_points.append(end_point)
        
        return optimized_points
    
    # Analytics and Reporting
    def generate_route_report(self, route: Route) -> Dict[str, Any]:
        """Generate comprehensive route report"""
        metrics = self._calculate_route_metrics(route)
        
        report = {
            "route_id": route.id,
            "route_name": route.name,
            "route_type": route.type,
            "floor_id": route.floor_id,
            "building_id": route.building_id,
            "created_at": route.created_at.isoformat(),
            "updated_at": route.updated_at.isoformat(),
            "metrics": {
                "total_distance": metrics.total_distance,
                "total_duration": metrics.total_duration,
                "efficiency_score": metrics.efficiency_score,
                "accessibility_score": metrics.accessibility_score,
                "complexity_score": metrics.complexity_score,
                "safety_score": metrics.safety_score,
                "congestion_score": metrics.congestion_score
            },
            "performance": {
                "performance_score": self._calculate_performance_score(metrics),
                "efficiency_rating": self._calculate_efficiency_rating(metrics),
                "validation_status": route.validation_status,
                "validation_errors": route.validation_errors,
                "validation_warnings": route.validation_warnings
            },
            "geometry": {
                "point_count": len(route.geometry.points),
                "segment_count": len(route.geometry.segments),
                "bounding_box": route.geometry.bounding_box
            },
            "tags": route.tags,
            "constraints": route.constraints,
            "requirements": route.requirements
        }
        
        return report
    
    def generate_floor_route_summary(self, floor_id: str) -> Dict[str, Any]:
        """Generate summary of all routes on a floor"""
        routes = self.load_routes()
        floor_routes = [r for r in routes if r.floor_id == floor_id]
        
        if not floor_routes:
            return {"error": "No routes found for floor"}
        
        # Calculate aggregate metrics
        total_routes = len(floor_routes)
        total_distance = sum(r.geometry.total_distance or 0 for r in floor_routes)
        avg_performance = sum(r.performance_score or 0 for r in floor_routes) / total_routes
        
        # Route type distribution
        type_distribution = {}
        for route in floor_routes:
            route_type = route.type
            type_distribution[route_type] = type_distribution.get(route_type, 0) + 1
        
        # Validation status distribution
        validation_distribution = {}
        for route in floor_routes:
            status = route.validation_status
            validation_distribution[status] = validation_distribution.get(status, 0) + 1
        
        summary = {
            "floor_id": floor_id,
            "total_routes": total_routes,
            "total_distance": total_distance,
            "average_performance_score": avg_performance,
            "route_type_distribution": type_distribution,
            "validation_status_distribution": validation_distribution,
            "routes": [self.generate_route_report(route) for route in floor_routes]
        }
        
        return summary 