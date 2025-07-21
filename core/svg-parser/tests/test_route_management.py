"""
Comprehensive tests for Route Management System
Tests CRUD operations, validation, optimization, and analytics
"""

import pytest
import json
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch

from core.models.route
    Route, RoutePoint, RouteGeometry, RouteSegment, RouteCreateRequest,
    RouteUpdateRequest, RouteAnalytics, RouteConflict, RouteValidationResult
)
from core.services.route_manager

class TestRouteManager:
    """Test suite for RouteManager service"""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create temporary data directory for tests"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def route_manager(self, temp_data_dir):
        """Create RouteManager instance with temporary data directory"""
        return RouteManager(data_dir=temp_data_dir)
    
    @pytest.fixture
    def sample_route_points(self):
        """Create sample route points for testing"""
        return [
            RoutePoint(x=0, y=0, type="start", name="Start"),
            RoutePoint(x=10, y=10, type="waypoint", name="Waypoint 1"),
            RoutePoint(x=20, y=20, type="waypoint", name="Waypoint 2"),
            RoutePoint(x=30, y=30, type="end", name="End")
        ]
    
    @pytest.fixture
    def sample_route_geometry(self, sample_route_points):
        """Create sample route geometry"""
        geometry = RouteGeometry(points=sample_route_points)
        geometry.calculate_metrics()
        return geometry
    
    @pytest.fixture
    def sample_route(self, sample_route_geometry):
        """Create sample route for testing"""
        return Route(
            name="Test Route",
            description="A test route",
            floor_id="floor-123",
            building_id="building-456",
            type="custom",
            priority="medium",
            geometry=sample_route_geometry,
            start_point=sample_route_geometry.points[0],
            end_point=sample_route_geometry.points[-1],
            is_active=True,
            is_public=True,
            tags=["test", "sample"]
        )
    
    def test_route_manager_initialization(self, temp_data_dir):
        """Test RouteManager initialization"""
        manager = RouteManager(data_dir=temp_data_dir)
        
        assert manager.data_dir == temp_data_dir
        assert os.path.exists(temp_data_dir)
        assert manager.routes_file == os.path.join(temp_data_dir, "routes.json")
        assert manager.analytics_file == os.path.join(temp_data_dir, "route_analytics.json")
        assert manager.conflicts_file == os.path.join(temp_data_dir, "route_conflicts.json")
    
    def test_load_save_routes(self, route_manager, sample_route):
        """Test loading and saving routes"""
        # Save routes
        routes = [sample_route]
        success = route_manager.save_routes(routes)
        assert success is True
        
        # Load routes
        loaded_routes = route_manager.load_routes()
        assert len(loaded_routes) == 1
        assert loaded_routes[0].name == sample_route.name
        assert loaded_routes[0].id == sample_route.id
    
    def test_load_save_analytics(self, route_manager):
        """Test loading and saving route analytics"""
        analytics = [
            RouteAnalytics(
                route_id="route-123",
                total_usage=10,
                average_duration=120.5,
                success_rate=95.0,
                user_ratings=4.2
            )
        ]
        
        success = route_manager.save_analytics(analytics)
        assert success is True
        
        loaded_analytics = route_manager.load_analytics()
        assert len(loaded_analytics) == 1
        assert loaded_analytics[0].route_id == "route-123"
        assert loaded_analytics[0].total_usage == 10
    
    def test_load_save_conflicts(self, route_manager):
        """Test loading and saving route conflicts"""
        conflicts = [
            RouteConflict(
                route_id="route-123",
                conflict_type="intersection",
                severity="high",
                description="Route intersects with another route",
                affected_routes=["route-456"]
            )
        ]
        
        success = route_manager.save_conflicts(conflicts)
        assert success is True
        
        loaded_conflicts = route_manager.load_conflicts()
        assert len(loaded_conflicts) == 1
        assert loaded_conflicts[0].route_id == "route-123"
        assert loaded_conflicts[0].conflict_type == "intersection"

class TestRouteValidation:
    """Test suite for route validation"""
    
    @pytest.fixture
    def route_manager(self, temp_data_dir):
        return RouteManager(data_dir=temp_data_dir)
    
    def test_validate_route_geometry_valid(self, route_manager, sample_route_geometry):
        """Test validation of valid route geometry"""
        errors = route_manager.validate_route_geometry(sample_route_geometry)
        assert len(errors) == 0
    
    def test_validate_route_geometry_insufficient_points(self, route_manager):
        """Test validation with insufficient points"""
        geometry = RouteGeometry(points=[
            RoutePoint(x=0, y=0, type="start")
        ])
        
        errors = route_manager.validate_route_geometry(geometry)
        assert len(errors) == 1
        assert "at least 2 points" in errors[0]
    
    def test_validate_route_geometry_invalid_start_point(self, route_manager):
        """Test validation with invalid start point type"""
        geometry = RouteGeometry(points=[
            RoutePoint(x=0, y=0, type="waypoint"),  # Should be "start"
            RoutePoint(x=10, y=10, type="end")
        ])
        
        errors = route_manager.validate_route_geometry(geometry)
        assert len(errors) == 1
        assert "First point must be of type 'start'" in errors[0]
    
    def test_validate_route_geometry_invalid_end_point(self, route_manager):
        """Test validation with invalid end point type"""
        geometry = RouteGeometry(points=[
            RoutePoint(x=0, y=0, type="start"),
            RoutePoint(x=10, y=10, type="waypoint")  # Should be "end"
        ])
        
        errors = route_manager.validate_route_geometry(geometry)
        assert len(errors) == 1
        assert "Last point must be of type 'end'" in errors[0]
    
    def test_validate_route_geometry_duplicate_points(self, route_manager):
        """Test validation with duplicate consecutive points"""
        geometry = RouteGeometry(points=[
            RoutePoint(x=0, y=0, type="start"),
            RoutePoint(x=0, y=0, type="end")  # Same coordinates as start
        ])
        
        errors = route_manager.validate_route_geometry(geometry)
        assert len(errors) == 1
        assert "Duplicate consecutive points" in errors[0]
    
    def test_validate_route_geometry_points_too_close(self, route_manager):
        """Test validation with points too close together"""
        geometry = RouteGeometry(points=[
            RoutePoint(x=0, y=0, type="start"),
            RoutePoint(x=0.05, y=0.05, type="end")  # Very close to start
        ])
        
        errors = route_manager.validate_route_geometry(geometry)
        assert len(errors) == 1
        assert "Points too close" in errors[0]
    
    def test_validate_route_geometry_points_too_far(self, route_manager):
        """Test validation with points too far apart"""
        geometry = RouteGeometry(points=[
            RoutePoint(x=0, y=0, type="start"),
            RoutePoint(x=2000, y=2000, type="end")  # Very far from start
        ])
        
        errors = route_manager.validate_route_geometry(geometry)
        assert len(errors) == 1
        assert "Points too far apart" in errors[0]
    
    def test_validate_route_geometry_invalid_coordinates(self, route_manager):
        """Test validation with invalid coordinates"""
        geometry = RouteGeometry(points=[
            RoutePoint(x=float('nan'), y=0, type="start"),
            RoutePoint(x=10, y=10, type="end")
        ])
        
        errors = route_manager.validate_route_geometry(geometry)
        assert len(errors) == 1
        assert "Invalid coordinates" in errors[0]

class TestRouteConsistency:
    """Test suite for route consistency checking"""
    
    @pytest.fixture
    def route_manager(self, temp_data_dir):
        return RouteManager(data_dir=temp_data_dir)
    
    def test_check_route_consistency_no_overlap(self, route_manager, sample_route):
        """Test consistency check with no overlapping routes"""
        other_route = Route(
            name="Other Route",
            floor_id="floor-456",  # Different floor
            building_id="building-456",
            type="custom",
            geometry=RouteGeometry(points=[
                RoutePoint(x=100, y=100, type="start"),
                RoutePoint(x=110, y=110, type="end")
            ]),
            start_point=RoutePoint(x=100, y=100, type="start"),
            end_point=RoutePoint(x=110, y=110, type="end")
        )
        
        warnings = route_manager.check_route_consistency(sample_route, [other_route])
        assert len(warnings) == 0
    
    def test_check_route_consistency_overlap(self, route_manager, sample_route):
        """Test consistency check with overlapping routes"""
        overlapping_route = Route(
            name="Overlapping Route",
            floor_id=sample_route.floor_id,  # Same floor
            building_id=sample_route.building_id,
            type="custom",
            geometry=RouteGeometry(points=[
                RoutePoint(x=5, y=5, type="start"),
                RoutePoint(x=15, y=15, type="end")
            ]),
            start_point=RoutePoint(x=5, y=5, type="start"),
            end_point=RoutePoint(x=15, y=15, type="end")
        )
        
        warnings = route_manager.check_route_consistency(sample_route, [overlapping_route])
        assert len(warnings) == 1
        assert "overlaps" in warnings[0]

class TestRouteConflictDetection:
    """Test suite for route conflict detection"""
    
    @pytest.fixture
    def route_manager(self, temp_data_dir):
        return RouteManager(data_dir=temp_data_dir)
    
    def test_detect_route_conflicts_no_conflicts(self, route_manager, sample_route):
        """Test conflict detection with no conflicts"""
        other_route = Route(
            name="Other Route",
            floor_id="floor-456",  # Different floor
            building_id="building-456",
            type="custom",
            geometry=RouteGeometry(points=[
                RoutePoint(x=100, y=100, type="start"),
                RoutePoint(x=110, y=110, type="end")
            ]),
            start_point=RoutePoint(x=100, y=100, type="start"),
            end_point=RoutePoint(x=110, y=110, type="end")
        )
        
        conflicts = route_manager.detect_route_conflicts(sample_route, [other_route])
        assert len(conflicts) == 0
    
    def test_detect_route_conflicts_intersection(self, route_manager, sample_route):
        """Test conflict detection with route intersection"""
        intersecting_route = Route(
            name="Intersecting Route",
            floor_id=sample_route.floor_id,
            building_id=sample_route.building_id,
            type="custom",
            geometry=RouteGeometry(points=[
                RoutePoint(x=15, y=5, type="start"),
                RoutePoint(x=15, y=25, type="end")
            ]),
            start_point=RoutePoint(x=15, y=5, type="start"),
            end_point=RoutePoint(x=15, y=25, type="end")
        )
        
        conflicts = route_manager.detect_route_conflicts(sample_route, [intersecting_route])
        assert len(conflicts) > 0
        assert any(c.conflict_type == "intersection" for c in conflicts)
    
    def test_detect_route_conflicts_proximity(self, route_manager, sample_route):
        """Test conflict detection with proximity conflicts"""
        proximate_route = Route(
            name="Proximate Route",
            floor_id=sample_route.floor_id,
            building_id=sample_route.building_id,
            type="custom",
            geometry=RouteGeometry(points=[
                RoutePoint(x=1, y=1, type="start"),
                RoutePoint(x=11, y=11, type="end")
            ]),
            start_point=RoutePoint(x=1, y=1, type="start"),
            end_point=RoutePoint(x=11, y=11, type="end")
        )
        
        conflicts = route_manager.detect_route_conflicts(sample_route, [proximate_route])
        assert len(conflicts) > 0
        assert any(c.conflict_type == "proximity" for c in conflicts)

class TestRoutePerformanceValidation:
    """Test suite for route performance validation"""
    
    @pytest.fixture
    def route_manager(self, temp_data_dir):
        return RouteManager(data_dir=temp_data_dir)
    
    def test_validate_route_performance(self, route_manager, sample_route):
        """Test route performance validation"""
        performance_data = route_manager.validate_route_performance(sample_route)
        
        assert "performance_score" in performance_data
        assert "efficiency_rating" in performance_data
        assert "accessibility_score" in performance_data
        assert "safety_score" in performance_data
        assert "warnings" in performance_data
        
        assert isinstance(performance_data["performance_score"], (int, float))
        assert isinstance(performance_data["efficiency_rating"], (int, float))
        assert isinstance(performance_data["accessibility_score"], (int, float))
        assert isinstance(performance_data["safety_score"], (int, float))
        assert isinstance(performance_data["warnings"], list)
    
    def test_calculate_route_metrics(self, route_manager, sample_route):
        """Test route metrics calculation"""
        metrics = route_manager._calculate_route_metrics(sample_route)
        
        assert isinstance(metrics, RouteMetrics)
        assert metrics.total_distance > 0
        assert metrics.total_duration > 0
        assert 0 <= metrics.efficiency_score <= 1
        assert 0 <= metrics.accessibility_score <= 100
        assert 0 <= metrics.complexity_score <= 1
        assert 0 <= metrics.safety_score <= 100
        assert 0 <= metrics.congestion_score <= 100
    
    def test_calculate_performance_score(self, route_manager):
        """Test performance score calculation"""
        metrics = RouteMetrics(
            total_distance=100.0,
            total_duration=120.0,
            efficiency_score=0.8,
            accessibility_score=75.0,
            complexity_score=0.3,
            safety_score=85.0,
            congestion_score=25.0
        )
        
        score = route_manager._calculate_performance_score(metrics)
        assert 0 <= score <= 100
        assert isinstance(score, float)
    
    def test_calculate_efficiency_rating(self, route_manager):
        """Test efficiency rating calculation"""
        metrics = RouteMetrics(
            total_distance=100.0,
            total_duration=120.0,
            efficiency_score=0.8,
            accessibility_score=75.0,
            complexity_score=0.3,
            safety_score=85.0,
            congestion_score=25.0
        )
        
        rating = route_manager._calculate_efficiency_rating(metrics)
        assert 0 <= rating <= 10
        assert isinstance(rating, float)

class TestRouteOptimization:
    """Test suite for route optimization"""
    
    @pytest.fixture
    def route_manager(self, temp_data_dir):
        return RouteManager(data_dir=temp_data_dir)
    
    def test_optimize_route_distance(self, route_manager, sample_route):
        """Test route optimization for distance"""
        optimized_route = route_manager.optimize_route(sample_route, "distance")
        
        assert optimized_route.id != sample_route.id
        assert optimized_route.name == f"{sample_route.name} (Distance Optimized)"
        assert optimized_route.is_optimized is True
        assert len(optimized_route.geometry.points) <= len(sample_route.geometry.points)
    
    def test_optimize_route_time(self, route_manager, sample_route):
        """Test route optimization for time"""
        optimized_route = route_manager.optimize_route(sample_route, "time")
        
        assert optimized_route.id != sample_route.id
        assert optimized_route.name == f"{sample_route.name} (Time Optimized)"
        assert optimized_route.is_optimized is True
    
    def test_optimize_route_accessibility(self, route_manager, sample_route):
        """Test route optimization for accessibility"""
        optimized_route = route_manager.optimize_route(sample_route, "accessibility")
        
        assert optimized_route.id != sample_route.id
        assert optimized_route.name == f"{sample_route.name} (Accessibility Optimized)"
        assert optimized_route.is_optimized is True
    
    def test_optimize_route_efficiency(self, route_manager, sample_route):
        """Test route optimization for efficiency"""
        optimized_route = route_manager.optimize_route(sample_route, "efficiency")
        
        assert optimized_route.id != sample_route.id
        assert optimized_route.name == f"{sample_route.name} (Efficiency Optimized)"
        assert optimized_route.is_optimized is True
    
    def test_optimize_route_unknown_type(self, route_manager, sample_route):
        """Test route optimization with unknown type"""
        optimized_route = route_manager.optimize_route(sample_route, "unknown")
        
        # Should return original route unchanged
        assert optimized_route.id == sample_route.id
        assert optimized_route.name == sample_route.name
        assert optimized_route.is_optimized is False

class TestRouteAnalytics:
    """Test suite for route analytics and reporting"""
    
    @pytest.fixture
    def route_manager(self, temp_data_dir):
        return RouteManager(data_dir=temp_data_dir)
    
    def test_generate_route_report(self, route_manager, sample_route):
        """Test route report generation"""
        report = route_manager.generate_route_report(sample_route)
        
        assert report["route_id"] == sample_route.id
        assert report["route_name"] == sample_route.name
        assert report["route_type"] == sample_route.type
        assert "metrics" in report
        assert "performance" in report
        assert "geometry" in report
        
        metrics = report["metrics"]
        assert "total_distance" in metrics
        assert "total_duration" in metrics
        assert "efficiency_score" in metrics
        assert "accessibility_score" in metrics
        
        performance = report["performance"]
        assert "performance_score" in performance
        assert "efficiency_rating" in performance
        assert "validation_status" in performance
    
    def test_generate_floor_route_summary(self, route_manager, sample_route):
        """Test floor route summary generation"""
        # Save a route first
        route_manager.save_routes([sample_route])
        
        summary = route_manager.generate_floor_route_summary(sample_route.floor_id)
        
        assert summary["floor_id"] == sample_route.floor_id
        assert summary["total_routes"] == 1
        assert summary["total_distance"] > 0
        assert "route_type_distribution" in summary
        assert "validation_status_distribution" in summary
        assert len(summary["routes"]) == 1
    
    def test_generate_floor_route_summary_no_routes(self, route_manager):
        """Test floor route summary with no routes"""
        summary = route_manager.generate_floor_route_summary("nonexistent-floor")
        
        assert "error" in summary
        assert "No routes found" in summary["error"]

class TestRouteCRUDOperations:
    """Test suite for route CRUD operations"""
    
    @pytest.fixture
    def route_manager(self, temp_data_dir):
        return RouteManager(data_dir=temp_data_dir)
    
    def test_create_route(self, route_manager, sample_route_geometry):
        """Test route creation"""
        # Create route request
        route_request = RouteCreateRequest(
            name="New Test Route",
            description="A new test route",
            floor_id="floor-123",
            building_id="building-456",
            type="custom",
            priority="medium",
            geometry=sample_route_geometry,
            is_public=True,
            tags=["test", "new"]
        )
        
        # In a real implementation, this would be handled by the API endpoint
        # For testing, we'll create the route directly
        route = Route(
            name=route_request.name,
            description=route_request.description,
            floor_id=route_request.floor_id,
            building_id=route_request.building_id,
            type=route_request.type,
            priority=route_request.priority,
            geometry=route_request.geometry,
            start_point=route_request.geometry.points[0],
            end_point=route_request.geometry.points[-1],
            is_public=route_request.is_public,
            tags=route_request.tags
        )
        
        # Save route
        routes = [route]
        success = route_manager.save_routes(routes)
        assert success is True
        
        # Verify route was saved
        loaded_routes = route_manager.load_routes()
        assert len(loaded_routes) == 1
        assert loaded_routes[0].name == route_request.name
    
    def test_update_route(self, route_manager, sample_route):
        """Test route update"""
        # Save original route
        route_manager.save_routes([sample_route])
        
        # Create update request
        update_request = RouteUpdateRequest(
            name="Updated Route Name",
            description="Updated description",
            priority="high"
        )
        
        # Update route
        sample_route.name = update_request.name
        sample_route.description = update_request.description
        sample_route.priority = update_request.priority
        sample_route.updated_at = datetime.utcnow()
        
        # Save updated route
        route_manager.save_routes([sample_route])
        
        # Verify update
        loaded_routes = route_manager.load_routes()
        assert len(loaded_routes) == 1
        assert loaded_routes[0].name == "Updated Route Name"
        assert loaded_routes[0].description == "Updated description"
        assert loaded_routes[0].priority == "high"
    
    def test_delete_route(self, route_manager, sample_route):
        """Test route deletion"""
        # Save route
        route_manager.save_routes([sample_route])
        
        # Verify route exists
        loaded_routes = route_manager.load_routes()
        assert len(loaded_routes) == 1
        
        # Delete route (remove from list)
        routes = route_manager.load_routes()
        routes = [r for r in routes if r.id != sample_route.id]
        route_manager.save_routes(routes)
        
        # Verify route was deleted
        loaded_routes = route_manager.load_routes()
        assert len(loaded_routes) == 0

class TestRouteIntegration:
    """Integration tests for route management system"""
    
    @pytest.fixture
    def route_manager(self, temp_data_dir):
        return RouteManager(data_dir=temp_data_dir)
    
    def test_full_route_lifecycle(self, route_manager, sample_route_geometry):
        """Test complete route lifecycle: create, validate, optimize, analyze, delete"""
        
        # 1. Create route
        route = Route(
            name="Lifecycle Test Route",
            description="Testing full lifecycle",
            floor_id="floor-123",
            building_id="building-456",
            type="custom",
            priority="medium",
            geometry=sample_route_geometry,
            start_point=sample_route_geometry.points[0],
            end_point=sample_route_geometry.points[-1],
            is_active=True,
            is_public=True
        )
        
        # 2. Validate route
        geometry_errors = route_manager.validate_route_geometry(route.geometry)
        assert len(geometry_errors) == 0
        
        # 3. Calculate performance
        performance_data = route_manager.validate_route_performance(route)
        assert "performance_score" in performance_data
        
        # 4. Save route
        route_manager.save_routes([route])
        
        # 5. Load and verify
        loaded_routes = route_manager.load_routes()
        assert len(loaded_routes) == 1
        assert loaded_routes[0].name == "Lifecycle Test Route"
        
        # 6. Optimize route
        optimized_route = route_manager.optimize_route(route, "efficiency")
        assert optimized_route.is_optimized is True
        
        # 7. Generate report
        report = route_manager.generate_route_report(route)
        assert report["route_name"] == "Lifecycle Test Route"
        
        # 8. Delete route
        routes = route_manager.load_routes()
        routes = [r for r in routes if r.id != route.id]
        route_manager.save_routes(routes)
        
        # 9. Verify deletion
        loaded_routes = route_manager.load_routes()
        assert len(loaded_routes) == 0
    
    def test_route_conflict_detection_integration(self, route_manager, sample_route):
        """Test integration of route conflict detection"""
        
        # Create conflicting route
        conflicting_route = Route(
            name="Conflicting Route",
            floor_id=sample_route.floor_id,
            building_id=sample_route.building_id,
            type="custom",
            geometry=RouteGeometry(points=[
                RoutePoint(x=15, y=5, type="start"),
                RoutePoint(x=15, y=25, type="end")
            ]),
            start_point=RoutePoint(x=15, y=5, type="start"),
            end_point=RoutePoint(x=15, y=25, type="end")
        )
        
        # Save both routes
        route_manager.save_routes([sample_route, conflicting_route])
        
        # Detect conflicts
        conflicts = route_manager.detect_route_conflicts(sample_route, [conflicting_route])
        assert len(conflicts) > 0
        
        # Save conflicts
        route_manager.save_conflicts(conflicts)
        
        # Load and verify conflicts
        loaded_conflicts = route_manager.load_conflicts()
        assert len(loaded_conflicts) > 0
        assert any(c.route_id == sample_route.id for c in loaded_conflicts)

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 