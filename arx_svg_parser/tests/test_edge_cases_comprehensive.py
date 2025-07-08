"""
Comprehensive Edge Case Tests for Arxos Platform

Tests cover:
- Empty floors and large datasets
- Concurrent edit scenarios
- Failed restore operations
- Stress testing for performance
- Boundary conditions
- Error recovery scenarios
"""

import pytest
import json
import tempfile
import shutil
import asyncio
import concurrent.futures
import threading
import time
import random
import string
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, List, Any

# Import all services
from services.version_control import VersionControlService
from services.route_manager import RouteManager
from services.floor_manager import FloorManager
from services.auto_snapshot import AutoSnapshotService
from services.realtime_service import RealTimeService as RealtimeService
from services.cache_service import CacheService
from services.data_partitioning import DataPartitioningService
from services.access_control import AccessControlService


class TestEmptyFloorsAndLargeDatasets:
    """Tests for handling empty floors and large datasets"""
    
    @pytest.fixture
    def vc_service(self):
        """Create version control service for edge case testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_edge_cases.db"
        storage_path = Path(temp_dir) / "versions"
        service = VersionControlService(str(db_path), str(storage_path))
        yield service
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def floor_manager(self):
        """Create floor manager for edge case testing"""
        return FloorManager()
    
    def test_empty_floor_creation(self, vc_service, floor_manager):
        """Test creation and handling of completely empty floors"""
        
        # Create empty floor
        empty_floor = {
            "floor_id": "empty-floor",
            "building_id": "empty-building",
            "objects": [],
            "metadata": {}
        }
        
        # Create version with empty floor
        result = vc_service.create_version(
            empty_floor,
            "empty-floor",
            "empty-building",
            "main",
            "Empty floor",
            "architect"
        )
        
        assert result["success"] is True
        assert result["version"]["object_count"] == 0
        
        # Verify empty floor can be retrieved
        version_data = vc_service.get_version_data(result["version_id"])
        assert version_data["success"] is True
        assert len(version_data["data"]["objects"]) == 0
        
        # Test floor manager with empty floor
        floor_result = floor_manager.create_floor(
            "empty-building",
            "Empty Floor",
            1,
            0.0,  # Zero area
            {},
            "architect"
        )
        
        assert floor_result["success"] is True
        assert floor_result["floor"]["area"] == 0.0
    
    def test_very_large_dataset(self, vc_service):
        """Test handling of very large datasets"""
        
        # Create large dataset with 100,000 objects
        large_objects = []
        for i in range(100000):
            large_objects.append({
                "id": f"obj-{i:06d}",
                "type": "device",
                "x": i % 1000,
                "y": i // 1000,
                "properties": {
                    "name": f"Device {i}",
                    "category": f"category-{i % 10}",
                    "status": "active" if i % 2 == 0 else "inactive",
                    "metadata": {
                        "created": datetime.utcnow().isoformat(),
                        "modified": datetime.utcnow().isoformat(),
                        "tags": [f"tag-{j}" for j in range(i % 5)]
                    }
                }
            })
        
        large_floor = {
            "floor_id": "large-floor",
            "building_id": "large-building",
            "objects": large_objects,
            "metadata": {
                "name": "Large Floor",
                "object_count": len(large_objects),
                "total_area": 1000000.0
            }
        }
        
        # Measure creation time
        start_time = time.time()
        
        result = vc_service.create_version(
            large_floor,
            "large-floor",
            "large-building",
            "main",
            "Large dataset version",
            "architect"
        )
        
        creation_time = time.time() - start_time
        
        assert result["success"] is True
        assert result["version"]["object_count"] == 100000
        assert creation_time < 30.0  # Should complete within 30 seconds
        
        # Test retrieval performance
        start_time = time.time()
        version_data = vc_service.get_version_data(result["version_id"])
        retrieval_time = time.time() - start_time
        
        assert version_data["success"] is True
        assert len(version_data["data"]["objects"]) == 100000
        assert retrieval_time < 10.0  # Should retrieve within 10 seconds
    
    def test_extremely_large_metadata(self, vc_service):
        """Test handling of extremely large metadata"""
        
        # Create large metadata
        large_metadata = {
            "name": "Large Metadata Floor",
            "description": "A" * 1000000,  # 1MB description
            "properties": {
                "detailed_info": "B" * 500000,  # 500KB detailed info
                "specifications": {
                    "technical_details": "C" * 250000,  # 250KB technical details
                    "requirements": "D" * 250000  # 250KB requirements
                }
            },
            "history": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "created",
                    "details": "E" * 100000  # 100KB per history entry
                }
                for _ in range(10)
            ]
        }
        
        floor_with_large_metadata = {
            "floor_id": "large-metadata-floor",
            "building_id": "large-metadata-building",
            "objects": [{"id": "test-obj", "type": "device", "x": 100, "y": 100}],
            "metadata": large_metadata
        }
        
        # Test creation
        result = vc_service.create_version(
            floor_with_large_metadata,
            "large-metadata-floor",
            "large-metadata-building",
            "main",
            "Large metadata version",
            "architect"
        )
        
        assert result["success"] is True
        
        # Test retrieval
        version_data = vc_service.get_version_data(result["version_id"])
        assert version_data["success"] is True
        assert len(version_data["data"]["metadata"]["description"]) == 1000000
    
    def test_mixed_empty_and_large_floors(self, vc_service):
        """Test handling of mixed empty and large floors in same building"""
        
        building_id = "mixed-building"
        floors = []
        
        # Create mix of empty and large floors
        for i in range(10):
            if i % 2 == 0:  # Empty floors
                floor_data = {
                    "floor_id": f"floor-{i}",
                    "building_id": building_id,
                    "objects": [],
                    "metadata": {"name": f"Empty Floor {i}"}
                }
            else:  # Large floors
                large_objects = [
                    {"id": f"obj-{i}-{j}", "type": "device", "x": j, "y": j}
                    for j in range(10000)
                ]
                floor_data = {
                    "floor_id": f"floor-{i}",
                    "building_id": building_id,
                    "objects": large_objects,
                    "metadata": {"name": f"Large Floor {i}"}
                }
            
            result = vc_service.create_version(
                floor_data,
                f"floor-{i}",
                building_id,
                "main",
                f"Floor {i} version",
                "architect"
            )
            
            assert result["success"] is True
            floors.append(result["version_id"])
        
        # Test retrieving all floors
        for version_id in floors:
            version_data = vc_service.get_version_data(version_id)
            assert version_data["success"] is True


class TestConcurrentEditScenarios:
    """Tests for concurrent edit scenarios"""
    
    @pytest.fixture
    def vc_service(self):
        """Create version control service for concurrent testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_concurrent.db"
        storage_path = Path(temp_dir) / "versions"
        service = VersionControlService(str(db_path), str(storage_path))
        yield service
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def realtime_service(self):
        """Create realtime service for concurrent testing"""
        return RealtimeService()
    
    def test_multiple_users_editing_same_floor(self, vc_service, realtime_service):
        """Test multiple users editing the same floor simultaneously"""
        
        # Create initial floor
        initial_floor = {
            "floor_id": "concurrent-floor",
            "building_id": "concurrent-building",
            "objects": [
                {"id": "room-001", "type": "room", "x": 100, "y": 100, "width": 50, "height": 50}
            ],
            "metadata": {"name": "Concurrent Floor"}
        }
        
        initial_version = vc_service.create_version(
            initial_floor,
            "concurrent-floor",
            "concurrent-building",
            "main",
            "Initial version",
            "architect"
        )
        
        # Simulate multiple users editing simultaneously
        users = ["user1", "user2", "user3", "user4", "user5"]
        user_changes = {}
        user_branches = {}
        
        def user_edit_workflow(user_id):
            """Simulate user editing workflow"""
            try:
                # Create branch
                branch_result = vc_service.create_branch(
                    f"{user_id}-branch",
                    "concurrent-floor",
                    "concurrent-building",
                    initial_version["version_id"],
                    user_id,
                    f"{user_id} working branch"
                )
                
                if not branch_result["success"]:
                    return {"user": user_id, "success": False, "error": "Branch creation failed"}
                
                user_branches[user_id] = branch_result["branch_name"]
                
                # Make changes
                user_floor = initial_floor.copy()
                user_floor["objects"].append({
                    "id": f"{user_id}-device",
                    "type": "device",
                    "x": 200 + hash(user_id) % 100,
                    "y": 200 + hash(user_id) % 100
                })
                
                # Simulate editing time
                time.sleep(random.uniform(0.1, 0.5))
                
                # Create version
                version_result = vc_service.create_version(
                    user_floor,
                    "concurrent-floor",
                    "concurrent-building",
                    branch_result["branch_name"],
                    f"{user_id} changes",
                    user_id
                )
                
                if version_result["success"]:
                    user_changes[user_id] = version_result["version_id"]
                    return {"user": user_id, "success": True, "version_id": version_result["version_id"]}
                else:
                    return {"user": user_id, "success": False, "error": "Version creation failed"}
                    
            except Exception as e:
                return {"user": user_id, "success": False, "error": str(e)}
        
        # Execute concurrent edits
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(users)) as executor:
            futures = [executor.submit(user_edit_workflow, user) for user in users]
            results = [future.result() for future in futures]
        
        # Verify results
        successful_edits = [r for r in results if r["success"]]
        assert len(successful_edits) >= len(users) * 0.8  # At least 80% should succeed
        
        # Verify all successful edits created different versions
        version_ids = [r["version_id"] for r in successful_edits]
        assert len(set(version_ids)) == len(version_ids)  # All unique
    
    def test_concurrent_branch_creation(self, vc_service):
        """Test concurrent branch creation scenarios"""
        
        # Create initial version
        initial_floor = {"floor_id": "branch-floor", "building_id": "branch-building", "objects": []}
        initial_version = vc_service.create_version(
            initial_floor,
            "branch-floor",
            "branch-building",
            "main",
            "Initial version",
            "architect"
        )
        
        # Try to create branches with same name concurrently
        branch_name = "concurrent-branch"
        
        def create_branch():
            return vc_service.create_branch(
                branch_name,
                "branch-floor",
                "branch-building",
                initial_version["version_id"],
                f"user-{threading.current_thread().ident}",
                "Concurrent branch"
            )
        
        # Create branches concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_branch) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # Only one should succeed, others should fail
        successful_branches = [r for r in results if r["success"]]
        failed_branches = [r for r in results if not r["success"]]
        
        assert len(successful_branches) == 1
        assert len(failed_branches) == 9
        
        # Verify error messages
        for failed_result in failed_branches:
            assert "already exists" in failed_result["message"].lower()
    
    def test_concurrent_merge_requests(self, vc_service):
        """Test concurrent merge request creation"""
        
        # Create initial version
        initial_floor = {"floor_id": "merge-floor", "building_id": "merge-building", "objects": []}
        initial_version = vc_service.create_version(
            initial_floor,
            "merge-floor",
            "merge-building",
            "main",
            "Initial version",
            "architect"
        )
        
        # Create multiple branches
        branches = []
        for i in range(5):
            branch_result = vc_service.create_branch(
                f"branch-{i}",
                "merge-floor",
                "merge-building",
                initial_version["version_id"],
                f"user-{i}",
                f"Branch {i}"
            )
            
            # Create version in branch
            version_result = vc_service.create_version(
                initial_floor,
                "merge-floor",
                "merge-building",
                branch_result["branch_name"],
                f"Version {i}",
                f"user-{i}"
            )
            
            branches.append({
                "branch_name": branch_result["branch_name"],
                "version_id": version_result["version_id"]
            })
        
        # Create merge requests concurrently
        def create_merge_request(branch_info):
            return vc_service.create_merge_request(
                branch_info["version_id"],
                initial_version["version_id"],
                f"user-{branch_info['branch_name']}",
                f"Merge {branch_info['branch_name']}"
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_merge_request, branch) for branch in branches]
            results = [future.result() for future in futures]
        
        # All merge requests should succeed
        for result in results:
            assert result["success"] is True
            assert "merge_request_id" in result
    
    def test_concurrent_version_creation_race_condition(self, vc_service):
        """Test race conditions in concurrent version creation"""
        
        # Create initial version
        initial_floor = {"floor_id": "race-floor", "building_id": "race-building", "objects": []}
        initial_version = vc_service.create_version(
            initial_floor,
            "race-floor",
            "race-building",
            "main",
            "Initial version",
            "architect"
        )
        
        # Try to create versions with same version number concurrently
        def create_version_with_delay():
            time.sleep(random.uniform(0.01, 0.1))  # Small random delay
            return vc_service.create_version(
                initial_floor,
                "race-floor",
                "race-building",
                "main",
                f"Version {threading.current_thread().ident}",
                f"user-{threading.current_thread().ident}"
            )
        
        # Create versions concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(create_version_with_delay) for _ in range(20)]
            results = [future.result() for future in futures]
        
        # All should succeed with unique version numbers
        successful_versions = [r for r in results if r["success"]]
        assert len(successful_versions) == 20
        
        # Check version numbers are unique and sequential
        version_numbers = [v["version"]["version_number"] for v in successful_versions]
        version_numbers.sort()
        
        # Should be sequential starting from 2 (after initial version)
        expected_numbers = list(range(2, 22))
        assert version_numbers == expected_numbers


class TestFailedRestoreOperations:
    """Tests for failed restore operations"""
    
    @pytest.fixture
    def vc_service(self):
        """Create version control service for restore testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_restore.db"
        storage_path = Path(temp_dir) / "versions"
        service = VersionControlService(str(db_path), str(storage_path))
        yield service
        shutil.rmtree(temp_dir)
    
    def test_restore_nonexistent_version(self, vc_service):
        """Test restore of nonexistent version"""
        
        result = vc_service.restore_version("nonexistent-version-id", "test-user")
        
        assert result["success"] is False
        assert "not found" in result["message"].lower()
    
    def test_restore_corrupted_version_file(self, vc_service):
        """Test restore of version with corrupted file"""
        
        # Create valid version
        initial_floor = {"floor_id": "corrupt-floor", "building_id": "corrupt-building", "objects": []}
        version_result = vc_service.create_version(
            initial_floor,
            "corrupt-floor",
            "corrupt-building",
            "main",
            "Valid version",
            "architect"
        )
        
        # Corrupt the version file
        version_file = Path(vc_service.storage_path) / f"{version_result['version_id']}.json"
        version_file.write_text("corrupted json data { invalid syntax")
        
        # Try to restore corrupted version
        result = vc_service.restore_version(version_result["version_id"], "test-user")
        
        assert result["success"] is False
        assert "corrupted" in result["message"].lower() or "invalid" in result["message"].lower()
    
    def test_restore_version_with_missing_objects(self, vc_service):
        """Test restore of version with missing referenced objects"""
        
        # Create version with object references
        floor_with_references = {
            "floor_id": "reference-floor",
            "building_id": "reference-building",
            "objects": [
                {"id": "obj-001", "type": "device", "x": 100, "y": 100},
                {"id": "obj-002", "type": "device", "x": 200, "y": 200, "parent_id": "obj-001"}
            ],
            "metadata": {"name": "Reference Floor"}
        }
        
        version_result = vc_service.create_version(
            floor_with_references,
            "reference-floor",
            "reference-building",
            "main",
            "Version with references",
            "architect"
        )
        
        # Corrupt file to remove referenced object
        corrupted_data = {
            "floor_id": "reference-floor",
            "building_id": "reference-building",
            "objects": [
                {"id": "obj-002", "type": "device", "x": 200, "y": 200, "parent_id": "obj-001"}
            ],
            "metadata": {"name": "Reference Floor"}
        }
        
        version_file = Path(vc_service.storage_path) / f"{version_result['version_id']}.json"
        version_file.write_text(json.dumps(corrupted_data))
        
        # Try to restore version with missing reference
        result = vc_service.restore_version(version_result["version_id"], "test-user")
        
        # Should either fail or handle gracefully
        if not result["success"]:
            assert "reference" in result["message"].lower() or "missing" in result["message"].lower()
    
    def test_restore_version_with_invalid_data_structure(self, vc_service):
        """Test restore of version with invalid data structure"""
        
        # Create valid version
        initial_floor = {"floor_id": "invalid-floor", "building_id": "invalid-building", "objects": []}
        version_result = vc_service.create_version(
            initial_floor,
            "invalid-floor",
            "invalid-building",
            "main",
            "Valid version",
            "architect"
        )
        
        # Create invalid data structure
        invalid_data = {
            "invalid_field": "invalid_value",
            "missing_required_fields": True
        }
        
        version_file = Path(vc_service.storage_path) / f"{version_result['version_id']}.json"
        version_file.write_text(json.dumps(invalid_data))
        
        # Try to restore invalid version
        result = vc_service.restore_version(version_result["version_id"], "test-user")
        
        assert result["success"] is False
        assert "invalid" in result["message"].lower() or "missing" in result["message"].lower()
    
    def test_restore_version_with_permission_denied(self, vc_service):
        """Test restore when file permissions are denied"""
        
        # Create valid version
        initial_floor = {"floor_id": "permission-floor", "building_id": "permission-building", "objects": []}
        version_result = vc_service.create_version(
            initial_floor,
            "permission-floor",
            "permission-building",
            "main",
            "Valid version",
            "architect"
        )
        
        # Simulate permission denied
        with patch('pathlib.Path.read_text', side_effect=PermissionError("Permission denied")):
            result = vc_service.restore_version(version_result["version_id"], "test-user")
            
            assert result["success"] is False
            assert "permission" in result["message"].lower()
    
    def test_restore_version_with_storage_full(self, vc_service):
        """Test restore when storage is full"""
        
        # Create valid version
        initial_floor = {"floor_id": "storage-floor", "building_id": "storage-building", "objects": []}
        version_result = vc_service.create_version(
            initial_floor,
            "storage-floor",
            "storage-building",
            "main",
            "Valid version",
            "architect"
        )
        
        # Simulate storage full error
        with patch('pathlib.Path.write_text', side_effect=OSError("No space left on device")):
            result = vc_service.restore_version(version_result["version_id"], "test-user")
            
            assert result["success"] is False
            assert "storage" in result["message"].lower() or "space" in result["message"].lower()


class TestStressTestingForPerformance:
    """Stress testing for performance"""
    
    @pytest.fixture
    def vc_service(self):
        """Create version control service for stress testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_stress.db"
        storage_path = Path(temp_dir) / "versions"
        service = VersionControlService(str(db_path), str(storage_path))
        yield service
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def floor_manager(self):
        """Create floor manager for stress testing"""
        return FloorManager()
    
    def test_rapid_version_creation(self, vc_service):
        """Test rapid creation of many versions"""
        
        initial_floor = {"floor_id": "stress-floor", "building_id": "stress-building", "objects": []}
        
        # Create initial version
        current_version = vc_service.create_version(
            initial_floor,
            "stress-floor",
            "stress-building",
            "main",
            "Initial version",
            "architect"
        )
        
        # Rapidly create 1000 versions
        start_time = time.time()
        
        for i in range(1000):
            # Add small change
            modified_floor = initial_floor.copy()
            modified_floor["objects"].append({
                "id": f"obj-{i}",
                "type": "device",
                "x": i,
                "y": i
            })
            
            current_version = vc_service.create_version(
                modified_floor,
                "stress-floor",
                "stress-building",
                "main",
                f"Version {i}",
                "architect"
            )
            
            if not current_version["success"]:
                break
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time
        assert total_time < 60.0  # 60 seconds for 1000 versions
        assert current_version["success"] is True
        
        # Verify version number
        assert current_version["version"]["version_number"] == 1001  # Initial + 1000
    
    def test_concurrent_branch_operations(self, vc_service):
        """Test concurrent operations on many branches"""
        
        # Create initial version
        initial_floor = {"floor_id": "branch-stress-floor", "building_id": "branch-stress-building", "objects": []}
        initial_version = vc_service.create_version(
            initial_floor,
            "branch-stress-floor",
            "branch-stress-building",
            "main",
            "Initial version",
            "architect"
        )
        
        # Create 100 branches concurrently
        def create_branch_and_version(branch_id):
            try:
                # Create branch
                branch_result = vc_service.create_branch(
                    f"stress-branch-{branch_id}",
                    "branch-stress-floor",
                    "branch-stress-building",
                    initial_version["version_id"],
                    f"user-{branch_id}",
                    f"Stress branch {branch_id}"
                )
                
                if not branch_result["success"]:
                    return {"branch_id": branch_id, "success": False}
                
                # Create version in branch
                version_result = vc_service.create_version(
                    initial_floor,
                    "branch-stress-floor",
                    "branch-stress-building",
                    branch_result["branch_name"],
                    f"Version in branch {branch_id}",
                    f"user-{branch_id}"
                )
                
                return {
                    "branch_id": branch_id,
                    "success": version_result["success"],
                    "version_id": version_result.get("version_id")
                }
                
            except Exception as e:
                return {"branch_id": branch_id, "success": False, "error": str(e)}
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(create_branch_and_version, i) for i in range(100)]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time
        assert total_time < 30.0  # 30 seconds for 100 branches
        
        # Most operations should succeed
        successful_operations = [r for r in results if r["success"]]
        assert len(successful_operations) >= 90  # At least 90% success rate
    
    def test_large_history_retrieval(self, vc_service):
        """Test retrieval of large version history"""
        
        # Create many versions
        initial_floor = {"floor_id": "history-floor", "building_id": "history-building", "objects": []}
        
        for i in range(1000):
            modified_floor = initial_floor.copy()
            modified_floor["objects"].append({
                "id": f"obj-{i}",
                "type": "device",
                "x": i,
                "y": i
            })
            
            vc_service.create_version(
                modified_floor,
                "history-floor",
                "history-building",
                "main",
                f"Version {i}",
                "architect"
            )
        
        # Test retrieving full history
        start_time = time.time()
        history = vc_service.get_version_history("history-floor", "history-building")
        end_time = time.time()
        
        retrieval_time = end_time - start_time
        
        assert history["success"] is True
        assert len(history["versions"]) == 1000
        assert retrieval_time < 10.0  # Should retrieve within 10 seconds
    
    def test_memory_usage_with_large_objects(self, vc_service):
        """Test memory usage with very large objects"""
        
        # Create floor with very large objects
        large_objects = []
        for i in range(100):
            # Each object has large properties
            large_object = {
                "id": f"large-obj-{i}",
                "type": "device",
                "x": i,
                "y": i,
                "properties": {
                    "name": f"Large Device {i}",
                    "description": "A" * 10000,  # 10KB description
                    "specifications": {
                        "technical_details": "B" * 5000,  # 5KB technical details
                        "requirements": "C" * 5000  # 5KB requirements
                    },
                    "metadata": {
                        "tags": [f"tag-{j}" for j in range(100)],
                        "history": [
                            {
                                "timestamp": datetime.utcnow().isoformat(),
                                "action": "created",
                                "details": "D" * 1000
                            }
                            for _ in range(10)
                        ]
                    }
                }
            }
            large_objects.append(large_object)
        
        large_floor = {
            "floor_id": "memory-floor",
            "building_id": "memory-building",
            "objects": large_objects,
            "metadata": {"name": "Memory Test Floor"}
        }
        
        # Create version with large objects
        start_time = time.time()
        result = vc_service.create_version(
            large_floor,
            "memory-floor",
            "memory-building",
            "main",
            "Large objects version",
            "architect"
        )
        creation_time = time.time() - start_time
        
        assert result["success"] is True
        assert creation_time < 30.0  # Should complete within 30 seconds
        
        # Test retrieval
        start_time = time.time()
        version_data = vc_service.get_version_data(result["version_id"])
        retrieval_time = time.time() - start_time
        
        assert version_data["success"] is True
        assert len(version_data["data"]["objects"]) == 100
        assert retrieval_time < 15.0  # Should retrieve within 15 seconds
    
    def test_database_connection_stress(self, vc_service):
        """Test stress on database connections"""
        
        # Simulate many concurrent database operations
        def database_operation(operation_id):
            try:
                # Create version
                floor_data = {
                    "floor_id": f"db-stress-floor-{operation_id}",
                    "building_id": "db-stress-building",
                    "objects": [{"id": f"obj-{operation_id}", "type": "device", "x": operation_id, "y": operation_id}],
                    "metadata": {"name": f"DB Stress Floor {operation_id}"}
                }
                
                result = vc_service.create_version(
                    floor_data,
                    f"db-stress-floor-{operation_id}",
                    "db-stress-building",
                    "main",
                    f"DB stress version {operation_id}",
                    f"user-{operation_id}"
                )
                
                if result["success"]:
                    # Retrieve version
                    version_data = vc_service.get_version_data(result["version_id"])
                    return {"operation_id": operation_id, "success": version_data["success"]}
                else:
                    return {"operation_id": operation_id, "success": False}
                    
            except Exception as e:
                return {"operation_id": operation_id, "success": False, "error": str(e)}
        
        # Run 500 concurrent database operations
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(database_operation, i) for i in range(500)]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time
        assert total_time < 60.0  # 60 seconds for 500 operations
        
        # Most operations should succeed
        successful_operations = [r for r in results if r["success"]]
        assert len(successful_operations) >= 450  # At least 90% success rate


class TestBoundaryConditions:
    """Tests for boundary conditions"""
    
    @pytest.fixture
    def vc_service(self):
        """Create version control service for boundary testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_boundary.db"
        storage_path = Path(temp_dir) / "versions"
        service = VersionControlService(str(db_path), str(storage_path))
        yield service
        shutil.rmtree(temp_dir)
    
    def test_maximum_string_lengths(self, vc_service):
        """Test handling of maximum string lengths"""
        
        # Test with very long strings
        long_string = "A" * 1000000  # 1MB string
        
        floor_with_long_strings = {
            "floor_id": "long-string-floor",
            "building_id": "long-string-building",
            "objects": [
                {
                    "id": "long-obj",
                    "type": "device",
                    "x": 100,
                    "y": 100,
                    "name": long_string,
                    "description": long_string
                }
            ],
            "metadata": {"name": long_string}
        }
        
        result = vc_service.create_version(
            floor_with_long_strings,
            "long-string-floor",
            "long-string-building",
            "main",
            "Long strings version",
            "architect"
        )
        
        assert result["success"] is True
        
        # Test retrieval
        version_data = vc_service.get_version_data(result["version_id"])
        assert version_data["success"] is True
        assert len(version_data["data"]["objects"][0]["name"]) == 1000000
    
    def test_extreme_coordinate_values(self, vc_service):
        """Test handling of extreme coordinate values"""
        
        # Test with extreme coordinates
        extreme_floor = {
            "floor_id": "extreme-floor",
            "building_id": "extreme-building",
            "objects": [
                {"id": "obj-1", "type": "device", "x": float('inf'), "y": float('inf')},
                {"id": "obj-2", "type": "device", "x": float('-inf'), "y": float('-inf')},
                {"id": "obj-3", "type": "device", "x": float('nan'), "y": float('nan')},
                {"id": "obj-4", "type": "device", "x": 1e308, "y": 1e308},  # Very large number
                {"id": "obj-5", "type": "device", "x": -1e308, "y": -1e308}  # Very small number
            ],
            "metadata": {"name": "Extreme Coordinates Floor"}
        }
        
        result = vc_service.create_version(
            extreme_floor,
            "extreme-floor",
            "extreme-building",
            "main",
            "Extreme coordinates version",
            "architect"
        )
        
        # Should handle extreme values gracefully
        if result["success"]:
            version_data = vc_service.get_version_data(result["version_id"])
            assert version_data["success"] is True
        else:
            # If it fails, should provide meaningful error
            assert "coordinate" in result["message"].lower() or "invalid" in result["message"].lower()
    
    def test_special_characters_in_ids(self, vc_service):
        """Test handling of special characters in IDs"""
        
        # Test with various special characters
        special_chars = [
            "obj-!@#$%^&*()",
            "obj-+={}[]|\\:;\"'<>?,./",
            "obj-émojis🚀",
            "obj-unicode-测试",
            "obj-with spaces",
            "obj-with\ttabs",
            "obj-with\nnewlines",
            "obj-with\rreturns"
        ]
        
        floor_with_special_ids = {
            "floor_id": "special-ids-floor",
            "building_id": "special-ids-building",
            "objects": [
                {"id": obj_id, "type": "device", "x": i * 100, "y": i * 100}
                for i, obj_id in enumerate(special_chars)
            ],
            "metadata": {"name": "Special IDs Floor"}
        }
        
        result = vc_service.create_version(
            floor_with_special_ids,
            "special-ids-floor",
            "special-ids-building",
            "main",
            "Special IDs version",
            "architect"
        )
        
        assert result["success"] is True
        
        # Test retrieval
        version_data = vc_service.get_version_data(result["version_id"])
        assert version_data["success"] is True
        assert len(version_data["data"]["objects"]) == len(special_chars)


if __name__ == "__main__":
    pytest.main([__file__]) 