"""
Comprehensive Integration Tests for Arxos Platform

Tests cover:
- End-to-end version control workflows
- Route management integration tests
- Floor comparison functionality tests
- Multi-user collaboration tests
- System integration scenarios
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

# Import all services
from arx_svg_parser.services.version_control import VersionControlService
from arx_svg_parser.services.route_manager import RouteManager
from arx_svg_parser.services.floor_manager import FloorManager
from arx_svg_parser.services.auto_snapshot import AutoSnapshotService, SnapshotConfig
from arx_svg_parser.services.realtime_service import RealTimeService as RealtimeService
from arx_svg_parser.services.cache_service import CacheService
from arx_svg_parser.services.data_partitioning import DataPartitioningService
from arx_svg_parser.services.access_control import AccessControlService
from arx_svg_parser.routers import version_control, auto_snapshot
from arx_svg_parser.routers import realtime, partitioning, access_control


class TestEndToEndVersionControlWorkflows:
    """Integration tests for end-to-end version control workflows"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def vc_service(self, temp_dir):
        """Create version control service instance"""
        db_path = Path(temp_dir) / "test_integration_vc.db"
        storage_path = Path(temp_dir) / "versions"
        return VersionControlService(str(db_path), str(storage_path))
    
    @pytest.fixture
    def sample_project_data(self):
        """Sample project data for testing"""
        return {
            "building_id": "test-building-001",
            "floors": [
                {
                    "floor_id": "floor-001",
                    "name": "Ground Floor",
                    "level": 0,
                    "objects": [
                        {"id": "room-001", "type": "room", "x": 100, "y": 100, "width": 50, "height": 50},
                        {"id": "room-002", "type": "room", "x": 200, "y": 200, "width": 60, "height": 40},
                        {"id": "device-001", "type": "device", "x": 150, "y": 150}
                    ]
                },
                {
                    "floor_id": "floor-002",
                    "name": "First Floor",
                    "level": 1,
                    "objects": [
                        {"id": "room-003", "type": "room", "x": 100, "y": 100, "width": 40, "height": 40},
                        {"id": "device-002", "type": "device", "x": 120, "y": 120}
                    ]
                }
            ]
        }
    
    def test_complete_version_control_workflow(self, vc_service, sample_project_data):
        """Test complete version control workflow from creation to merge"""
        
        # Step 1: Create initial versions for all floors
        initial_versions = {}
        for floor in sample_project_data["floors"]:
            result = vc_service.create_version(
                floor,
                floor["floor_id"],
                sample_project_data["building_id"],
                "main",
                f"Initial version of {floor['name']}",
                "architect"
            )
            initial_versions[floor["floor_id"]] = result["version_id"]
        
        # Step 2: Create feature branches for each floor
        feature_branches = {}
        for floor in sample_project_data["floors"]:
            result = vc_service.create_branch(
                f"feature-{floor['floor_id']}",
                floor["floor_id"],
                sample_project_data["building_id"],
                initial_versions[floor["floor_id"]],
                "developer",
                f"Feature branch for {floor['name']}"
            )
            feature_branches[floor["floor_id"]] = result["branch_name"]
        
        # Step 3: Make changes in feature branches
        modified_floors = {}
        for floor in sample_project_data["floors"]:
            # Create modified version
            modified_floor = floor.copy()
            modified_floor["objects"].append({
                "id": f"new-device-{floor['floor_id']}",
                "type": "device",
                "x": 300,
                "y": 300
            })
            modified_floor["metadata"] = {"last_modified": datetime.utcnow().isoformat()}
            
            result = vc_service.create_version(
                modified_floor,
                floor["floor_id"],
                sample_project_data["building_id"],
                feature_branches[floor["floor_id"]],
                f"Added new device to {floor['name']}",
                "developer"
            )
            modified_floors[floor["floor_id"]] = result["version_id"]
        
        # Step 4: Create merge requests
        merge_requests = {}
        for floor in sample_project_data["floors"]:
            result = vc_service.create_merge_request(
                modified_floors[floor["floor_id"]],
                initial_versions[floor["floor_id"]],
                "developer",
                f"Merge feature changes for {floor['name']}"
            )
            merge_requests[floor["floor_id"]] = result["merge_request_id"]
        
        # Step 5: Review and approve merge requests
        for floor in sample_project_data["floors"]:
            # Add review comment
            vc_service.add_comment(
                merge_requests[floor["floor_id"]],
                "reviewer",
                f"Changes look good for {floor['name']}"
            )
            
            # Execute merge
            result = vc_service.execute_merge(merge_requests[floor["floor_id"]], "reviewer")
            assert result["success"] is True
        
        # Step 6: Verify final state
        for floor in sample_project_data["floors"]:
            # Get latest version
            history = vc_service.get_version_history(floor["floor_id"], sample_project_data["building_id"])
            latest_version = history["versions"][0]
            
            # Verify changes were merged
            version_data = vc_service.get_version_data(latest_version["version_id"])
            assert version_data["success"] is True
            
            # Check that new device was added
            objects = version_data["data"]["objects"]
            new_device_ids = [obj["id"] for obj in objects if obj["id"].startswith("new-device-")]
            assert len(new_device_ids) == 1
    
    def test_complex_branching_scenario(self, vc_service, sample_project_data):
        """Test complex branching scenario with multiple developers"""
        
        # Initial setup
        floor = sample_project_data["floors"][0]
        initial_result = vc_service.create_version(
            floor,
            floor["floor_id"],
            sample_project_data["building_id"],
            "main",
            "Initial version",
            "architect"
        )
        
        # Developer 1 creates feature branch
        dev1_branch = vc_service.create_branch(
            "dev1-feature",
            floor["floor_id"],
            sample_project_data["building_id"],
            initial_result["version_id"],
            "developer1",
            "Developer 1 feature branch"
        )
        
        # Developer 2 creates different feature branch
        dev2_branch = vc_service.create_branch(
            "dev2-feature",
            floor["floor_id"],
            sample_project_data["building_id"],
            initial_result["version_id"],
            "developer2",
            "Developer 2 feature branch"
        )
        
        # Developer 1 makes changes
        dev1_floor = floor.copy()
        dev1_floor["objects"].append({"id": "dev1-device", "type": "device", "x": 400, "y": 400})
        dev1_version = vc_service.create_version(
            dev1_floor,
            floor["floor_id"],
            sample_project_data["building_id"],
            "dev1-feature",
            "Developer 1 changes",
            "developer1"
        )
        
        # Developer 2 makes different changes
        dev2_floor = floor.copy()
        dev2_floor["objects"].append({"id": "dev2-device", "type": "device", "x": 500, "y": 500})
        dev2_version = vc_service.create_version(
            dev2_floor,
            floor["floor_id"],
            sample_project_data["building_id"],
            "dev2-feature",
            "Developer 2 changes",
            "developer2"
        )
        
        # Merge dev1 changes first
        dev1_merge = vc_service.create_merge_request(
            dev1_version["version_id"],
            initial_result["version_id"],
            "developer1",
            "Merge dev1 changes"
        )
        vc_service.execute_merge(dev1_merge["merge_request_id"], "reviewer")
        
        # Merge dev2 changes (should create new base)
        dev2_merge = vc_service.create_merge_request(
            dev2_version["version_id"],
            dev1_version["version_id"],  # Now based on dev1's merged version
            "developer2",
            "Merge dev2 changes"
        )
        vc_service.execute_merge(dev2_merge["merge_request_id"], "reviewer")
        
        # Verify final state has both changes
        history = vc_service.get_version_history(floor["floor_id"], sample_project_data["building_id"])
        latest_version = history["versions"][0]
        version_data = vc_service.get_version_data(latest_version["version_id"])
        
        objects = version_data["data"]["objects"]
        device_ids = [obj["id"] for obj in objects if obj["id"].startswith("dev")]
        assert "dev1-device" in device_ids
        assert "dev2-device" in device_ids
    
    def test_conflict_resolution_workflow(self, vc_service, sample_project_data):
        """Test conflict resolution workflow"""
        
        # Initial setup
        floor = sample_project_data["floors"][0]
        initial_result = vc_service.create_version(
            floor,
            floor["floor_id"],
            sample_project_data["building_id"],
            "main",
            "Initial version",
            "architect"
        )
        
        # Create two branches with conflicting changes
        branch1 = vc_service.create_branch(
            "conflict-branch-1",
            floor["floor_id"],
            sample_project_data["building_id"],
            initial_result["version_id"],
            "developer1"
        )
        
        branch2 = vc_service.create_branch(
            "conflict-branch-2",
            floor["floor_id"],
            sample_project_data["building_id"],
            initial_result["version_id"],
            "developer2"
        )
        
        # Make conflicting changes to same object
        floor1 = floor.copy()
        floor1["objects"][0]["x"] = 150  # Modify same object
        
        floor2 = floor.copy()
        floor2["objects"][0]["x"] = 250  # Different modification to same object
        
        version1 = vc_service.create_version(
            floor1,
            floor["floor_id"],
            sample_project_data["building_id"],
            "conflict-branch-1",
            "Conflicting change 1",
            "developer1"
        )
        
        version2 = vc_service.create_version(
            floor2,
            floor["floor_id"],
            sample_project_data["building_id"],
            "conflict-branch-2",
            "Conflicting change 2",
            "developer2"
        )
        
        # Try to merge - should detect conflicts
        merge_request = vc_service.create_merge_request(
            version1["version_id"],
            initial_result["version_id"],
            "developer1",
            "Merge with conflicts"
        )
        
        # Detect conflicts
        conflicts = vc_service.detect_conflicts(version1["version_id"], version2["version_id"])
        assert len(conflicts) > 0
        
        # Resolve conflicts
        resolved_floor = floor.copy()
        resolved_floor["objects"][0]["x"] = 200  # Compromise value
        
        resolved_version = vc_service.create_version(
            resolved_floor,
            floor["floor_id"],
            sample_project_data["building_id"],
            "conflict-branch-1",
            "Resolved conflicts",
            "developer1"
        )
        
        # Update merge request with resolved version
        vc_service.update_merge_request(
            merge_request["merge_request_id"],
            resolved_version["version_id"],
            "developer1"
        )
        
        # Execute merge
        result = vc_service.execute_merge(merge_request["merge_request_id"], "reviewer")
        assert result["success"] is True


class TestRouteManagementIntegration:
    """Integration tests for route management"""
    
    @pytest.fixture
    def route_manager(self):
        """Create route manager instance"""
        return RouteManager()
    
    @pytest.fixture
    def floor_manager(self):
        """Create floor manager instance"""
        return FloorManager()
    
    @pytest.fixture
    def sample_floor_with_routes(self):
        """Sample floor data with routes for testing"""
        return {
            "floor_id": "route-test-floor",
            "building_id": "route-test-building",
            "name": "Route Test Floor",
            "level": 1,
            "area": 2000.0,
            "objects": [
                {"id": "room-001", "type": "room", "x": 100, "y": 100, "width": 50, "height": 50},
                {"id": "room-002", "type": "room", "x": 300, "y": 300, "width": 60, "height": 40},
                {"id": "exit-001", "type": "exit", "x": 500, "y": 500},
                {"id": "stair-001", "type": "stair", "x": 200, "y": 200}
            ],
            "metadata": {"name": "Route Test Floor"}
        }
    
    def test_route_creation_with_floor_integration(self, route_manager, floor_manager, sample_floor_with_routes):
        """Test route creation integrated with floor management"""
        
        # Create floor
        floor_result = floor_manager.create_floor(
            sample_floor_with_routes["building_id"],
            sample_floor_with_routes["name"],
            sample_floor_with_routes["level"],
            sample_floor_with_routes["area"],
            sample_floor_with_routes["metadata"],
            "architect"
        )
        
        # Add objects to floor
        floor_manager.add_objects_to_floor(
            floor_result["floor_id"],
            sample_floor_with_routes["objects"],
            "architect"
        )
        
        # Create evacuation route
        evacuation_waypoints = [
            {"x": 100, "y": 100},  # Start in room-001
            {"x": 200, "y": 200},  # Through stair-001
            {"x": 500, "y": 500}   # End at exit-001
        ]
        
        evacuation_route = route_manager.create_route(
            floor_result["floor_id"],
            sample_floor_with_routes["building_id"],
            "Evacuation Route 1",
            "evacuation",
            evacuation_waypoints,
            {"distance": 300.0, "estimated_time": 180, "accessibility": True},
            "safety_officer"
        )
        
        assert evacuation_route["success"] is True
        
        # Create access route
        access_waypoints = [
            {"x": 300, "y": 300},  # Start in room-002
            {"x": 200, "y": 200},  # Through stair-001
            {"x": 100, "y": 100}   # End in room-001
        ]
        
        access_route = route_manager.create_route(
            floor_result["floor_id"],
            sample_floor_with_routes["building_id"],
            "Access Route 1",
            "access",
            access_waypoints,
            {"distance": 250.0, "estimated_time": 120, "accessibility": True},
            "facility_manager"
        )
        
        assert access_route["success"] is True
        
        # Get all routes for floor
        floor_routes = route_manager.get_routes_by_floor(floor_result["floor_id"])
        assert len(floor_routes) == 2
        
        # Verify route types
        route_types = [r["route_type"] for r in floor_routes]
        assert "evacuation" in route_types
        assert "access" in route_types
    
    def test_route_optimization_integration(self, route_manager, floor_manager, sample_floor_with_routes):
        """Test route optimization integrated with floor layout"""
        
        # Create floor with complex layout
        floor_result = floor_manager.create_floor(
            sample_floor_with_routes["building_id"],
            sample_floor_with_routes["name"],
            sample_floor_with_routes["level"],
            sample_floor_with_routes["area"],
            sample_floor_with_routes["metadata"],
            "architect"
        )
        
        # Add complex object layout
        complex_objects = sample_floor_with_routes["objects"] + [
            {"id": "obstacle-001", "type": "obstacle", "x": 250, "y": 250, "width": 20, "height": 20},
            {"id": "obstacle-002", "type": "obstacle", "x": 350, "y": 350, "width": 20, "height": 20}
        ]
        
        floor_manager.add_objects_to_floor(
            floor_result["floor_id"],
            complex_objects,
            "architect"
        )
        
        # Create inefficient route
        inefficient_waypoints = [
            {"x": 100, "y": 100},
            {"x": 400, "y": 400},  # Goes around obstacles inefficiently
            {"x": 500, "y": 500}
        ]
        
        inefficient_route = route_manager.create_route(
            floor_result["floor_id"],
            sample_floor_with_routes["building_id"],
            "Inefficient Route",
            "evacuation",
            inefficient_waypoints,
            {"distance": 600.0, "estimated_time": 300},
            "safety_officer"
        )
        
        # Optimize route
        optimized_result = route_manager.optimize_route(inefficient_route["route_id"])
        
        assert optimized_result["success"] is True
        assert optimized_result["route"]["properties"]["distance"] < 600.0
        assert optimized_result["route"]["properties"]["estimated_time"] < 300
    
    def test_route_validation_with_floor_constraints(self, route_manager, floor_manager, sample_floor_with_routes):
        """Test route validation against floor constraints"""
        
        # Create floor
        floor_result = floor_manager.create_floor(
            sample_floor_with_routes["building_id"],
            sample_floor_with_routes["name"],
            sample_floor_with_routes["level"],
            sample_floor_with_routes["area"],
            sample_floor_with_routes["metadata"],
            "architect"
        )
        
        # Add objects with constraints
        constrained_objects = sample_floor_with_routes["objects"] + [
            {"id": "restricted-001", "type": "restricted_area", "x": 250, "y": 250, "width": 100, "height": 100},
            {"id": "hazard-001", "type": "hazard", "x": 350, "y": 350, "width": 50, "height": 50}
        ]
        
        floor_manager.add_objects_to_floor(
            floor_result["floor_id"],
            constrained_objects,
            "architect"
        )
        
        # Try to create route through restricted area
        invalid_waypoints = [
            {"x": 100, "y": 100},
            {"x": 300, "y": 300},  # Goes through restricted area
            {"x": 500, "y": 500}
        ]
        
        invalid_route = route_manager.create_route(
            floor_result["floor_id"],
            sample_floor_with_routes["building_id"],
            "Invalid Route",
            "evacuation",
            invalid_waypoints,
            {"distance": 400.0, "estimated_time": 200},
            "safety_officer"
        )
        
        # Should fail validation
        assert invalid_route["success"] is False
        assert "restricted" in invalid_route["message"].lower() or "constraint" in invalid_route["message"].lower()


class TestFloorComparisonFunctionality:
    """Integration tests for floor comparison functionality"""
    
    @pytest.fixture
    def floor_manager(self):
        """Create floor manager instance"""
        return FloorManager()
    
    @pytest.fixture
    def sample_floors_for_comparison(self):
        """Sample floors for comparison testing"""
        return {
            "floor_1": {
                "floor_id": "compare-floor-1",
                "building_id": "compare-building",
                "name": "Original Floor",
                "level": 1,
                "area": 1000.0,
                "objects": [
                    {"id": "room-001", "type": "room", "x": 100, "y": 100, "width": 50, "height": 50},
                    {"id": "room-002", "type": "room", "x": 200, "y": 200, "width": 60, "height": 40},
                    {"id": "device-001", "type": "device", "x": 150, "y": 150}
                ],
                "metadata": {"name": "Original Floor"}
            },
            "floor_2": {
                "floor_id": "compare-floor-2",
                "building_id": "compare-building",
                "name": "Modified Floor",
                "level": 1,
                "area": 1200.0,
                "objects": [
                    {"id": "room-001", "type": "room", "x": 100, "y": 100, "width": 60, "height": 60},  # Modified
                    {"id": "room-002", "type": "room", "x": 200, "y": 200, "width": 60, "height": 40},
                    {"id": "device-001", "type": "device", "x": 150, "y": 150},
                    {"id": "device-002", "type": "device", "x": 300, "y": 300}  # Added
                ],
                "metadata": {"name": "Modified Floor"}
            }
        }
    
    def test_floor_comparison_basic(self, floor_manager, sample_floors_for_comparison):
        """Test basic floor comparison functionality"""
        
        # Create two floors
        floor1_result = floor_manager.create_floor(
            sample_floors_for_comparison["floor_1"]["building_id"],
            sample_floors_for_comparison["floor_1"]["name"],
            sample_floors_for_comparison["floor_1"]["level"],
            sample_floors_for_comparison["floor_1"]["area"],
            sample_floors_for_comparison["floor_1"]["metadata"],
            "architect"
        )
        
        floor2_result = floor_manager.create_floor(
            sample_floors_for_comparison["floor_2"]["building_id"],
            sample_floors_for_comparison["floor_2"]["name"],
            sample_floors_for_comparison["floor_2"]["level"],
            sample_floors_for_comparison["floor_2"]["area"],
            sample_floors_for_comparison["floor_2"]["metadata"],
            "architect"
        )
        
        # Add objects to floors
        floor_manager.add_objects_to_floor(
            floor1_result["floor_id"],
            sample_floors_for_comparison["floor_1"]["objects"],
            "architect"
        )
        
        floor_manager.add_objects_to_floor(
            floor2_result["floor_id"],
            sample_floors_for_comparison["floor_2"]["objects"],
            "architect"
        )
        
        # Compare floors
        comparison = floor_manager.compare_floors(
            floor1_result["floor_id"],
            floor2_result["floor_id"]
        )
        
        assert comparison["success"] is True
        assert "similarity_score" in comparison
        assert "differences" in comparison
        assert "added_objects" in comparison["differences"]
        assert "modified_objects" in comparison["differences"]
        assert "removed_objects" in comparison["differences"]
        
        # Verify specific differences
        differences = comparison["differences"]
        assert len(differences["added_objects"]) == 1  # device-002
        assert len(differences["modified_objects"]) == 1  # room-001
        assert len(differences["removed_objects"]) == 0
    
    def test_floor_comparison_with_metadata(self, floor_manager, sample_floors_for_comparison):
        """Test floor comparison including metadata changes"""
        
        # Create floors with different metadata
        floor1_result = floor_manager.create_floor(
            sample_floors_for_comparison["floor_1"]["building_id"],
            sample_floors_for_comparison["floor_1"]["name"],
            sample_floors_for_comparison["floor_1"]["level"],
            sample_floors_for_comparison["floor_1"]["area"],
            {"floor_type": "office", "max_occupancy": 50},
            "architect"
        )
        
        floor2_result = floor_manager.create_floor(
            sample_floors_for_comparison["floor_2"]["building_id"],
            sample_floors_for_comparison["floor_2"]["name"],
            sample_floors_for_comparison["floor_2"]["level"],
            sample_floors_for_comparison["floor_2"]["area"],
            {"floor_type": "retail", "max_occupancy": 100},
            "architect"
        )
        
        # Compare floors
        comparison = floor_manager.compare_floors(
            floor1_result["floor_id"],
            floor2_result["floor_id"]
        )
        
        assert comparison["success"] is True
        assert "metadata_differences" in comparison["differences"]
        
        metadata_diff = comparison["differences"]["metadata_differences"]
        assert "floor_type" in metadata_diff
        assert "max_occupancy" in metadata_diff
    
    def test_floor_comparison_performance(self, floor_manager):
        """Test floor comparison performance with large datasets"""
        
        # Create large floors
        large_floor_1 = {
            "floor_id": "large-floor-1",
            "building_id": "large-building",
            "name": "Large Floor 1",
            "level": 1,
            "area": 10000.0,
            "objects": [
                {"id": f"obj-{i}", "type": "device", "x": i * 10, "y": i * 10}
                for i in range(1000)  # 1000 objects
            ],
            "metadata": {"name": "Large Floor 1"}
        }
        
        large_floor_2 = {
            "floor_id": "large-floor-2",
            "building_id": "large-building",
            "name": "Large Floor 2",
            "level": 1,
            "area": 10000.0,
            "objects": [
                {"id": f"obj-{i}", "type": "device", "x": i * 10, "y": i * 10}
                for i in range(1000)  # 1000 objects with some differences
            ] + [{"id": "new-obj", "type": "device", "x": 5000, "y": 5000}],
            "metadata": {"name": "Large Floor 2"}
        }
        
        # Create floors
        floor1_result = floor_manager.create_floor(
            large_floor_1["building_id"],
            large_floor_1["name"],
            large_floor_1["level"],
            large_floor_1["area"],
            large_floor_1["metadata"],
            "architect"
        )
        
        floor2_result = floor_manager.create_floor(
            large_floor_2["building_id"],
            large_floor_2["name"],
            large_floor_2["level"],
            large_floor_2["area"],
            large_floor_2["metadata"],
            "architect"
        )
        
        # Add objects
        floor_manager.add_objects_to_floor(
            floor1_result["floor_id"],
            large_floor_1["objects"],
            "architect"
        )
        
        floor_manager.add_objects_to_floor(
            floor2_result["floor_id"],
            large_floor_2["objects"],
            "architect"
        )
        
        # Measure comparison performance
        import time
        start_time = time.time()
        
        comparison = floor_manager.compare_floors(
            floor1_result["floor_id"],
            floor2_result["floor_id"]
        )
        
        end_time = time.time()
        comparison_time = end_time - start_time
        
        assert comparison["success"] is True
        assert comparison_time < 5.0  # Should complete within 5 seconds
        
        # Verify differences
        differences = comparison["differences"]
        assert len(differences["added_objects"]) == 1  # new-obj


class TestMultiUserCollaboration:
    """Integration tests for multi-user collaboration"""
    
    @pytest.fixture
    def vc_service(self):
        """Create version control service for collaboration testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_collaboration.db"
        storage_path = Path(temp_dir) / "versions"
        service = VersionControlService(str(db_path), str(storage_path))
        yield service
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def realtime_service(self):
        """Create realtime service for collaboration testing"""
        return RealtimeService()
    
    @pytest.fixture
    def access_control_service(self):
        """Create access control service for collaboration testing"""
        return AccessControlService()
    
    def test_concurrent_editing_scenario(self, vc_service, realtime_service, access_control_service):
        """Test concurrent editing scenario with multiple users"""
        
        # Setup users
        users = ["architect", "engineer", "contractor", "inspector"]
        for user in users:
            access_control_service.create_user(user, "password", "editor")
        
        # Create initial floor
        initial_floor = {
            "floor_id": "collaboration-floor",
            "building_id": "collaboration-building",
            "objects": [
                {"id": "room-001", "type": "room", "x": 100, "y": 100, "width": 50, "height": 50},
                {"id": "device-001", "type": "device", "x": 150, "y": 150}
            ],
            "metadata": {"name": "Collaboration Floor"}
        }
        
        # Architect creates initial version
        initial_version = vc_service.create_version(
            initial_floor,
            "collaboration-floor",
            "collaboration-building",
            "main",
            "Initial floor design",
            "architect"
        )
        
        # Multiple users work on different branches simultaneously
        user_branches = {}
        user_changes = {}
        
        for user in users[1:]:  # Skip architect
            # Create branch for user
            branch_result = vc_service.create_branch(
                f"{user}-branch",
                "collaboration-floor",
                "collaboration-building",
                initial_version["version_id"],
                user,
                f"{user} working branch"
            )
            
            user_branches[user] = branch_result["branch_name"]
            
            # User makes changes
            user_floor = initial_floor.copy()
            user_floor["objects"].append({
                "id": f"{user}-device",
                "type": "device",
                "x": 200 + len(user) * 10,
                "y": 200 + len(user) * 10
            })
            
            change_result = vc_service.create_version(
                user_floor,
                "collaboration-floor",
                "collaboration-building",
                user_branches[user],
                f"{user} changes",
                user
            )
            
            user_changes[user] = change_result["version_id"]
        
        # Simulate real-time collaboration
        collaboration_events = []
        
        def user_activity(user, action):
            collaboration_events.append({
                "user": user,
                "action": action,
                "timestamp": datetime.utcnow()
            })
        
        # Simulate users working simultaneously
        user_activity("engineer", "editing_electrical")
        user_activity("contractor", "editing_structural")
        user_activity("inspector", "reviewing_changes")
        
        # Create merge requests for each user
        merge_requests = {}
        for user in users[1:]:
            merge_request = vc_service.create_merge_request(
                user_changes[user],
                initial_version["version_id"],
                user,
                f"Merge {user} changes"
            )
            merge_requests[user] = merge_request["merge_request_id"]
        
        # Simulate code review process
        for user in users[1:]:
            # Add review comments
            vc_service.add_comment(
                merge_requests[user],
                "architect",
                f"Reviewing {user} changes"
            )
            
            # Approve and merge
            vc_service.execute_merge(merge_requests[user], "architect")
        
        # Verify final collaborative result
        history = vc_service.get_version_history("collaboration-floor", "collaboration-building")
        latest_version = history["versions"][0]
        version_data = vc_service.get_version_data(latest_version["version_id"])
        
        # Check that all user changes are included
        objects = version_data["data"]["objects"]
        user_device_ids = [obj["id"] for obj in objects if obj["id"].endswith("-device")]
        
        for user in users[1:]:
            assert f"{user}-device" in user_device_ids
        
        # Verify collaboration events were tracked
        assert len(collaboration_events) == 3
    
    def test_conflict_resolution_collaboration(self, vc_service, realtime_service):
        """Test conflict resolution in collaborative environment"""
        
        # Create initial version
        initial_floor = {
            "floor_id": "conflict-floor",
            "building_id": "conflict-building",
            "objects": [
                {"id": "room-001", "type": "room", "x": 100, "y": 100, "width": 50, "height": 50}
            ],
            "metadata": {"name": "Conflict Floor"}
        }
        
        initial_version = vc_service.create_version(
            initial_floor,
            "conflict-floor",
            "conflict-building",
            "main",
            "Initial version",
            "architect"
        )
        
        # Two users modify the same object simultaneously
        user1_floor = initial_floor.copy()
        user1_floor["objects"][0]["width"] = 60  # User 1 changes width
        
        user2_floor = initial_floor.copy()
        user2_floor["objects"][0]["height"] = 60  # User 2 changes height
        
        # Create branches and versions
        vc_service.create_branch("user1-branch", "conflict-floor", "conflict-building", initial_version["version_id"], "user1")
        vc_service.create_branch("user2-branch", "conflict-floor", "conflict-building", initial_version["version_id"], "user2")
        
        user1_version = vc_service.create_version(
            user1_floor,
            "conflict-floor",
            "conflict-building",
            "user1-branch",
            "User 1 changes",
            "user1"
        )
        
        user2_version = vc_service.create_version(
            user2_floor,
            "conflict-floor",
            "conflict-building",
            "user2-branch",
            "User 2 changes",
            "user2"
        )
        
        # Detect conflicts
        conflicts = vc_service.detect_conflicts(user1_version["version_id"], user2_version["version_id"])
        assert len(conflicts) > 0
        
        # Simulate conflict resolution discussion
        discussion_events = []
        
        def add_discussion_event(user, message):
            discussion_events.append({
                "user": user,
                "message": message,
                "timestamp": datetime.utcnow()
            })
        
        add_discussion_event("user1", "I need the width to be 60 for equipment placement")
        add_discussion_event("user2", "I need the height to be 60 for ceiling clearance")
        add_discussion_event("architect", "Let's combine both changes")
        
        # Create resolved version
        resolved_floor = initial_floor.copy()
        resolved_floor["objects"][0]["width"] = 60
        resolved_floor["objects"][0]["height"] = 60
        
        resolved_version = vc_service.create_version(
            resolved_floor,
            "conflict-floor",
            "conflict-building",
            "user1-branch",
            "Resolved conflicts - combined both changes",
            "architect"
        )
        
        # Merge resolved version
        merge_request = vc_service.create_merge_request(
            resolved_version["version_id"],
            initial_version["version_id"],
            "architect",
            "Merge resolved conflicts"
        )
        
        vc_service.execute_merge(merge_request["merge_request_id"], "architect")
        
        # Verify resolution
        history = vc_service.get_version_history("conflict-floor", "conflict-building")
        latest_version = history["versions"][0]
        version_data = vc_service.get_version_data(latest_version["version_id"])
        
        final_room = version_data["data"]["objects"][0]
        assert final_room["width"] == 60
        assert final_room["height"] == 60
        
        # Verify discussion was tracked
        assert len(discussion_events) == 3
    
    def test_permission_based_collaboration(self, vc_service, access_control_service):
        """Test collaboration with different permission levels"""
        
        # Setup users with different roles
        access_control_service.create_user("admin", "password", "admin")
        access_control_service.create_user("architect", "password", "editor")
        access_control_service.create_user("viewer", "password", "viewer")
        
        # Create initial version
        initial_floor = {
            "floor_id": "permission-floor",
            "building_id": "permission-building",
            "objects": [
                {"id": "room-001", "type": "room", "x": 100, "y": 100, "width": 50, "height": 50}
            ],
            "metadata": {"name": "Permission Floor"}
        }
        
        initial_version = vc_service.create_version(
            initial_floor,
            "permission-floor",
            "permission-building",
            "main",
            "Initial version",
            "admin"
        )
        
        # Test different permission levels
        permission_tests = [
            ("admin", "create_branch", True),
            ("architect", "create_branch", True),
            ("viewer", "create_branch", False),
            ("admin", "create_version", True),
            ("architect", "create_version", True),
            ("viewer", "create_version", False),
            ("admin", "merge_request", True),
            ("architect", "merge_request", True),
            ("viewer", "merge_request", False)
        ]
        
        for user, action, should_succeed in permission_tests:
            if action == "create_branch":
                result = vc_service.create_branch(
                    f"{user}-branch",
                    "permission-floor",
                    "permission-building",
                    initial_version["version_id"],
                    user,
                    f"{user} branch"
                )
            elif action == "create_version":
                result = vc_service.create_version(
                    initial_floor,
                    "permission-floor",
                    "permission-building",
                    "main",
                    f"{user} version",
                    user
                )
            elif action == "merge_request":
                result = vc_service.create_merge_request(
                    initial_version["version_id"],
                    initial_version["version_id"],
                    user,
                    f"{user} merge request"
                )
            
            if should_succeed:
                assert result["success"] is True
            else:
                assert result["success"] is False or "permission" in result["message"].lower()


if __name__ == "__main__":
    pytest.main([__file__]) 