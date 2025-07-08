"""
Comprehensive Unit Tests for Arxos Platform

Tests cover:
- Version control handlers
- Route management
- Floor-specific features
- Error handling
- Edge cases
"""

import pytest
import json
import tempfile
import shutil
import asyncio
import concurrent.futures
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, List, Any

# Import all services and handlers
from services.version_control import VersionControlService, Version, Branch, MergeRequest
from services.route_manager import RouteManager, Route, RouteType, RouteStatus
from services.floor_manager import FloorManager, Floor, FloorStatus
from services.auto_snapshot import AutoSnapshotService, SnapshotConfig, ChangeMetrics
from services.realtime_service import RealTimeService as RealtimeService, WebSocketManager
from services.cache_service import CacheService, RedisCacheManager
from services.data_partitioning import DataPartitioningService
from services.access_control import AccessControlService, User, UserRole, Permission
from routers import version_control, auto_snapshot
from routers import realtime, partitioning, access_control


class TestVersionControlHandlers:
    """Unit tests for version control handlers"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def vc_service(self, temp_dir):
        """Create version control service instance"""
        db_path = Path(temp_dir) / "test_version_control.db"
        storage_path = Path(temp_dir) / "versions"
        return VersionControlService(str(db_path), str(storage_path))
    
    @pytest.fixture
    def sample_floor_data(self):
        """Sample floor data for testing"""
        return {
            "floor_id": "test-floor-1",
            "building_id": "test-building-1",
            "objects": [
                {"id": "obj1", "type": "wall", "x": 100, "y": 100},
                {"id": "obj2", "type": "door", "x": 200, "y": 200}
            ],
            "metadata": {"name": "Test Floor", "level": 1}
        }
    
    def test_create_version_handler(self, vc_service, sample_floor_data):
        """Test version creation handler"""
        result = vc_service.create_version(
            sample_floor_data,
            "test-floor-1",
            "test-building-1",
            "main",
            "Initial commit",
            "test-user"
        )
        
        assert result["success"] is True
        assert "version_id" in result
        assert "version_number" in result
        assert result["version_number"] == 1
    
    def test_create_branch_handler(self, vc_service, sample_floor_data):
        """Test branch creation handler"""
        # Create base version
        version_result = vc_service.create_version(
            sample_floor_data,
            "test-floor-1",
            "test-building-1",
            "main",
            "Initial commit",
            "test-user"
        )
        
        # Create branch
        result = vc_service.create_branch(
            "feature-branch",
            "test-floor-1",
            "test-building-1",
            version_result["version_id"],
            "test-user",
            "Test feature branch"
        )
        
        assert result["success"] is True
        assert result["branch_name"] == "feature-branch"
    
    def test_get_version_history_handler(self, vc_service, sample_floor_data):
        """Test version history retrieval handler"""
        # Create multiple versions
        vc_service.create_version(
            sample_floor_data,
            "test-floor-1",
            "test-building-1",
            "main",
            "Version 1",
            "test-user"
        )
        
        vc_service.create_version(
            sample_floor_data,
            "test-floor-1",
            "test-building-1",
            "main",
            "Version 2",
            "test-user"
        )
        
        result = vc_service.get_version_history("test-floor-1", "test-building-1")
        
        assert result["success"] is True
        assert len(result["versions"]) == 2
        assert result["versions"][0]["message"] == "Version 2"
        assert result["versions"][1]["message"] == "Version 1"
    
    def test_merge_request_handler(self, vc_service, sample_floor_data):
        """Test merge request creation and handling"""
        # Create source and target versions
        source_version = vc_service.create_version(
            sample_floor_data,
            "test-floor-1",
            "test-building-1",
            "feature-branch",
            "Feature changes",
            "test-user"
        )
        
        target_version = vc_service.create_version(
            sample_floor_data,
            "test-floor-1",
            "test-building-1",
            "main",
            "Main changes",
            "test-user"
        )
        
        # Create merge request
        result = vc_service.create_merge_request(
            source_version["version_id"],
            target_version["version_id"],
            "test-user",
            "Merge feature into main"
        )
        
        assert result["success"] is True
        assert "merge_request_id" in result
    
    def test_conflict_detection_handler(self, vc_service):
        """Test conflict detection handler"""
        # Create conflicting data
        data1 = {"objects": [{"id": "obj1", "x": 100, "y": 100}]}
        data2 = {"objects": [{"id": "obj1", "x": 200, "y": 200}]}
        
        # Create versions with conflicts
        v1 = vc_service.create_version(data1, "test-floor-1", "test-building-1", "branch1", "V1", "user1")
        v2 = vc_service.create_version(data2, "test-floor-1", "test-building-1", "branch2", "V2", "user2")
        
        # Detect conflicts
        conflicts = vc_service.detect_conflicts(v1["version_id"], v2["version_id"])
        
        assert len(conflicts) > 0
        assert any(c["type"] == "object_modification" for c in conflicts)
    
    def test_annotation_handler(self, vc_service, sample_floor_data):
        """Test annotation creation and retrieval"""
        # Create version
        version = vc_service.create_version(
            sample_floor_data,
            "test-floor-1",
            "test-building-1",
            "main",
            "Test version",
            "test-user"
        )
        
        # Add annotation
        annotation_result = vc_service.add_annotation(
            version["version_id"],
            "test-user",
            "Test annotation",
            {"x": 100, "y": 100},
            "note"
        )
        
        assert annotation_result["success"] is True
        
        # Get annotations
        annotations = vc_service.get_annotations(version["version_id"])
        assert len(annotations) == 1
        assert annotations[0]["content"] == "Test annotation"
    
    def test_comment_handler(self, vc_service, sample_floor_data):
        """Test comment creation and retrieval"""
        # Create version
        version = vc_service.create_version(
            sample_floor_data,
            "test-floor-1",
            "test-building-1",
            "main",
            "Test version",
            "test-user"
        )
        
        # Add comment
        comment_result = vc_service.add_comment(
            version["version_id"],
            "test-user",
            "Test comment"
        )
        
        assert comment_result["success"] is True
        
        # Get comments
        comments = vc_service.get_comments(version["version_id"])
        assert len(comments) == 1
        assert comments[0]["content"] == "Test comment"


class TestRouteManagement:
    """Unit tests for route management"""
    
    @pytest.fixture
    def route_manager(self):
        """Create route manager instance"""
        return RouteManager()
    
    @pytest.fixture
    def sample_route_data(self):
        """Sample route data for testing"""
        return {
            "route_id": "route-001",
            "floor_id": "floor-001",
            "building_id": "building-001",
            "name": "Test Route",
            "route_type": RouteType.EVACUATION,
            "waypoints": [
                {"x": 100, "y": 100},
                {"x": 200, "y": 200},
                {"x": 300, "y": 300}
            ],
            "properties": {
                "distance": 150.0,
                "estimated_time": 120,
                "accessibility": True
            }
        }
    
    def test_create_route(self, route_manager, sample_route_data):
        """Test route creation"""
        result = route_manager.create_route(
            sample_route_data["floor_id"],
            sample_route_data["building_id"],
            sample_route_data["name"],
            sample_route_data["route_type"],
            sample_route_data["waypoints"],
            sample_route_data["properties"],
            "test-user"
        )
        
        assert result["success"] is True
        assert "route_id" in result
        assert result["route"]["name"] == "Test Route"
    
    def test_get_route(self, route_manager, sample_route_data):
        """Test route retrieval"""
        # Create route
        create_result = route_manager.create_route(
            sample_route_data["floor_id"],
            sample_route_data["building_id"],
            sample_route_data["name"],
            sample_route_data["route_type"],
            sample_route_data["waypoints"],
            sample_route_data["properties"],
            "test-user"
        )
        
        # Get route
        route = route_manager.get_route(create_result["route_id"])
        
        assert route is not None
        assert route["name"] == "Test Route"
        assert route["route_type"] == RouteType.EVACUATION
    
    def test_update_route(self, route_manager, sample_route_data):
        """Test route update"""
        # Create route
        create_result = route_manager.create_route(
            sample_route_data["floor_id"],
            sample_route_data["building_id"],
            sample_route_data["name"],
            sample_route_data["route_type"],
            sample_route_data["waypoints"],
            sample_route_data["properties"],
            "test-user"
        )
        
        # Update route
        updated_waypoints = [
            {"x": 150, "y": 150},
            {"x": 250, "y": 250}
        ]
        
        result = route_manager.update_route(
            create_result["route_id"],
            {"name": "Updated Route", "waypoints": updated_waypoints},
            "test-user"
        )
        
        assert result["success"] is True
        assert result["route"]["name"] == "Updated Route"
        assert len(result["route"]["waypoints"]) == 2
    
    def test_delete_route(self, route_manager, sample_route_data):
        """Test route deletion"""
        # Create route
        create_result = route_manager.create_route(
            sample_route_data["floor_id"],
            sample_route_data["building_id"],
            sample_route_data["name"],
            sample_route_data["route_type"],
            sample_route_data["waypoints"],
            sample_route_data["properties"],
            "test-user"
        )
        
        # Delete route
        result = route_manager.delete_route(create_result["route_id"], "test-user")
        
        assert result["success"] is True
        
        # Verify route is deleted
        route = route_manager.get_route(create_result["route_id"])
        assert route is None
    
    def test_get_routes_by_floor(self, route_manager, sample_route_data):
        """Test getting routes by floor"""
        # Create multiple routes
        route_manager.create_route(
            sample_route_data["floor_id"],
            sample_route_data["building_id"],
            "Route 1",
            RouteType.EVACUATION,
            sample_route_data["waypoints"],
            sample_route_data["properties"],
            "test-user"
        )
        
        route_manager.create_route(
            sample_route_data["floor_id"],
            sample_route_data["building_id"],
            "Route 2",
            RouteType.ACCESS,
            sample_route_data["waypoints"],
            sample_route_data["properties"],
            "test-user"
        )
        
        # Get routes by floor
        routes = route_manager.get_routes_by_floor(sample_route_data["floor_id"])
        
        assert len(routes) == 2
        route_names = [r["name"] for r in routes]
        assert "Route 1" in route_names
        assert "Route 2" in route_names
    
    def test_route_validation(self, route_manager):
        """Test route validation"""
        # Test invalid waypoints
        invalid_waypoints = [{"x": 100, "y": 100}]  # Only one waypoint
        
        result = route_manager.create_route(
            "floor-001",
            "building-001",
            "Invalid Route",
            RouteType.EVACUATION,
            invalid_waypoints,
            {},
            "test-user"
        )
        
        assert result["success"] is False
        assert "waypoints" in result["message"]
    
    def test_route_optimization(self, route_manager, sample_route_data):
        """Test route optimization"""
        # Create route with inefficient waypoints
        inefficient_waypoints = [
            {"x": 100, "y": 100},
            {"x": 500, "y": 500},
            {"x": 200, "y": 200},
            {"x": 300, "y": 300}
        ]
        
        create_result = route_manager.create_route(
            sample_route_data["floor_id"],
            sample_route_data["building_id"],
            "Inefficient Route",
            RouteType.EVACUATION,
            inefficient_waypoints,
            sample_route_data["properties"],
            "test-user"
        )
        
        # Optimize route
        result = route_manager.optimize_route(create_result["route_id"])
        
        assert result["success"] is True
        assert len(result["route"]["waypoints"]) <= len(inefficient_waypoints)


class TestFloorSpecificFeatures:
    """Unit tests for floor-specific features"""
    
    @pytest.fixture
    def floor_manager(self):
        """Create floor manager instance"""
        return FloorManager()
    
    @pytest.fixture
    def sample_floor_data(self):
        """Sample floor data for testing"""
        return {
            "floor_id": "floor-001",
            "building_id": "building-001",
            "name": "Test Floor",
            "level": 1,
            "area": 1000.0,
            "objects": [
                {"id": "room-001", "type": "room", "x": 100, "y": 100, "width": 50, "height": 50},
                {"id": "room-002", "type": "room", "x": 200, "y": 200, "width": 60, "height": 40},
                {"id": "device-001", "type": "device", "x": 150, "y": 150}
            ],
            "metadata": {
                "floor_type": "office",
                "max_occupancy": 50,
                "accessibility": True
            }
        }
    
    def test_floor_creation(self, floor_manager, sample_floor_data):
        """Test floor creation"""
        result = floor_manager.create_floor(
            sample_floor_data["building_id"],
            sample_floor_data["name"],
            sample_floor_data["level"],
            sample_floor_data["area"],
            sample_floor_data["metadata"],
            "test-user"
        )
        
        assert result["success"] is True
        assert "floor_id" in result
        assert result["floor"]["name"] == "Test Floor"
        assert result["floor"]["level"] == 1
    
    def test_floor_update(self, floor_manager, sample_floor_data):
        """Test floor update"""
        # Create floor
        create_result = floor_manager.create_floor(
            sample_floor_data["building_id"],
            sample_floor_data["name"],
            sample_floor_data["level"],
            sample_floor_data["area"],
            sample_floor_data["metadata"],
            "test-user"
        )
        
        # Update floor
        result = floor_manager.update_floor(
            create_result["floor_id"],
            {"name": "Updated Floor", "area": 1200.0},
            "test-user"
        )
        
        assert result["success"] is True
        assert result["floor"]["name"] == "Updated Floor"
        assert result["floor"]["area"] == 1200.0
    
    def test_floor_deletion(self, floor_manager, sample_floor_data):
        """Test floor deletion"""
        # Create floor
        create_result = floor_manager.create_floor(
            sample_floor_data["building_id"],
            sample_floor_data["name"],
            sample_floor_data["level"],
            sample_floor_data["area"],
            sample_floor_data["metadata"],
            "test-user"
        )
        
        # Delete floor
        result = floor_manager.delete_floor(create_result["floor_id"], "test-user")
        
        assert result["success"] is True
        
        # Verify floor is deleted
        floor = floor_manager.get_floor(create_result["floor_id"])
        assert floor is None
    
    def test_floor_comparison(self, floor_manager, sample_floor_data):
        """Test floor comparison functionality"""
        # Create two similar floors
        floor1_result = floor_manager.create_floor(
            sample_floor_data["building_id"],
            "Floor 1",
            sample_floor_data["level"],
            sample_floor_data["area"],
            sample_floor_data["metadata"],
            "test-user"
        )
        
        floor2_result = floor_manager.create_floor(
            sample_floor_data["building_id"],
            "Floor 2",
            sample_floor_data["level"],
            sample_floor_data["area"],
            sample_floor_data["metadata"],
            "test-user"
        )
        
        # Compare floors
        comparison = floor_manager.compare_floors(
            floor1_result["floor_id"],
            floor2_result["floor_id"]
        )
        
        assert comparison["success"] is True
        assert "similarity_score" in comparison
        assert "differences" in comparison
    
    def test_floor_analytics(self, floor_manager, sample_floor_data):
        """Test floor analytics"""
        # Create floor with objects
        floor_result = floor_manager.create_floor(
            sample_floor_data["building_id"],
            sample_floor_data["name"],
            sample_floor_data["level"],
            sample_floor_data["area"],
            sample_floor_data["metadata"],
            "test-user"
        )
        
        # Add objects to floor
        floor_manager.add_objects_to_floor(
            floor_result["floor_id"],
            sample_floor_data["objects"],
            "test-user"
        )
        
        # Get analytics
        analytics = floor_manager.get_floor_analytics(floor_result["floor_id"])
        
        assert analytics["success"] is True
        assert "object_count" in analytics
        assert "area_utilization" in analytics
        assert "object_distribution" in analytics
    
    def test_floor_grid_calibration(self, floor_manager, sample_floor_data):
        """Test floor grid calibration"""
        # Create floor
        floor_result = floor_manager.create_floor(
            sample_floor_data["building_id"],
            sample_floor_data["name"],
            sample_floor_data["level"],
            sample_floor_data["area"],
            sample_floor_data["metadata"],
            "test-user"
        )
        
        # Calibrate grid
        grid_data = {
            "origin_x": 0,
            "origin_y": 0,
            "pixels_per_unit": 10,
            "unit": "feet"
        }
        
        result = floor_manager.calibrate_grid(
            floor_result["floor_id"],
            grid_data,
            "test-user"
        )
        
        assert result["success"] is True
        assert result["grid"]["pixels_per_unit"] == 10
        assert result["grid"]["unit"] == "feet"
    
    def test_floor_export(self, floor_manager, sample_floor_data):
        """Test floor export functionality"""
        # Create floor
        floor_result = floor_manager.create_floor(
            sample_floor_data["building_id"],
            sample_floor_data["name"],
            sample_floor_data["level"],
            sample_floor_data["area"],
            sample_floor_data["metadata"],
            "test-user"
        )
        
        # Add objects
        floor_manager.add_objects_to_floor(
            floor_result["floor_id"],
            sample_floor_data["objects"],
            "test-user"
        )
        
        # Export floor
        export_result = floor_manager.export_floor(
            floor_result["floor_id"],
            "json",
            "test-user"
        )
        
        assert export_result["success"] is True
        assert "export_data" in export_result
        assert "file_size" in export_result


class TestErrorHandling:
    """Unit tests for error handling"""
    
    @pytest.fixture
    def vc_service(self):
        """Create version control service for error testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_error_handling.db"
        storage_path = Path(temp_dir) / "versions"
        service = VersionControlService(str(db_path), str(storage_path))
        yield service
        shutil.rmtree(temp_dir)
    
    def test_invalid_floor_id(self, vc_service):
        """Test handling of invalid floor ID"""
        result = vc_service.get_version_history("", "building-001")
        assert result["success"] is False
        assert "floor_id" in result["message"].lower()
    
    def test_invalid_building_id(self, vc_service):
        """Test handling of invalid building ID"""
        result = vc_service.get_version_history("floor-001", "")
        assert result["success"] is False
        assert "building_id" in result["message"].lower()
    
    def test_nonexistent_version(self, vc_service):
        """Test handling of nonexistent version"""
        result = vc_service.get_version_data("nonexistent-version-id")
        assert result["success"] is False
        assert "not found" in result["message"].lower()
    
    def test_invalid_branch_name(self, vc_service):
        """Test handling of invalid branch name"""
        sample_data = {"test": "data"}
        version_result = vc_service.create_version(
            sample_data, "floor-001", "building-001",
            "main", "Initial commit", "test-user"
        )
        
        result = vc_service.create_branch(
            "",  # Invalid empty branch name
            "floor-001",
            "building-001",
            version_result["version_id"],
            "test-user"
        )
        
        assert result["success"] is False
        assert "branch name" in result["message"].lower()
    
    def test_duplicate_branch_creation(self, vc_service):
        """Test handling of duplicate branch creation"""
        sample_data = {"test": "data"}
        version_result = vc_service.create_version(
            sample_data, "floor-001", "building-001",
            "main", "Initial commit", "test-user"
        )
        
        # Create first branch
        vc_service.create_branch(
            "feature-branch",
            "floor-001",
            "building-001",
            version_result["version_id"],
            "test-user"
        )
        
        # Try to create duplicate branch
        result = vc_service.create_branch(
            "feature-branch",
            "floor-001",
            "building-001",
            version_result["version_id"],
            "test-user"
        )
        
        assert result["success"] is False
        assert "already exists" in result["message"].lower()
    
    def test_invalid_merge_request(self, vc_service):
        """Test handling of invalid merge request"""
        result = vc_service.create_merge_request(
            "invalid-source-id",
            "invalid-target-id",
            "test-user",
            "Invalid merge request"
        )
        
        assert result["success"] is False
        assert "not found" in result["message"].lower()
    
    def test_database_connection_error(self, vc_service):
        """Test handling of database connection errors"""
        # Simulate database connection error
        with patch('sqlite3.connect', side_effect=Exception("Database connection failed")):
            result = vc_service.create_version(
                {"test": "data"},
                "floor-001",
                "building-001",
                "main",
                "Test commit",
                "test-user"
            )
            
            assert result["success"] is False
            assert "database" in result["message"].lower()
    
    def test_file_system_error(self, vc_service):
        """Test handling of file system errors"""
        # Simulate file system error
        with patch('pathlib.Path.exists', return_value=False):
            result = vc_service.get_version_data("some-version-id")
            assert result["success"] is False
    
    def test_invalid_data_format(self, vc_service):
        """Test handling of invalid data format"""
        # Test with invalid JSON data
        invalid_data = "invalid json string"
        
        result = vc_service.create_version(
            invalid_data,
            "floor-001",
            "building-001",
            "main",
            "Test commit",
            "test-user"
        )
        
        assert result["success"] is False
        assert "data format" in result["message"].lower()
    
    def test_missing_required_fields(self, vc_service):
        """Test handling of missing required fields"""
        # Test with incomplete data
        incomplete_data = {"objects": []}  # Missing floor_id, building_id
        
        result = vc_service.create_version(
            incomplete_data,
            "",  # Missing floor_id
            "",  # Missing building_id
            "main",
            "Test commit",
            "test-user"
        )
        
        assert result["success"] is False
        assert "required" in result["message"].lower()
    
    def test_permission_denied(self, vc_service):
        """Test handling of permission denied errors"""
        # Simulate permission error
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
            result = vc_service.create_version(
                {"test": "data"},
                "floor-001",
                "building-001",
                "main",
                "Test commit",
                "test-user"
            )
            
            assert result["success"] is False
            assert "permission" in result["message"].lower()
    
    def test_storage_full_error(self, vc_service):
        """Test handling of storage full errors"""
        # Simulate storage full error
        with patch('pathlib.Path.write_text', side_effect=OSError("No space left on device")):
            result = vc_service.create_version(
                {"test": "data"},
                "floor-001",
                "building-001",
                "main",
                "Test commit",
                "test-user"
            )
            
            assert result["success"] is False
            assert "storage" in result["message"].lower()


class TestEdgeCases:
    """Unit tests for edge cases"""
    
    @pytest.fixture
    def vc_service(self):
        """Create version control service for edge case testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_edge_cases.db"
        storage_path = Path(temp_dir) / "versions"
        service = VersionControlService(str(db_path), str(storage_path))
        yield service
        shutil.rmtree(temp_dir)
    
    def test_empty_floor_data(self, vc_service):
        """Test handling of empty floor data"""
        empty_data = {
            "floor_id": "empty-floor",
            "building_id": "building-001",
            "objects": [],
            "metadata": {}
        }
        
        result = vc_service.create_version(
            empty_data,
            "empty-floor",
            "building-001",
            "main",
            "Empty floor",
            "test-user"
        )
        
        assert result["success"] is True
        assert result["version"]["object_count"] == 0
    
    def test_large_dataset(self, vc_service):
        """Test handling of large datasets"""
        # Create large dataset
        large_data = {
            "floor_id": "large-floor",
            "building_id": "building-001",
            "objects": [
                {"id": f"obj-{i}", "type": "device", "x": i, "y": i}
                for i in range(10000)  # 10,000 objects
            ],
            "metadata": {"name": "Large Floor"}
        }
        
        result = vc_service.create_version(
            large_data,
            "large-floor",
            "building-001",
            "main",
            "Large dataset",
            "test-user"
        )
        
        assert result["success"] is True
        assert result["version"]["object_count"] == 10000
    
    def test_concurrent_version_creation(self, vc_service):
        """Test concurrent version creation"""
        sample_data = {"test": "data"}
        
        def create_version():
            return vc_service.create_version(
                sample_data,
                "concurrent-floor",
                "building-001",
                "main",
                "Concurrent version",
                "test-user"
            )
        
        # Create versions concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_version) for _ in range(5)]
            results = [future.result() for future in futures]
        
        # All should succeed
        for result in results:
            assert result["success"] is True
        
        # Check version numbers are unique
        version_numbers = [r["version"]["version_number"] for r in results]
        assert len(set(version_numbers)) == 5
    
    def test_failed_restore_operation(self, vc_service):
        """Test handling of failed restore operations"""
        # Create version
        sample_data = {"test": "data"}
        version_result = vc_service.create_version(
            sample_data,
            "restore-floor",
            "building-001",
            "main",
            "Test version",
            "test-user"
        )
        
        # Simulate corrupted version file
        version_file = Path(vc_service.storage_path) / f"{version_result['version_id']}.json"
        version_file.write_text("corrupted json data")
        
        # Try to restore
        result = vc_service.restore_version(version_result["version_id"], "test-user")
        
        assert result["success"] is False
        assert "corrupted" in result["message"].lower()
    
    def test_malicious_data_injection(self, vc_service):
        """Test handling of malicious data injection"""
        malicious_data = {
            "floor_id": "malicious-floor",
            "building_id": "building-001",
            "objects": [
                {
                    "id": "malicious-obj",
                    "type": "device",
                    "x": 100,
                    "y": 100,
                    "script": "<script>alert('xss')</script>",
                    "sql": "'; DROP TABLE versions; --"
                }
            ],
            "metadata": {"name": "Malicious Floor"}
        }
        
        result = vc_service.create_version(
            malicious_data,
            "malicious-floor",
            "building-001",
            "main",
            "Malicious data",
            "test-user"
        )
        
        # Should handle malicious data gracefully
        assert result["success"] is True
        
        # Verify data is sanitized
        version_data = vc_service.get_version_data(result["version_id"])
        assert version_data["success"] is True
        assert "script" not in str(version_data["data"])
    
    def test_extremely_long_strings(self, vc_service):
        """Test handling of extremely long strings"""
        long_string = "a" * 1000000  # 1MB string
        
        long_data = {
            "floor_id": "long-string-floor",
            "building_id": "building-001",
            "objects": [
                {
                    "id": "long-obj",
                    "type": "device",
                    "x": 100,
                    "y": 100,
                    "description": long_string
                }
            ],
            "metadata": {"name": "Long String Floor"}
        }
        
        result = vc_service.create_version(
            long_data,
            "long-string-floor",
            "building-001",
            "main",
            "Long string test",
            "test-user"
        )
        
        # Should handle large strings
        assert result["success"] is True
    
    def test_special_characters(self, vc_service):
        """Test handling of special characters"""
        special_data = {
            "floor_id": "special-floor",
            "building_id": "building-001",
            "objects": [
                {
                    "id": "special-obj",
                    "type": "device",
                    "x": 100,
                    "y": 100,
                    "name": "Test Device with émojis 🚀 and symbols @#$%^&*()"
                }
            ],
            "metadata": {"name": "Special Characters Floor"}
        }
        
        result = vc_service.create_version(
            special_data,
            "special-floor",
            "building-001",
            "main",
            "Special characters test",
            "test-user"
        )
        
        assert result["success"] is True
        
        # Verify special characters are preserved
        version_data = vc_service.get_version_data(result["version_id"])
        assert "émojis" in str(version_data["data"])
        assert "🚀" in str(version_data["data"])
    
    def test_nested_objects(self, vc_service):
        """Test handling of deeply nested objects"""
        nested_data = {
            "floor_id": "nested-floor",
            "building_id": "building-001",
            "objects": [
                {
                    "id": "nested-obj",
                    "type": "device",
                    "x": 100,
                    "y": 100,
                    "properties": {
                        "level1": {
                            "level2": {
                                "level3": {
                                    "level4": {
                                        "level5": "deep value"
                                    }
                                }
                            }
                        }
                    }
                }
            ],
            "metadata": {"name": "Nested Objects Floor"}
        }
        
        result = vc_service.create_version(
            nested_data,
            "nested-floor",
            "building-001",
            "main",
            "Nested objects test",
            "test-user"
        )
        
        assert result["success"] is True
        
        # Verify nested structure is preserved
        version_data = vc_service.get_version_data(result["version_id"])
        assert version_data["data"]["objects"][0]["properties"]["level1"]["level2"]["level3"]["level4"]["level5"] == "deep value"


if __name__ == "__main__":
    pytest.main([__file__]) 